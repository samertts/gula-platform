"""Synthetic durable-core contracts for the national clinical workflow.

This module is an additive, route-free service-layer boundary over the existing
Leap 02 ``NationalCoreWorkflow``. It adds recovery, bounded delivery, disclosure
and lineage *contracts* for synthetic evidence. It is deliberately not a new
database, audit authority, MPI, LIMS, EHR writer, FHIR conformance engine,
broker, or production persistence layer:

* no HTTP route, national-router mount, migration, DDL, trigger, or schema change;
* no database connection, broker, government connector, credential, or real data;
* no change to release gates, activation state, or medical-access authority;
* no exactly-once or full-FHIR-conformance claim.

The recovery journal protects a synthetic snapshot from accidental mutation and
truncation, but it is not a security-grade audit chain. Canonical audit remains
``CanonicalAuditService`` and is still verified by the wrapped workflow.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any

from app.clinical.observability import clinical_safety_metrics
from app.integration.fhir_r4_exchange import (
    SYNTHETIC_TAG_CODE,
    SYNTHETIC_TAG_SYSTEM,
    validate_synthetic_bundle,
)
from app.lab_slice.models import RELEASE_RELEASED, SyntheticLabCase
from app.lab_slice.terminology_bindings import (
    BINDING_UNMAPPED,
    LOCAL_TEST_SYSTEM,
    LOINC_SYSTEM,
    bind_test,
)
from app.national.fhir.validation import FHIRValidationEngine
from app.national.services.national_core_workflow import (
    WORKFLOW_LAYERS,
    NationalCoreWorkflow,
    NationalCoreWorkflowCommand,
    NationalCoreWorkflowResult,
)
from app.services.reference.national_lab_catalog import NationalLaboratoryCatalog

DURABLE_CORE_SCHEMA = "durable_national_clinical_core.v1.synthetic"
DURABLE_CORE_SOURCE = "durable_national_clinical_core_synthetic"
DURABLE_CORE_LAYERS: tuple[str, ...] = WORKFLOW_LAYERS
_METRIC_OPERATION = "durable_national_core"
_METRIC_RESOURCE = "durable_core_receipt"
_UCUM_SYSTEM = "http://unitsofmeasure.org"
_RAW_NID_RUN = re.compile(r"(?<!\d)\d{9,18}(?!\d)")
_OPAQUE = re.compile(r"^[A-Za-z0-9._:\-/]{1,200}$")
_GENESIS_DIGEST = "0" * 64

RECEIPT_PENDING = "pending_recovery"
RECEIPT_COMMITTED = "committed"
RECEIPT_FAILED = "failed"

JOURNAL_INTENT = "intent"
JOURNAL_COMMIT = "commit"
JOURNAL_FAIL = "fail"
JOURNAL_REPLAY = "replay"
JOURNAL_RECOVERY = "recovery"

_SENSITIVE_KEYS = frozenset(
    {
        "identifier",
        "telecom",
        "address",
        "birthdate",
        "birth_date",
        "contact",
        "national_id",
        "nationalid",
        "raw_nid",
        "credential",
        "password",
        "secret",
    }
)
_ALLOWED_CODING_SYSTEMS = frozenset({LOINC_SYSTEM, LOCAL_TEST_SYSTEM, _UCUM_SYSTEM})
_JOURNAL_KINDS = frozenset(
    {
        JOURNAL_INTENT,
        JOURNAL_COMMIT,
        JOURNAL_FAIL,
        JOURNAL_REPLAY,
        JOURNAL_RECOVERY,
    }
)
_JOURNAL_PAYLOAD_KEYS = frozenset(
    {"reason", "status", "attempts", "outcome", "schema", "recovered"}
)


class DurableCoreError(RuntimeError):
    """Base bounded failure for synthetic durable-core contracts."""


class DurableCoreIntegrityError(DurableCoreError):
    """A recovery snapshot failed hash-chain or bound validation."""


class DurableCoreReplayError(DurableCoreError):
    """An existing key was reused with different command inputs."""


class DurableCoreRecoveryRequired(DurableCoreError):
    """An interrupted command must be recovered before another execution."""


class DurableCoreInterruptionError(DurableCoreError):
    """A synthetic outbox/transaction interruption was injected."""


class DurableCoreConflict(DurableCoreError):
    """A duplicate clinical or outbox identity carries a different payload."""


class DurableCoreAuthorizationError(DurableCoreError):
    """A preflight authorization or unresolved identity gate failed closed."""


class FHIRDisclosureDenied(DurableCoreError):
    """A synthetic FHIR bundle failed the strict disclosure pre-check."""


class DurableCoreProjectionError(DurableCoreError):
    """A longitudinal projection attempt failed and was recorded for replay."""


# -- Bounded contracts -------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DurableCorePolicy:
    """Process-local limits; all values are synthetic and owner-reversible."""

    max_receipts: int = 256
    max_outbox_entries: int = 256
    max_journal_entries: int = 4096
    max_command_attempts: int = 5
    max_offline_attempts: int = 5
    max_offline_entries: int = 256
    backoff_base_seconds: float = 1.0
    backoff_cap_seconds: float = 60.0
    fail_before_workflow: bool = False
    fail_after_workflow: bool = False
    hard_interrupt_before_workflow: bool = False

    def __post_init__(self) -> None:
        for label, value in (
            ("max_receipts", self.max_receipts),
            ("max_outbox_entries", self.max_outbox_entries),
            ("max_journal_entries", self.max_journal_entries),
            ("max_command_attempts", self.max_command_attempts),
            ("max_offline_attempts", self.max_offline_attempts),
            ("max_offline_entries", self.max_offline_entries),
        ):
            if value < 1 or value > 10000:
                raise DurableCoreError(f"{label} is outside the bounded synthetic range")
        if not 0.0 < self.backoff_base_seconds <= 60.0:
            raise DurableCoreError("backoff_base_seconds is outside the bounded synthetic range")
        if not self.backoff_base_seconds <= self.backoff_cap_seconds <= 3600.0:
            raise DurableCoreError("backoff_cap_seconds is outside the bounded synthetic range")


@dataclass(frozen=True, slots=True)
class DurableCoreReceipt:
    """Non-sensitive recovery receipt; never an audit row or database record."""

    workflow_key: str
    correlation_id: str
    fingerprint: str
    status: str
    attempts: int
    result_digest: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_key": self.workflow_key,
            "correlation_id": self.correlation_id,
            "fingerprint": self.fingerprint,
            "status": self.status,
            "attempts": self.attempts,
            "result_digest": self.result_digest,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> DurableCoreReceipt:
        return cls(
            workflow_key=str(value["workflow_key"]),
            correlation_id=str(value["correlation_id"]),
            fingerprint=str(value["fingerprint"]),
            status=str(value["status"]),
            attempts=int(value["attempts"]),
            result_digest=str(value["result_digest"]),
            created_at=str(value["created_at"]),
            updated_at=str(value["updated_at"]),
        )


@dataclass(frozen=True, slots=True)
class JournalEntry:
    sequence: int
    kind: str
    workflow_key: str
    fingerprint: str
    payload: dict[str, Any]
    previous_digest: str
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "kind": self.kind,
            "workflow_key": self.workflow_key,
            "fingerprint": self.fingerprint,
            "payload": dict(self.payload),
            "previous_digest": self.previous_digest,
            "digest": self.digest,
        }


@dataclass(frozen=True, slots=True)
class OutboxEnvelope:
    """Synthetic envelope shaped after the canonical outbox contract."""

    fingerprint: str
    workflow_key: str
    correlation_id: str
    entity_type: str
    entity_id: str
    payload_digest: str
    status: str = "pending"
    attempts: int = 0
    synthetic: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "fingerprint": self.fingerprint,
            "workflow_key": self.workflow_key,
            "correlation_id": self.correlation_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "payload_digest": self.payload_digest,
            "status": self.status,
            "attempts": self.attempts,
            "synthetic": self.synthetic,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> OutboxEnvelope:
        return cls(
            fingerprint=str(value["fingerprint"]),
            workflow_key=str(value["workflow_key"]),
            correlation_id=str(value["correlation_id"]),
            entity_type=str(value["entity_type"]),
            entity_id=str(value["entity_id"]),
            payload_digest=str(value["payload_digest"]),
            status=str(value.get("status", "pending")),
            attempts=int(value.get("attempts", 0)),
            synthetic=bool(value.get("synthetic", True)),
        )


@dataclass(frozen=True, slots=True)
class FHIRGuardResult:
    valid: bool
    errors: tuple[str, ...]
    resource_types: tuple[str, ...]
    reference_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "resource_types": list(self.resource_types),
            "reference_count": self.reference_count,
        }


@dataclass(frozen=True, slots=True)
class LongitudinalEvent:
    """Bounded projection envelope; it is not an EHR write or durable row."""

    event_id: str
    patient_reference: str
    result_reference: str
    decision_reference: str
    revision: int
    status: str
    replayed: bool
    synthetic: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "patient_reference": self.patient_reference,
            "result_reference": self.result_reference,
            "decision_reference": self.decision_reference,
            "revision": self.revision,
            "status": self.status,
            "replayed": self.replayed,
            "synthetic": self.synthetic,
        }


@dataclass(frozen=True, slots=True)
class DurableCoreExecutionResult:
    schema_version: str
    workflow_key: str
    correlation_id: str
    fingerprint: str
    replayed: bool
    receipt: DurableCoreReceipt
    workflow_result: NationalCoreWorkflowResult | None
    outbox_summary: dict[str, Any]
    offline_summary: dict[str, Any]
    integrity: dict[str, Any]

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "workflow_key": self.workflow_key,
            "correlation_id": self.correlation_id,
            "fingerprint": self.fingerprint,
            "replayed": self.replayed,
            "receipt": self.receipt.to_dict(),
            "workflow": self.workflow_result.to_public_dict() if self.workflow_result else None,
            "outbox_summary": dict(self.outbox_summary),
            "offline_summary": dict(self.offline_summary),
            "integrity": dict(self.integrity),
        }


@dataclass(frozen=True, slots=True)
class DurableCoreRecoveryResult:
    schema_version: str
    pending_found: int
    recovered: int
    receipts: int
    outbox_entries: int
    integrity: dict[str, Any]

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "pending_found": self.pending_found,
            "recovered": self.recovered,
            "receipts": self.receipts,
            "outbox_entries": self.outbox_entries,
            "integrity": dict(self.integrity),
        }


@dataclass(frozen=True, slots=True)
class ResultRegistration:
    result_id: str
    fingerprint: str
    revision: int
    supersedes: str | None
    status: str
    released: bool
    replayed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "fingerprint": self.fingerprint,
            "revision": self.revision,
            "supersedes": self.supersedes,
            "status": self.status,
            "released": self.released,
            "replayed": self.replayed,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> ResultRegistration:
        return cls(
            result_id=str(value["result_id"]),
            fingerprint=str(value["fingerprint"]),
            revision=int(value["revision"]),
            supersedes=(str(value["supersedes"]) if value.get("supersedes") is not None else None),
            status=str(value["status"]),
            released=bool(value.get("released", False)),
            replayed=bool(value.get("replayed", False)),
        )


@dataclass(frozen=True, slots=True)
class ResultCorrection:
    case: SyntheticLabCase
    registration: ResultRegistration

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "case_reference": self.case.result.result_id,
            "registration": self.registration.to_dict(),
        }


# -- Helpers -----------------------------------------------------------------


def _stable_digest(value: Any) -> str:
    encoded = json.dumps(
        NationalCoreWorkflow._jsonable(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _journal_digest(
    *,
    sequence: int,
    kind: str,
    workflow_key: str,
    fingerprint: str,
    payload: Mapping[str, Any],
    previous_digest: str,
) -> str:
    encoded = json.dumps(
        {
            "schema": DURABLE_CORE_SCHEMA,
            "sequence": sequence,
            "kind": kind,
            "workflow_key": workflow_key,
            "fingerprint": fingerprint,
            "payload": NationalCoreWorkflow._jsonable(payload),
            "previous_digest": previous_digest,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _reason(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return "unknown"
    return value.strip().lower().replace(" ", "_")[:96]


def _safe_reason(value: str) -> str:
    from app.clinical.observability import reason_code

    return reason_code(value)


def _metric(*, outcome: str, reason: str | None = None) -> None:
    clinical_safety_metrics.record_command(
        operation=_METRIC_OPERATION,
        resource_type=_METRIC_RESOURCE,
        outcome=outcome,
        reason=reason,
    )


def _walk_sensitive(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            text_key = str(key).lower()
            child_path = f"{path}.{key}"
            if text_key in _SENSITIVE_KEYS:
                findings.append(child_path)
            findings.extend(_walk_sensitive(item, child_path))
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            findings.extend(_walk_sensitive(item, f"{path}[{index}]"))
    return findings


def _bounded_reviewer(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        raise DurableCoreError(f"{label} must be a bounded non-empty string")
    if _OPAQUE.fullmatch(value) is None:
        raise DurableCoreError(f"{label} must be an opaque synthetic reference")
    return value


# -- Recovery journal --------------------------------------------------------


class DurableCoreJournal:
    """Append-only synthetic recovery journal with local integrity checks."""

    def __init__(self, policy: DurableCorePolicy | None = None) -> None:
        self.policy = policy or DurableCorePolicy()
        self._entries: list[JournalEntry] = []
        self._declared_count = 0
        self._tail_digest = _GENESIS_DIGEST

    def append(
        self,
        *,
        kind: str,
        workflow_key: str,
        fingerprint: str,
        payload: Mapping[str, Any] | None = None,
    ) -> JournalEntry:
        if kind not in _JOURNAL_KINDS:
            raise DurableCoreIntegrityError("unsupported journal entry kind")
        if len(self._entries) >= self.policy.max_journal_entries:
            raise DurableCoreIntegrityError("journal depth cap reached")
        safe_payload = {
            key: value
            for key, value in (payload or {}).items()
            if key in _JOURNAL_PAYLOAD_KEYS
        }
        entry = JournalEntry(
            sequence=len(self._entries) + 1,
            kind=kind,
            workflow_key=workflow_key,
            fingerprint=fingerprint,
            payload=dict(safe_payload),
            previous_digest=self._tail_digest,
            digest="",
        )
        digest = _journal_digest(
            sequence=entry.sequence,
            kind=entry.kind,
            workflow_key=entry.workflow_key,
            fingerprint=entry.fingerprint,
            payload=entry.payload,
            previous_digest=entry.previous_digest,
        )
        entry = replace(entry, digest=digest)
        self._entries.append(entry)
        self._declared_count = len(self._entries)
        self._tail_digest = digest
        return entry

    def entries(self) -> tuple[JournalEntry, ...]:
        return tuple(self._entries)

    def verify(self) -> dict[str, Any]:
        previous = _GENESIS_DIGEST
        for index, entry in enumerate(self._entries, start=1):
            if entry.sequence != index or entry.previous_digest != previous:
                return {"status": "INVALID", "violation": "sequence_or_link", "sequence": index}
            expected = _journal_digest(
                sequence=entry.sequence,
                kind=entry.kind,
                workflow_key=entry.workflow_key,
                fingerprint=entry.fingerprint,
                payload=entry.payload,
                previous_digest=entry.previous_digest,
            )
            if expected != entry.digest:
                return {"status": "INVALID", "violation": "digest", "sequence": index}
            previous = entry.digest
        if self._declared_count != len(self._entries) or self._tail_digest != previous:
            return {"status": "INVALID", "violation": "truncation", "sequence": len(self._entries)}
        return {"status": "VALID", "entries": len(self._entries), "tail_digest": previous}

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": DURABLE_CORE_SCHEMA,
            "declared_count": self._declared_count,
            "tail_digest": self._tail_digest,
            "entries": [entry.to_dict() for entry in self._entries],
        }

    def restore(self, snapshot: Mapping[str, Any]) -> None:
        """Validate a snapshot into locals before mutating the live journal."""

        if snapshot.get("schema") != DURABLE_CORE_SCHEMA:
            raise DurableCoreIntegrityError("unsupported recovery journal schema")
        raw_entries = snapshot.get("entries", [])
        if not isinstance(raw_entries, Sequence) or isinstance(raw_entries, (str, bytes)):
            raise DurableCoreIntegrityError("journal entries must be a sequence")
        declared = int(snapshot.get("declared_count", -1))
        if declared < 0 or declared > self.policy.max_journal_entries:
            raise DurableCoreIntegrityError("journal declaration is outside the bounded range")
        if declared != len(raw_entries):
            raise DurableCoreIntegrityError("journal declaration does not match its entries")
        restored: list[JournalEntry] = []
        for item in raw_entries:
            if not isinstance(item, Mapping):
                raise DurableCoreIntegrityError("journal entry is not a mapping")
            kind = str(item.get("kind", ""))
            if kind not in _JOURNAL_KINDS:
                raise DurableCoreIntegrityError("unsupported journal entry kind in recovery snapshot")
            raw_payload = item.get("payload", {})
            if not isinstance(raw_payload, Mapping):
                raise DurableCoreIntegrityError("journal entry payload is not a mapping")
            if any(str(key) not in _JOURNAL_PAYLOAD_KEYS for key in raw_payload):
                raise DurableCoreIntegrityError("unsupported journal payload key in recovery snapshot")
            payload = dict(raw_payload)
            restored.append(
                JournalEntry(
                    sequence=int(item["sequence"]),
                    kind=kind,
                    workflow_key=str(item["workflow_key"]),
                    fingerprint=str(item["fingerprint"]),
                    payload=payload,
                    previous_digest=str(item["previous_digest"]),
                    digest=str(item["digest"]),
                )
            )
        previous = _GENESIS_DIGEST
        for index, entry in enumerate(restored, start=1):
            expected = _journal_digest(
                sequence=entry.sequence,
                kind=entry.kind,
                workflow_key=entry.workflow_key,
                fingerprint=entry.fingerprint,
                payload=entry.payload,
                previous_digest=entry.previous_digest,
            )
            if entry.sequence != index or entry.previous_digest != previous:
                raise DurableCoreIntegrityError("restored journal link is broken")
            if expected != entry.digest:
                raise DurableCoreIntegrityError("restored journal digest is invalid")
            previous = entry.digest
        if str(snapshot.get("tail_digest", "")) != previous:
            raise DurableCoreIntegrityError("restored journal tail does not match")
        self._entries = restored
        self._declared_count = len(restored)
        self._tail_digest = previous


class DurableCoreOutbox:
    """Bounded synthetic outbox envelope store; no broker or table is used."""

    def __init__(self, policy: DurableCorePolicy | None = None) -> None:
        self.policy = policy or DurableCorePolicy()
        self._entries: dict[str, OutboxEnvelope] = {}

    def enqueue(self, envelope: OutboxEnvelope) -> bool:
        existing = self._entries.get(envelope.fingerprint)
        if existing is not None:
            if existing.payload_digest != envelope.payload_digest:
                raise DurableCoreConflict("outbox fingerprint was reused with a different payload")
            return False
        if len(self._entries) >= self.policy.max_outbox_entries:
            raise DurableCoreError("outbox depth cap reached")
        self._entries[envelope.fingerprint] = envelope
        return True

    def mark_status(self, *, workflow_key: str, status: str) -> int:
        changed = 0
        for fingerprint, envelope in self._entries.items():
            if envelope.workflow_key == workflow_key and envelope.status != status:
                self._entries[fingerprint] = replace(envelope, status=status)
                changed += 1
        return changed

    def summary(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for envelope in self._entries.values():
            counts[envelope.status] = counts.get(envelope.status, 0) + 1
        return {"total": len(self._entries), "by_status": counts}

    def snapshot(self) -> list[dict[str, Any]]:
        return [envelope.to_dict() for envelope in self._entries.values()]

    def restore(self, raw_entries: Sequence[Mapping[str, Any]]) -> None:
        restored: dict[str, OutboxEnvelope] = {}
        for item in raw_entries:
            envelope = OutboxEnvelope.from_mapping(item)
            if envelope.fingerprint in restored:
                raise DurableCoreIntegrityError("duplicate outbox fingerprint in recovery snapshot")
            restored[envelope.fingerprint] = envelope
        if len(restored) > self.policy.max_outbox_entries:
            raise DurableCoreIntegrityError("outbox recovery snapshot exceeds the depth cap")
        self._entries = restored


class OfflineRecoveryPolicy:
    """Bounded retry policy over the existing store-forward engine."""

    def __init__(self, adapter: Any, policy: DurableCorePolicy | None = None) -> None:
        self.adapter = adapter
        self.policy = policy or DurableCorePolicy()
        self._next_retry: dict[str, float] = {}

    def snapshot(self) -> list[dict[str, float]]:
        return [
            {"id": key, "next_retry_at": value} for key, value in sorted(self._next_retry.items())
        ]

    def restore(self, raw_schedule: Sequence[Mapping[str, float]]) -> None:
        if len(raw_schedule) > self.policy.max_offline_entries:
            raise DurableCoreIntegrityError("offline retry schedule exceeds the depth cap")
        restored: dict[str, float] = {}
        for item in raw_schedule:
            key = str(item["id"])
            value = float(item["next_retry_at"])
            if not key or key in restored:
                raise DurableCoreIntegrityError("offline retry schedule has an invalid or duplicate id")
            if not math.isfinite(value) or value < 0:
                raise DurableCoreIntegrityError("offline retry schedule has a non-finite time")
            restored[key] = value
        self._next_retry = restored

    @staticmethod
    def _jitter(entry_id: str, attempt: int) -> float:
        digest = hashlib.sha256(f"{entry_id}:{attempt}".encode()).hexdigest()
        return (int(digest[:8], 16) % 1000) / 1000.0

    async def sync(self, *, now: float) -> dict[str, Any]:
        queue = self.adapter.store_forward.snapshot()
        eligible_ids = {
            str(item["id"])
            for item in queue
            if str(item.get("status")) == "pending"
            and now >= self._next_retry.get(str(item["id"]), 0.0)
        }
        deferred = sum(1 for item in queue if str(item.get("status")) == "pending") - len(
            eligible_ids
        )
        dead_before = len(self.adapter.store_forward.list_dead())
        summary = await self.adapter.offline_sync.sync_all(
            eligible=lambda entry: entry.id in eligible_ids
        )
        for result in summary.get("results", []):
            entry_id = str(result.get("id", ""))
            if result.get("status") == "failed":
                entry = next(
                    (
                        item
                        for item in self.adapter.store_forward.snapshot()
                        if str(item["id"]) == entry_id
                    ),
                    None,
                )
                attempt = int(entry.get("retry_count", 1)) if entry else 1
                if attempt >= self.policy.max_offline_attempts:
                    self.adapter.store_forward.force_dead(
                        entry_id, str(result.get("error", "bounded retry exhaustion"))
                    )
                    self._next_retry.pop(entry_id, None)
                    continue
                delay = min(
                    self.policy.backoff_base_seconds * (2 ** max(0, attempt - 1)),
                    self.policy.backoff_cap_seconds,
                )
                self._next_retry[entry_id] = now + delay + self._jitter(entry_id, attempt)
            else:
                self._next_retry.pop(entry_id, None)
        dead_after = len(self.adapter.store_forward.list_dead())
        bounded = {key: value for key, value in summary.items() if key != "results"}
        bounded.update(
            {
                "attempted": len(eligible_ids),
                "deferred": deferred,
                "dead": dead_after,
                "newly_dead": max(0, dead_after - dead_before),
                "scheduled": len(self._next_retry),
            }
        )
        return bounded


# -- FHIR disclosure pre-check ----------------------------------------------


class FHIRDisclosureGuard:
    """Strict synthetic pre-check; explicitly not full FHIR conformance."""

    def validate(
        self,
        bundle: Mapping[str, Any],
        *,
        expected_patient_reference: str,
        expected_organization_id: str | None = None,
        allowed_code_systems: frozenset[str] | None = None,
    ) -> FHIRGuardResult:
        errors: list[str] = []
        systems = allowed_code_systems or _ALLOWED_CODING_SYSTEMS
        if not isinstance(expected_patient_reference, str) or not expected_patient_reference:
            errors.append("expected patient reference is required")
        if bundle.get("resourceType") != "Bundle":
            errors.append("bundle resourceType must be Bundle")
        entries = bundle.get("entry")
        if not isinstance(entries, (list, tuple)) or not 1 <= len(entries) <= 100:
            errors.append("bundle entry count is outside the synthetic bound")
            entries = []
        serialized = json.dumps(bundle, sort_keys=True, default=str)
        if _RAW_NID_RUN.search(serialized):
            errors.append("bundle contains a raw identifier-shaped value")
        sensitive_paths = _walk_sensitive(bundle)
        if sensitive_paths:
            errors.append(f"bundle contains disallowed fields: {sensitive_paths[:5]}")

        resources: list[dict[str, Any]] = []
        resource_index: dict[tuple[str, str], dict[str, Any]] = {}
        for index, item in enumerate(entries):
            if not isinstance(item, Mapping):
                errors.append(f"entry[{index}] is not a mapping")
                continue
            resource = item.get("resource")
            if not isinstance(resource, Mapping):
                errors.append(f"entry[{index}] has no resource")
                continue
            resource_dict = dict(resource)
            resources.append(resource_dict)
            resource_type = str(resource_dict.get("resourceType", ""))
            resource_id = str(resource_dict.get("id", ""))
            full_url = str(item.get("fullUrl", ""))
            if full_url != f"urn:uuid:{resource_id}":
                errors.append(f"entry[{index}] fullUrl does not match its resource id")
            key = (resource_type, resource_id)
            if key in resource_index:
                errors.append(f"duplicate bundle resource reference at entry[{index}]")
            else:
                resource_index[key] = resource_dict
            tags = (
                resource_dict.get("meta", {}).get("tag", [])
                if isinstance(resource_dict.get("meta"), Mapping)
                else []
            )
            has_synthetic_tag = any(
                isinstance(tag, Mapping)
                and tag.get("system") == SYNTHETIC_TAG_SYSTEM
                and tag.get("code") == SYNTHETIC_TAG_CODE
                for tag in tags
            )
            if not has_synthetic_tag:
                errors.append(f"{resource_type or 'resource'} lacks the synthetic provenance tag")
            validation = FHIRValidationEngine().validate(resource_dict)
            errors.extend(f"{resource_type}: {error}" for error in validation.errors)

        errors.extend(validate_synthetic_bundle(dict(bundle)))

        expected_patient_ref = f"Patient/{expected_patient_reference}"
        reference_count = 0
        for resource in resources:
            contained_ids = {
                str(item.get("id"))
                for item in resource.get("contained", [])
                if isinstance(item, Mapping)
            }
            for reference in self._references(resource):
                reference_count += 1
                if reference.startswith("#"):
                    if reference[1:] not in contained_ids:
                        errors.append(
                            f"{resource['resourceType']} has an unresolved contained reference"
                        )
                    continue
                match = re.fullmatch(r"([A-Za-z]+)/([A-Za-z0-9._\-]+)", reference)
                if match is None:
                    errors.append(f"{resource['resourceType']} has an unsupported reference form")
                    continue
                target = (match.group(1), match.group(2))
                if target not in resource_index:
                    errors.append(f"{resource['resourceType']} references a missing {reference}")
                if reference.startswith("Patient/") and reference != expected_patient_ref:
                    errors.append(f"{resource['resourceType']} discloses a different patient")
            organization = resource.get("managingOrganization") or resource.get("performer")
            if expected_organization_id and isinstance(organization, Mapping):
                reference = str(organization.get("reference", ""))
                if reference and reference != f"Organization/{expected_organization_id}":
                    errors.append(f"{resource['resourceType']} discloses a different organization")

        for resource in resources:
            for coding in self._codings(resource):
                if not isinstance(coding, Mapping):
                    errors.append(f"{resource['resourceType']} has a malformed coding entry")
                    continue
                system = str(coding.get("system", ""))
                if system not in systems:
                    errors.append(f"{resource['resourceType']} uses an unsupported code system")
                if not str(coding.get("code", "")).strip():
                    errors.append(f"{resource['resourceType']} has an empty terminology code")
            quantity = resource.get("valueQuantity")
            if isinstance(quantity, Mapping):
                if quantity.get("system") != _UCUM_SYSTEM:
                    errors.append(f"{resource['resourceType']} does not bind UCUM explicitly")
                if not str(quantity.get("code", "")).strip():
                    errors.append(f"{resource['resourceType']} omits the UCUM code")
                elif str(quantity.get("code")) != str(quantity.get("unit", "")):
                    errors.append(f"{resource['resourceType']} UCUM code and unit disagree")

        return FHIRGuardResult(
            valid=not errors,
            errors=tuple(dict.fromkeys(errors)),
            resource_types=tuple(
                dict.fromkeys(str(item.get("resourceType", "")) for item in resources)
            ),
            reference_count=reference_count,
        )

    def assert_valid(
        self,
        bundle: Mapping[str, Any],
        *,
        expected_patient_reference: str,
        expected_organization_id: str | None = None,
    ) -> FHIRGuardResult:
        result = self.validate(
            bundle,
            expected_patient_reference=expected_patient_reference,
            expected_organization_id=expected_organization_id,
        )
        if not result.valid:
            raise FHIRDisclosureDenied("; ".join(result.errors[:10]))
        return result

    @staticmethod
    def _references(value: Any) -> list[str]:
        found: list[str] = []
        if isinstance(value, Mapping):
            for key, item in value.items():
                if key in {"reference", "subject", "patient", "specimen", "target", "request"}:
                    found.extend(FHIRDisclosureGuard._reference_values(item))
                else:
                    found.extend(FHIRDisclosureGuard._references(item))
        elif isinstance(value, (list, tuple)):
            for item in value:
                found.extend(FHIRDisclosureGuard._references(item))
        return found

    @staticmethod
    def _reference_values(value: Any) -> list[str]:
        if isinstance(value, Mapping):
            reference = value.get("reference")
            if isinstance(reference, str):
                return [reference]
            return FHIRDisclosureGuard._references(value)
        if isinstance(value, str):
            return [value]
        if isinstance(value, (list, tuple)):
            result: list[str] = []
            for item in value:
                result.extend(FHIRDisclosureGuard._reference_values(item))
            return result
        return []

    @staticmethod
    def _codings(value: Any) -> list[Any]:
        found: list[Any] = []
        if isinstance(value, Mapping):
            for key, item in value.items():
                if key == "coding" and isinstance(item, (list, tuple)):
                    found.extend(item)
                else:
                    found.extend(FHIRDisclosureGuard._codings(item))
        elif isinstance(value, (list, tuple)):
            for item in value:
                found.extend(FHIRDisclosureGuard._codings(item))
        return found


# -- Laboratory lineage and longitudinal projection contract ----------------


class ResultLineageLedger:
    """Append-only lineage for synthetic result revisions; not a LIMS store."""

    def __init__(self, catalog: NationalLaboratoryCatalog | None = None) -> None:
        if catalog is None:
            catalog = NationalLaboratoryCatalog()
            catalog.seed_common_tests()
        self.catalog = catalog
        self._records: dict[str, ResultRegistration] = {}

    def register(self, case: SyntheticLabCase) -> ResultRegistration:
        fingerprint = _stable_digest(case)
        existing = self._records.get(case.result.result_id)
        if existing is not None:
            if existing.fingerprint != fingerprint:
                raise DurableCoreConflict("result id was reused with a different payload")
            return replace(existing, replayed=True)
        registration = ResultRegistration(
            result_id=case.result.result_id,
            fingerprint=fingerprint,
            revision=1,
            supersedes=None,
            status="registered",
            released=False,
        )
        self._records[case.result.result_id] = registration
        return registration

    def mark_released(
        self, *, result_id: str, decision_status: str, decision_result_id: str
    ) -> None:
        record = self._records.get(result_id)
        if record is None:
            raise DurableCoreError("result was not registered in the lineage ledger")
        if decision_status != RELEASE_RELEASED or decision_result_id != result_id:
            raise DurableCoreError("only an explicit release decision can mark a result released")
        self._records[result_id] = replace(record, status="released", released=True)

    def correct(
        self,
        case: SyntheticLabCase,
        *,
        corrected_value: float,
        reason: str,
        reviewer: str,
        corrected_result_id: str,
    ) -> ResultCorrection:
        _bounded_reviewer(reason, "reason")
        _bounded_reviewer(reviewer, "reviewer")
        _bounded_reviewer(corrected_result_id, "corrected_result_id")
        original = self._records.get(case.result.result_id)
        if original is None or not original.released:
            raise DurableCoreError("only a released result can be corrected")
        if corrected_result_id == case.result.result_id:
            raise DurableCoreConflict("a correction must use a new result id")
        if corrected_result_id in self._records:
            raise DurableCoreConflict("corrected result id is already registered")
        if any(record.supersedes == case.result.result_id for record in self._records.values()):
            raise DurableCoreConflict("this result already has a correction")
        from dataclasses import replace as dataclass_replace

        corrected_result = dataclass_replace(
            case.result,
            result_id=corrected_result_id,
            value=float(corrected_value),
            previous_value=case.result.value,
        )
        corrected_case = dataclass_replace(case, result=corrected_result)
        if corrected_result.patient_id != case.patient.patient_id:
            raise DurableCoreError("corrected result belongs to a different patient")
        if not (
            corrected_result.reference_low
            <= corrected_result.value
            <= corrected_result.reference_high
        ):
            raise DurableCoreError("corrected value is outside the synthetic reference range")
        if (
            corrected_result.critical_low is not None
            and corrected_result.value <= corrected_result.critical_low
        ) or (
            corrected_result.critical_high is not None
            and corrected_result.value >= corrected_result.critical_high
        ):
            raise DurableCoreError("corrected critical value requires quarantine, not correction")
        binding = bind_test(self.catalog, corrected_result.test_code)
        if binding.status == BINDING_UNMAPPED or binding.unit != corrected_result.unit:
            raise DurableCoreError("corrected result has unsupported terminology or unit")
        fingerprint = _stable_digest(corrected_case)
        if any(record.fingerprint == fingerprint for record in self._records.values()):
            raise DurableCoreConflict("corrected result fingerprint already exists")
        registration = ResultRegistration(
            result_id=corrected_result.result_id,
            fingerprint=fingerprint,
            revision=original.revision + 1,
            supersedes=original.result_id,
            status="pending_review",
            released=False,
        )
        self._records[corrected_result.result_id] = registration
        return ResultCorrection(case=corrected_case, registration=registration)

    def snapshot(self) -> list[dict[str, Any]]:
        return [record.to_dict() for record in self._records.values()]

    def restore(self, raw_records: Sequence[Mapping[str, Any]]) -> None:
        restored: dict[str, ResultRegistration] = {}
        for item in raw_records:
            record = ResultRegistration.from_mapping(item)
            if record.result_id in restored:
                raise DurableCoreIntegrityError("duplicate result lineage record in snapshot")
            restored[record.result_id] = record
        self._records = restored


class LongitudinalProjectionContract:
    """Idempotent bounded projection envelope; no EHR write or durable row."""

    def __init__(self) -> None:
        self._events: dict[str, LongitudinalEvent] = {}
        self._failures: dict[str, int] = {}

    def project(
        self,
        case: SyntheticLabCase,
        decision: Any,
        *,
        expected_patient_reference: str,
        fail: bool = False,
    ) -> LongitudinalEvent:
        record = decision
        if getattr(record, "status", None) != RELEASE_RELEASED:
            raise DurableCoreProjectionError(
                "unreleased results cannot enter a longitudinal projection"
            )
        if getattr(record, "result_id", None) != case.result.result_id:
            raise DurableCoreProjectionError("decision and result are not bound")
        if case.result.patient_id != expected_patient_reference:
            raise DurableCoreProjectionError("result belongs to a different patient")
        event_id = f"synthetic-longitudinal-{hashlib.sha256(_stable_digest(case).encode()).hexdigest()[:20]}"
        existing = self._events.get(event_id)
        if existing is not None:
            return replace(existing, replayed=True)
        if fail:
            self._failures[event_id] = self._failures.get(event_id, 0) + 1
            raise DurableCoreProjectionError("synthetic EHR projection interruption")
        event = LongitudinalEvent(
            event_id=event_id,
            patient_reference=case.patient.patient_id,
            result_reference=case.result.result_id,
            decision_reference=str(getattr(record, "decision_id", "")),
            revision=1,
            status="projected_envelope_only",
            replayed=False,
        )
        self._events[event_id] = event
        return event

    def failure_count(self, event_id: str) -> int:
        return self._failures.get(event_id, 0)

    def snapshot(self) -> dict[str, Any]:
        return {
            "events": [event.to_dict() for event in self._events.values()],
            "failures": dict(self._failures),
        }


# -- Coordinator ------------------------------------------------------------


class DurableNationalCoreCoordinator:
    """Compose the Leap 02 workflow with synthetic recovery contracts."""

    def __init__(
        self,
        workflow: NationalCoreWorkflow | None = None,
        policy: DurableCorePolicy | None = None,
    ) -> None:
        self.policy = policy or DurableCorePolicy()
        self.workflow = workflow or NationalCoreWorkflow()
        self.journal = DurableCoreJournal(self.policy)
        self.outbox = DurableCoreOutbox(self.policy)
        self.receipts: dict[str, DurableCoreReceipt] = {}
        self.offline = OfflineRecoveryPolicy(self.workflow.adapter, self.policy)
        self._locks: dict[tuple[str, int], asyncio.Lock] = {}

    def _lock(self, workflow_key: str) -> asyncio.Lock:
        key = (workflow_key, id(asyncio.get_running_loop()))
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    @staticmethod
    def _fingerprint(command: NationalCoreWorkflowCommand) -> str:
        workflow_fingerprint = NationalCoreWorkflow._fingerprint(command)
        return hashlib.sha256(f"{DURABLE_CORE_SCHEMA}:{workflow_fingerprint}".encode()).hexdigest()

    @staticmethod
    def _preflight(command: NationalCoreWorkflowCommand, now: datetime) -> None:
        for label, value in (
            ("workflow_key", command.workflow_key),
            ("correlation_id", command.correlation_id),
            ("organization_id", command.organization_id),
            ("facility_id", command.facility_id),
        ):
            if _RAW_NID_RUN.search(value):
                raise DurableCoreAuthorizationError(f"{label} contains an identifier-shaped value")
        if command.identity.secondary_nid_hash not in (None, command.identity.national_id_hash):
            raise DurableCoreAuthorizationError(
                "D-IDENTITY-02 unresolved: conflicting NID hashes veto linkage"
            )
        if not command.identity.nid_verified:
            raise DurableCoreAuthorizationError("identity evidence is not verified")
        if command.organization_id != command.access.request.organization_id:
            raise DurableCoreAuthorizationError("cross-institution access is denied")
        if command.facility_id != command.access.request.facility_id:
            raise DurableCoreAuthorizationError("cross-facility access is denied")
        session = command.access.actor.session
        expires_at = getattr(session, "expires_at", None)
        if expires_at is None or expires_at <= (command.now or now):
            raise DurableCoreAuthorizationError("authorization session is expired")

    async def run(
        self,
        session: Any,
        command: NationalCoreWorkflowCommand,
        *,
        now: datetime | None = None,
    ) -> DurableCoreExecutionResult:
        now = now or datetime.now(UTC)
        fingerprint = self._fingerprint(command)
        async with self._lock(command.workflow_key):
            integrity = self.journal.verify()
            if integrity["status"] != "VALID":
                raise DurableCoreIntegrityError("recovery journal integrity check failed")
            existing = self.receipts.get(command.workflow_key)
            if existing is not None:
                if existing.fingerprint != fingerprint:
                    _metric(outcome="rejected", reason="duplicate_command")
                    raise DurableCoreReplayError("workflow key was reused with different inputs")
                if existing.status == RECEIPT_COMMITTED:
                    self.journal.append(
                        kind=JOURNAL_REPLAY,
                        workflow_key=command.workflow_key,
                        fingerprint=fingerprint,
                        payload={"status": "replayed"},
                    )
                    _metric(outcome="completed")
                    return DurableCoreExecutionResult(
                        schema_version=DURABLE_CORE_SCHEMA,
                        workflow_key=command.workflow_key,
                        correlation_id=command.correlation_id,
                        fingerprint=fingerprint,
                        replayed=True,
                        receipt=existing,
                        workflow_result=None,
                        outbox_summary=self.outbox.summary(),
                        offline_summary={},
                        integrity=self.journal.verify(),
                    )
                if existing.status == RECEIPT_PENDING:
                    _metric(outcome="rejected", reason="invalid_state_transition")
                    raise DurableCoreRecoveryRequired("interrupted command must be recovered first")
                if existing.attempts >= self.policy.max_command_attempts:
                    _metric(outcome="rejected", reason="invalid_state_transition")
                    raise DurableCoreError("command attempt cap reached")

            if len(self.receipts) >= self.policy.max_receipts and existing is None:
                raise DurableCoreError("receipt depth cap reached")
            self._preflight(command, now)
            timestamp = (command.now or now).isoformat()
            attempts = 1 if existing is None else existing.attempts + 1
            pending = DurableCoreReceipt(
                workflow_key=command.workflow_key,
                correlation_id=command.correlation_id,
                fingerprint=fingerprint,
                status=RECEIPT_PENDING,
                attempts=attempts,
                result_digest="",
                created_at=existing.created_at if existing else timestamp,
                updated_at=timestamp,
            )
            self.receipts[command.workflow_key] = pending
            self.journal.append(
                kind=JOURNAL_INTENT,
                workflow_key=command.workflow_key,
                fingerprint=fingerprint,
                payload={"status": RECEIPT_PENDING, "attempts": attempts},
            )
            if self.policy.hard_interrupt_before_workflow:
                # BaseException models a process restart that cannot run the
                # normal failure journal append; recovery must be explicit.
                raise KeyboardInterrupt("synthetic process restart before workflow")
            try:
                if self.policy.fail_before_workflow:
                    raise DurableCoreInterruptionError("synthetic pre-workflow interruption")
                workflow_result = await self.workflow.run(session, command)
                if workflow_result.audit_verification.get("status") != "VALID":
                    raise DurableCoreError("canonical audit chain verification failed")
                if self.policy.fail_after_workflow:
                    raise DurableCoreInterruptionError("synthetic post-workflow interruption")
                public = workflow_result.to_public_dict()
                envelope = OutboxEnvelope(
                    fingerprint=fingerprint,
                    workflow_key=command.workflow_key,
                    correlation_id=command.correlation_id,
                    entity_type="durable_core_recovery",
                    entity_id=str(public.get("bundle_reference") or public.get("result_id") or ""),
                    payload_digest=_stable_digest(public),
                )
                self.outbox.enqueue(envelope)
                offline_summary = await self.offline.sync(now=(command.now or now).timestamp())
                if offline_summary.get("synced", 0) or offline_summary.get("duplicates", 0):
                    self.outbox.mark_status(workflow_key=command.workflow_key, status="delivered")
                committed = replace(
                    pending,
                    status=RECEIPT_COMMITTED,
                    result_digest=envelope.payload_digest,
                    updated_at=(command.now or now).isoformat(),
                )
                self.receipts[command.workflow_key] = committed
                self.journal.append(
                    kind=JOURNAL_COMMIT,
                    workflow_key=command.workflow_key,
                    fingerprint=fingerprint,
                    payload={"status": RECEIPT_COMMITTED, "attempts": attempts},
                )
            except Exception as exc:
                message = str(exc)
                if "audit" in message.casefold():
                    clinical_safety_metrics.record_audit_failure(
                        operation=_METRIC_OPERATION, resource_type=_METRIC_RESOURCE
                    )
                failed = replace(
                    pending,
                    status=RECEIPT_FAILED,
                    updated_at=(command.now or now).isoformat(),
                )
                self.receipts[command.workflow_key] = failed
                self.journal.append(
                    kind=JOURNAL_FAIL,
                    workflow_key=command.workflow_key,
                    fingerprint=fingerprint,
                    payload={"reason": _safe_reason(message), "status": RECEIPT_FAILED},
                )
                _metric(outcome="rejected", reason=_safe_reason(message))
                raise
            _metric(outcome="completed")
            return DurableCoreExecutionResult(
                schema_version=DURABLE_CORE_SCHEMA,
                workflow_key=command.workflow_key,
                correlation_id=command.correlation_id,
                fingerprint=fingerprint,
                replayed=False,
                receipt=self.receipts[command.workflow_key],
                workflow_result=workflow_result,
                outbox_summary=self.outbox.summary(),
                offline_summary=offline_summary,
                integrity=self.journal.verify(),
            )

    def recover(self, snapshot: Mapping[str, Any] | None = None) -> DurableCoreRecoveryResult:
        """Recover synthetic receipt state after an interruption or restart."""

        if snapshot is not None:
            self.restore(snapshot)
        integrity = self.journal.verify()
        if integrity["status"] != "VALID":
            raise DurableCoreIntegrityError("cannot recover from an invalid journal")
        pending = [key for key, value in self.receipts.items() if value.status == RECEIPT_PENDING]
        for key in pending:
            record = self.receipts[key]
            self.receipts[key] = replace(record, status=RECEIPT_FAILED)
            self.journal.append(
                kind=JOURNAL_RECOVERY,
                workflow_key=key,
                fingerprint=record.fingerprint,
                payload={"recovered": 1, "status": RECEIPT_FAILED},
            )
        _metric(outcome="completed" if not pending else "rejected", reason="recovery")
        return DurableCoreRecoveryResult(
            schema_version=DURABLE_CORE_SCHEMA,
            pending_found=len(pending),
            recovered=len(pending),
            receipts=len(self.receipts),
            outbox_entries=self.outbox.summary()["total"],
            integrity=self.journal.verify(),
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": DURABLE_CORE_SCHEMA,
            "journal": self.journal.snapshot(),
            "receipts": [value.to_dict() for value in self.receipts.values()],
            "outbox": self.outbox.snapshot(),
            "offline_schedule": self.offline.snapshot(),
            "policy": {
                "max_receipts": self.policy.max_receipts,
                "max_outbox_entries": self.policy.max_outbox_entries,
                "max_journal_entries": self.policy.max_journal_entries,
                "max_command_attempts": self.policy.max_command_attempts,
                "max_offline_attempts": self.policy.max_offline_attempts,
                "max_offline_entries": self.policy.max_offline_entries,
            },
        }

    def restore(self, snapshot: Mapping[str, Any]) -> None:
        if snapshot.get("schema") != DURABLE_CORE_SCHEMA:
            raise DurableCoreIntegrityError("unsupported durable core recovery schema")
        self.journal.restore(snapshot["journal"])
        self.outbox.restore(snapshot.get("outbox", []))
        raw_receipts = snapshot.get("receipts", [])
        receipts: dict[str, DurableCoreReceipt] = {}
        for item in raw_receipts:
            receipt = DurableCoreReceipt.from_mapping(item)
            if receipt.workflow_key in receipts:
                raise DurableCoreIntegrityError("duplicate receipt in recovery snapshot")
            receipts[receipt.workflow_key] = receipt
        if len(receipts) > self.policy.max_receipts:
            raise DurableCoreIntegrityError("receipt snapshot exceeds the depth cap")
        self.receipts = receipts
        self.offline.restore(snapshot.get("offline_schedule", []))


__all__ = [
    "DURABLE_CORE_LAYERS",
    "DURABLE_CORE_SCHEMA",
    "DurableCoreAuthorizationError",
    "DurableCoreConflict",
    "DurableCoreError",
    "DurableCoreExecutionResult",
    "DurableCoreIntegrityError",
    "DurableCoreInterruptionError",
    "DurableCoreJournal",
    "DurableCoreOutbox",
    "DurableCorePolicy",
    "DurableCoreRecoveryRequired",
    "DurableCoreReplayError",
    "DurableNationalCoreCoordinator",
    "FHIRDisclosureDenied",
    "FHIRDisclosureGuard",
    "FHIRGuardResult",
    "LongitudinalEvent",
    "LongitudinalProjectionContract",
    "OfflineRecoveryPolicy",
    "OutboxEnvelope",
    "ResultCorrection",
    "ResultLineageLedger",
    "ResultRegistration",
]
