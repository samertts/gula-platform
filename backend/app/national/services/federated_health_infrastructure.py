"""Additive synthetic contracts for a federated national health infrastructure.

This module is deliberately route-free, DDL-free, and dependency-free. It adds
registry, custody, disclosure, referral, exchange, reconciliation, and
privacy-safe observability contracts over canonical services. It does not
implement a second identity, MPI, audit, outbox, FHIR, or offline authority.

All state is process-local and synthetic. No production endpoint, credential,
real patient record, or government system is touched.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Any

from app._compat import UTC
from app.clinical.observability import clinical_safety_metrics, reason_code
from app.contracts.integration import IntegrationEventEnvelope, normalize_correlation_id
from app.national.enums import FacilityType, ReferralPriority, ReferralStatus
from app.national.services import durable_clinical_core as _durable

FEDERATION_SCHEMA = "national_federated_health_infrastructure.v1.synthetic"
FEDERATION_SOURCE = "national_federated_health_infrastructure_synthetic"
_METRIC_OPERATION = "federated_national_health"
_METRIC_RESOURCE = "federated_exchange"

INSTITUTION_REGISTERED = "registered"
INSTITUTION_VERIFIED = "verified"
INSTITUTION_AUTHORIZED = "authorized"
INSTITUTION_SUSPENDED = "suspended"
INSTITUTION_REVOKED = "revoked"
_INSTITUTION_STATES = frozenset(
    {
        INSTITUTION_REGISTERED,
        INSTITUTION_VERIFIED,
        INSTITUTION_AUTHORIZED,
        INSTITUTION_SUSPENDED,
        INSTITUTION_REVOKED,
    }
)
_ACTIVE_INSTITUTION_STATES = frozenset({INSTITUTION_VERIFIED, INSTITUTION_AUTHORIZED})
_INSTITUTION_TRANSITIONS = {
    INSTITUTION_REGISTERED: frozenset({INSTITUTION_VERIFIED, INSTITUTION_REVOKED}),
    INSTITUTION_VERIFIED: frozenset({INSTITUTION_AUTHORIZED, INSTITUTION_SUSPENDED, INSTITUTION_REVOKED}),
    INSTITUTION_AUTHORIZED: frozenset({INSTITUTION_SUSPENDED, INSTITUTION_REVOKED}),
    INSTITUTION_SUSPENDED: frozenset({INSTITUTION_AUTHORIZED, INSTITUTION_REVOKED}),
    INSTITUTION_REVOKED: frozenset(),
}

KIND_NATIONAL = "national"
KIND_DIRECTORATE = "directorate"
KIND_FACILITY = "facility"
_INSTITUTION_KINDS = frozenset({KIND_NATIONAL, KIND_DIRECTORATE, KIND_FACILITY})

TRUST_ACTIVE = "active"
TRUST_REVOKED = "revoked"

DATA_CATEGORIES = frozenset(
    {
        "identity_reference",
        "referral",
        "lab_order",
        "lab_result",
        "clinical_document",
        "public_health_aggregate",
    }
)
APPROVED_PURPOSES = frozenset({"treatment", "referral", "public_health_authorized", "care_coordination"})
PROFESSIONAL_ROLES = frozenset(
    {"physician", "nurse", "technician", "directorate_coordinator", "national_coordinator"}
)
EMERGENCY_REASONS = frozenset(
    {"emergency", "trauma", "cardiac_arrest", "mass_casualty", "critical_care"}
)

REFERRAL_CREATED = "created"
REFERRAL_ROUTED = "routed"
REFERRAL_TRANSMITTED = "transmitted"
REFERRAL_ACKNOWLEDGED = "acknowledged"
REFERRAL_ACCEPTED = "accepted"
REFERRAL_REJECTED = "rejected"
REFERRAL_EXPIRED = "expired"
REFERRAL_CANCELLED = "cancelled"

EXCHANGE_CREATED = "created"
EXCHANGE_SENT = "sent"
EXCHANGE_DELIVERED = "delivered"
EXCHANGE_ACKNOWLEDGED = "acknowledged"
EXCHANGE_RETRY_SCHEDULED = "retry_scheduled"
EXCHANGE_DEAD_LETTER = "dead_letter"
EXCHANGE_CONFLICT = "reconciliation_required"

CONSENT_ACTIVE = "active"
CONSENT_ABSENT = "absent"
CONSENT_WITHDRAWN = "withdrawn"
CONSENT_EXPIRED = "expired"

_RAW_IDENTIFIER = _durable._RAW_NID_RUN
_OPAQUE = _durable._OPAQUE
_SENSITIVE_KEYS = _durable._SENSITIVE_KEYS
_ISO_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
_HEX_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_MAX_TEXT = 200


class FederationError(RuntimeError):
    """Base class for federated contract failures."""


class FederationDenied(FederationError):
    """A deny-by-default policy or trust decision."""


class FederationValidationError(FederationError):
    """Malformed or unsupported synthetic input."""


class FederationConflict(FederationError):
    """A conflicting clinical revision that must not be overwritten."""


class FederationIntegrityError(FederationError):
    """Provenance, digest, or snapshot integrity failure."""


@dataclass(frozen=True)
class FederationPolicy:
    """Bounded process-local limits for all federated contracts."""

    max_institutions: int = 128
    max_trust_relations: int = 256
    max_records: int = 512
    max_envelopes: int = 512
    max_audit_events: int = 2048
    max_retries: int = 3
    retry_base_seconds: float = 1.0
    decision_window_seconds: int = 300

    def __post_init__(self) -> None:
        for label, value in (
            ("max_institutions", self.max_institutions),
            ("max_trust_relations", self.max_trust_relations),
            ("max_records", self.max_records),
            ("max_envelopes", self.max_envelopes),
            ("max_audit_events", self.max_audit_events),
            ("max_retries", self.max_retries),
            ("decision_window_seconds", self.decision_window_seconds),
        ):
            if value < 1 or value > 100_000:
                raise FederationValidationError(f"{label} is outside the bounded range")
        if not math.isfinite(self.retry_base_seconds) or self.retry_base_seconds <= 0:
            raise FederationValidationError("retry_base_seconds must be finite and positive")


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def _safe_reason(value: str) -> str:
    return reason_code(value)


def _metric(*, outcome: str, reason: str | None = None) -> None:
    clinical_safety_metrics.record_command(
        operation=_METRIC_OPERATION,
        resource_type=_METRIC_RESOURCE,
        outcome=outcome,
        reason=_safe_reason(reason or ""),
    )


def _opaque(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > _MAX_TEXT:
        raise FederationValidationError(f"{label} must be a bounded string")
    if not _OPAQUE.fullmatch(value):
        raise FederationValidationError(f"{label} is not an opaque reference")
    if _RAW_IDENTIFIER.search(value):
        raise FederationValidationError(f"{label} contains an identifier-shaped value")
    return value


def _digest_value(value: str, label: str) -> str:
    if not isinstance(value, str) or _HEX_DIGEST.fullmatch(value) is None:
        raise FederationValidationError(f"{label} must be a SHA-256 digest")
    return value


def _timestamp(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 64
        or _RAW_IDENTIFIER.search(value)
        or _ISO_TIMESTAMP.fullmatch(value) is None
    ):
        raise FederationValidationError(f"{label} is not a bounded ISO timestamp")
    try:
        datetime.fromisoformat(value)
    except ValueError as exc:
        raise FederationValidationError(f"{label} is not an ISO timestamp") from exc
    return value


def _now(now: datetime | None = None) -> datetime:
    return now or datetime.now(UTC)


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _reject_sensitive(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).casefold() in _SENSITIVE_KEYS:
                raise FederationValidationError(f"disallowed field at {path}.{key}")
            _reject_sensitive(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_sensitive(child, f"{path}[{index}]")
    elif isinstance(value, str) and _RAW_IDENTIFIER.search(value):
        segment = path.rsplit(".", 1)[-1]
        if not (_HEX_DIGEST.fullmatch(value) or segment.endswith("_digest")):
            raise FederationValidationError(f"identifier-shaped value at {path}")


@dataclass(frozen=True)
class InstitutionRecord:
    """Synthetic registry entry; never a credential or a real endpoint."""

    institution_id: str
    kind: str
    status: str
    endpoint_reference: str
    profiles: tuple[str, ...]
    capabilities: tuple[str, ...]
    directorate_id: str | None = None
    facility_type: str | None = None
    authorized_until: str | None = None
    provenance_digest: str = ""

    def __post_init__(self) -> None:
        _opaque(self.institution_id, "institution_id")
        _opaque(self.endpoint_reference, "endpoint_reference")
        if self.kind not in _INSTITUTION_KINDS:
            raise FederationValidationError("unsupported institution kind")
        if self.status not in _INSTITUTION_STATES:
            raise FederationValidationError("unsupported institution lifecycle state")
        if self.facility_type is not None and self.facility_type not in {
            item.value for item in FacilityType
        }:
            raise FederationValidationError("unsupported facility type")
        if self.directorate_id is not None:
            _opaque(self.directorate_id, "directorate_id")
        if self.authorized_until is not None:
            _timestamp(self.authorized_until, "authorized_until")
        if len(self.profiles) > 16 or len(self.capabilities) > 32:
            raise FederationValidationError("institution metadata is unbounded")
        for item in (*self.profiles, *self.capabilities):
            _opaque(item, "profile_or_capability")
        if not self.provenance_digest:
            object.__setattr__(self, "provenance_digest", self._compute_digest())

    def _compute_digest(self) -> str:
        return _digest(
            {
                "institution_id": self.institution_id,
                "kind": self.kind,
                "status": self.status,
                "endpoint_reference": self.endpoint_reference,
                "profiles": self.profiles,
                "capabilities": self.capabilities,
                "directorate_id": self.directorate_id,
                "facility_type": self.facility_type,
                "authorized_until": self.authorized_until,
            }
        )

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "schema": FEDERATION_SCHEMA,
            "institution_id": self.institution_id,
            "kind": self.kind,
            "status": self.status,
            "profiles": list(self.profiles),
            "capabilities": list(self.capabilities),
            "directorate_id": self.directorate_id,
            "facility_type": self.facility_type,
            "authorized_until": self.authorized_until,
            "provenance_digest": self.provenance_digest,
        }

    def to_snapshot_dict(self) -> dict[str, Any]:
        """Internal snapshot form: includes the synthetic endpoint reference."""

        return {**self.to_public_dict(), "endpoint_reference": self.endpoint_reference}


@dataclass(frozen=True)
class TrustRelation:
    source_institution_id: str
    target_institution_id: str
    scope: tuple[str, ...]
    expires_at: str
    status: str = TRUST_ACTIVE

    def __post_init__(self) -> None:
        _opaque(self.source_institution_id, "source_institution_id")
        _opaque(self.target_institution_id, "target_institution_id")
        if self.source_institution_id == self.target_institution_id:
            raise FederationValidationError("self-trust is not allowed")
        _timestamp(self.expires_at, "expires_at")
        if self.status not in {TRUST_ACTIVE, TRUST_REVOKED}:
            raise FederationValidationError("unsupported trust state")
        if not self.scope or not set(self.scope) <= DATA_CATEGORIES:
            raise FederationValidationError("trust scope is empty or unsupported")

    def digest(self) -> str:
        return _digest(
            {
                "source": self.source_institution_id,
                "target": self.target_institution_id,
                "scope": sorted(self.scope),
                "expires_at": self.expires_at,
                "status": self.status,
            }
        )


@dataclass(frozen=True)
class FederatedRecord:
    """Ownership metadata only; no clinical payload is stored here."""

    record_id: str
    institution_id: str
    patient_reference: str
    category: str
    revision: int
    event_sequence: int
    recorded_at: str
    classification: str
    disclosure_policy: str
    payload_digest: str
    integrity_digest: str = ""

    def __post_init__(self) -> None:
        for label, value in (
            ("record_id", self.record_id),
            ("institution_id", self.institution_id),
            ("patient_reference", self.patient_reference),
            ("classification", self.classification),
            ("disclosure_policy", self.disclosure_policy),
        ):
            _opaque(value, label)
        _digest_value(self.payload_digest, "payload_digest")
        _timestamp(self.recorded_at, "recorded_at")
        if self.category not in DATA_CATEGORIES:
            raise FederationValidationError("unsupported record category")
        if self.revision < 1 or self.event_sequence < 1:
            raise FederationValidationError("revision and event sequence must be positive")
        if not self.integrity_digest:
            object.__setattr__(self, "integrity_digest", self._compute_digest())

    def _compute_digest(self) -> str:
        return _digest(
            {
                "record_id": self.record_id,
                "institution_id": self.institution_id,
                "patient_reference": self.patient_reference,
                "category": self.category,
                "revision": self.revision,
                "event_sequence": self.event_sequence,
                "recorded_at": self.recorded_at,
                "classification": self.classification,
                "disclosure_policy": self.disclosure_policy,
                "payload_digest": self.payload_digest,
            }
        )

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "institution_id": self.institution_id,
            "patient_reference": self.patient_reference,
            "category": self.category,
            "revision": self.revision,
            "event_sequence": self.event_sequence,
            "recorded_at": self.recorded_at,
            "classification": self.classification,
            "disclosure_policy": self.disclosure_policy,
            "payload_digest": self.payload_digest,
            "integrity_digest": self.integrity_digest,
        }


@dataclass(frozen=True)
class EmergencyGrant:
    approver_reference: str
    reason_code: str
    categories: tuple[str, ...]
    expires_at: str
    audit_reference: str

    def __post_init__(self) -> None:
        for label, value in (
            ("approver_reference", self.approver_reference),
            ("reason_code", self.reason_code),
            ("audit_reference", self.audit_reference),
        ):
            _opaque(value, label)
        _timestamp(self.expires_at, "expires_at")
        if not self.categories or not set(self.categories) <= DATA_CATEGORIES:
            raise FederationValidationError("emergency scope is empty or unsupported")
        if "public_health_aggregate" in self.categories:
            raise FederationValidationError("emergency access cannot include public health aggregates")
        if self.reason_code not in EMERGENCY_REASONS:
            raise FederationValidationError("unsupported emergency reason code")


@dataclass(frozen=True)
class DisclosureRequest:
    requester_reference: str
    requesting_institution_id: str
    role: str
    relationship_reference: str
    purpose: str
    category: str
    legal_basis_reference: str
    consent_status: str
    audit_reference: str
    minimum_necessary: bool
    at: str
    emergency_grant: EmergencyGrant | None = None
    patient_reference: str | None = None
    record_reference: str | None = None

    def __post_init__(self) -> None:
        for label, value in (
            ("requester_reference", self.requester_reference),
            ("requesting_institution_id", self.requesting_institution_id),
            ("relationship_reference", self.relationship_reference),
            ("legal_basis_reference", self.legal_basis_reference),
            ("audit_reference", self.audit_reference),
        ):
            _opaque(value, label)
        if self.patient_reference is not None:
            _opaque(self.patient_reference, "patient_reference")
        if self.record_reference is not None:
            _opaque(self.record_reference, "record_reference")
        _timestamp(self.at, "at")
        if self.category not in DATA_CATEGORIES:
            raise FederationValidationError("unsupported disclosure category")
        if self.consent_status not in {
            CONSENT_ACTIVE,
            CONSENT_ABSENT,
            CONSENT_WITHDRAWN,
            CONSENT_EXPIRED,
        }:
            raise FederationValidationError("unsupported consent state")


@dataclass(frozen=True)
class DisclosureDecision:
    allowed: bool
    reason_code: str
    categories: tuple[str, ...]
    expires_at: str
    audit_reference: str
    decision_digest: str
    # Binding context. An allow decision is valid only for the exact exchange
    # context below; a digest alone is never an authorization token.
    source_institution_id: str = ""
    target_institution_id: str = ""
    requester_reference: str = ""
    patient_reference: str = ""
    record_reference: str = ""
    category: str = ""
    purpose: str = ""
    role: str = ""
    request_digest: str = ""

    def binding_fields(self) -> dict[str, Any]:
        return {
            "source_institution_id": self.source_institution_id,
            "target_institution_id": self.target_institution_id,
            "requester_reference": self.requester_reference,
            "patient_reference": self.patient_reference,
            "record_reference": self.record_reference,
            "category": self.category,
            "purpose": self.purpose,
            "role": self.role,
        }

    def authorizes(self, envelope: ExchangeEnvelope, *, at: str) -> None:
        """Fail closed unless this decision binds the exact envelope and time."""

        if not self.allowed:
            raise FederationDenied("disclosure decision is not an allow decision")
        if _parse_iso(self.expires_at) <= _parse_iso(at):
            raise FederationDenied("disclosure decision is expired")
        if self.source_institution_id != envelope.source_institution_id:
            raise FederationDenied("decision source institution mismatch")
        if self.target_institution_id != envelope.destination_institution_id:
            raise FederationDenied("decision target institution mismatch")
        if self.patient_reference != envelope.patient_reference:
            raise FederationDenied("decision patient reference mismatch")
        if self.record_reference != envelope.record_reference:
            raise FederationDenied("decision record reference mismatch")
        if not envelope.requester_reference or self.requester_reference != envelope.requester_reference:
            raise FederationDenied("decision requester mismatch")
        if self.category != envelope.category or envelope.category not in self.categories:
            raise FederationDenied("decision category mismatch")

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "schema": FEDERATION_SCHEMA,
            "allowed": self.allowed,
            "reason_code": self.reason_code,
            "categories": list(self.categories),
            "expires_at": self.expires_at,
            "audit_reference": self.audit_reference,
            "decision_digest": self.decision_digest,
            "request_digest": self.request_digest,
            **self.binding_fields(),
        }


@dataclass(frozen=True)
class ExchangeEnvelope:
    envelope_id: str
    idempotency_key: str
    correlation_id: str
    source_institution_id: str
    destination_institution_id: str
    message_type: str
    patient_reference: str
    record_reference: str
    category: str
    revision: int
    event_sequence: int
    expires_at: str
    decision_digest: str
    provenance_digest: str
    requester_reference: str = ""

    def __post_init__(self) -> None:
        if normalize_correlation_id(self.correlation_id, fallback="") != self.correlation_id:
            raise FederationValidationError("correlation_id is not a canonical log-safe identifier")
        for label, value in (
            ("envelope_id", self.envelope_id),
            ("idempotency_key", self.idempotency_key),
            ("correlation_id", self.correlation_id),
            ("source_institution_id", self.source_institution_id),
            ("destination_institution_id", self.destination_institution_id),
            ("patient_reference", self.patient_reference),
            ("record_reference", self.record_reference),
        ):
            _opaque(value, label)
        if self.requester_reference:
            _opaque(self.requester_reference, "requester_reference")
        _digest_value(self.decision_digest, "decision_digest")
        _digest_value(self.provenance_digest, "provenance_digest")
        if self.message_type not in {
            "identity_reference",
            "record_discovery",
            "referral",
            "lab_order",
            "lab_result",
            "clinical_document",
            "acknowledgement",
            "receipt",
            "reconciliation",
        }:
            raise FederationValidationError("unsupported exchange message type")
        if self.category not in DATA_CATEGORIES:
            raise FederationValidationError("unsupported exchange category")
        if self.revision < 1 or self.event_sequence < 1:
            raise FederationValidationError("exchange ordering metadata must be positive")
        _timestamp(self.expires_at, "expires_at")

    def digest(self) -> str:
        return _digest(
            {
                "envelope_id": self.envelope_id,
                "idempotency_key": self.idempotency_key,
                "source": self.source_institution_id,
                "destination": self.destination_institution_id,
                "message_type": self.message_type,
                "patient_reference": self.patient_reference,
                "record_reference": self.record_reference,
                "category": self.category,
                "revision": self.revision,
                "event_sequence": self.event_sequence,
                "requester_reference": self.requester_reference,
                "decision_digest": self.decision_digest,
                "provenance_digest": self.provenance_digest,
            }
        )

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "envelope_id": self.envelope_id,
            "correlation_id": self.correlation_id,
            "source_institution_id": self.source_institution_id,
            "destination_institution_id": self.destination_institution_id,
            "message_type": self.message_type,
            "patient_reference": self.patient_reference,
            "record_reference": self.record_reference,
            "category": self.category,
            "revision": self.revision,
            "event_sequence": self.event_sequence,
            "expires_at": self.expires_at,
            "requester_reference": self.requester_reference,
            "envelope_digest": self.digest(),
        }

    def to_snapshot_dict(self) -> dict[str, Any]:
        """Internal snapshot form: all authoritative envelope metadata."""

        return {
            "envelope_id": self.envelope_id,
            "idempotency_key": self.idempotency_key,
            "correlation_id": self.correlation_id,
            "source_institution_id": self.source_institution_id,
            "destination_institution_id": self.destination_institution_id,
            "message_type": self.message_type,
            "patient_reference": self.patient_reference,
            "record_reference": self.record_reference,
            "category": self.category,
            "revision": self.revision,
            "event_sequence": self.event_sequence,
            "expires_at": self.expires_at,
            "requester_reference": self.requester_reference,
            "decision_digest": self.decision_digest,
            "provenance_digest": self.provenance_digest,
            "envelope_digest": self.digest(),
        }

    @classmethod
    def from_snapshot_dict(cls, item: Mapping[str, Any]) -> ExchangeEnvelope:
        envelope = cls(
            envelope_id=str(item["envelope_id"]),
            idempotency_key=str(item["idempotency_key"]),
            correlation_id=str(item["correlation_id"]),
            source_institution_id=str(item["source_institution_id"]),
            destination_institution_id=str(item["destination_institution_id"]),
            message_type=str(item["message_type"]),
            patient_reference=str(item["patient_reference"]),
            record_reference=str(item["record_reference"]),
            category=str(item["category"]),
            revision=int(item["revision"]),
            event_sequence=int(item["event_sequence"]),
            expires_at=str(item["expires_at"]),
            decision_digest=str(item["decision_digest"]),
            provenance_digest=str(item["provenance_digest"]),
            requester_reference=str(item.get("requester_reference", "")),
        )
        if str(item["envelope_digest"]) != envelope.digest():
            raise FederationIntegrityError("envelope digest does not match its fields")
        return envelope

    def to_integration_event(
        self,
        *,
        tenant_id: str,
        actor_id: str,
        occurred_at: datetime,
    ) -> IntegrationEventEnvelope:
        """Reuse the canonical cross-repository envelope shape with digests only."""

        return IntegrationEventEnvelope(
            event_id=self.envelope_id,
            event_type=f"federated.{self.message_type}",
            schema_version=1,
            source_service=FEDERATION_SOURCE,
            tenant_id=_opaque(tenant_id, "tenant_id"),
            occurred_at=occurred_at,
            actor_id=_opaque(actor_id, "actor_id"),
            entity_id=self.record_reference,
            correlation_id=self.correlation_id,
            idempotency_key=self.idempotency_key,
            payload={
                "envelope_digest": self.digest(),
                "category": self.category,
                "decision_digest": self.decision_digest,
            },
        )


@dataclass
class ExchangeReceipt:
    envelope_id: str
    idempotency_key: str
    status: str
    attempts: int
    reason_code: str
    acknowledged: bool = False
    accepted: bool = False
    envelope_digest: str = ""
    next_retry_at: float | None = None
    updated_at: str = ""

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "envelope_id": self.envelope_id,
            "idempotency_key": self.idempotency_key,
            "status": self.status,
            "attempts": self.attempts,
            "reason_code": self.reason_code,
            "acknowledged": self.acknowledged,
            "accepted": self.accepted,
            "envelope_digest": self.envelope_digest,
            "next_retry_at": self.next_retry_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class ReferralRequest:
    referral_id: str
    source_facility_id: str
    destination_facility_id: str
    destination_directorate_id: str | None
    patient_reference: str
    purpose: str
    priority: str
    reason_code: str
    expires_at: str
    correlation_id: str

    def __post_init__(self) -> None:
        for label, value in (
            ("referral_id", self.referral_id),
            ("source_facility_id", self.source_facility_id),
            ("destination_facility_id", self.destination_facility_id),
            ("patient_reference", self.patient_reference),
            ("reason_code", self.reason_code),
            ("correlation_id", self.correlation_id),
        ):
            _opaque(value, label)
        if self.destination_directorate_id is not None:
            _opaque(self.destination_directorate_id, "destination_directorate_id")
        if self.priority not in {item.value for item in ReferralPriority}:
            raise FederationValidationError("unsupported referral priority")
        _timestamp(self.expires_at, "expires_at")


@dataclass
class ReferralState:
    request: ReferralRequest
    status: str
    acknowledged_by: str | None = None
    decision_by: str | None = None
    envelope_id: str | None = None
    reason_code: str = "none"

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "referral_id": self.request.referral_id,
            "status": self.status,
            "source_facility_id": self.request.source_facility_id,
            "destination_facility_id": self.request.destination_facility_id,
            "destination_directorate_id": self.request.destination_directorate_id,
            "patient_reference": self.request.patient_reference,
            "priority": self.request.priority,
            "expires_at": self.request.expires_at,
            "correlation_id": self.request.correlation_id,
            "envelope_id": self.envelope_id,
            "acknowledged_by": self.acknowledged_by,
            "decision_by": self.decision_by,
            "reason_code": self.reason_code,
            "canonical_referral_status": ReferralStatus.SENT.value
            if self.status in {REFERRAL_ROUTED, REFERRAL_TRANSMITTED, REFERRAL_ACKNOWLEDGED}
            else ReferralStatus.DRAFT.value,
        }


class FederatedInstitutionRegistry:
    """Synthetic registry with explicit lifecycle and trust relations."""

    def __init__(self, policy: FederationPolicy | None = None) -> None:
        self.policy = policy or FederationPolicy()
        self._institutions: dict[str, InstitutionRecord] = {}
        self._trust: dict[tuple[str, str], TrustRelation] = {}

    def register(
        self,
        *,
        kind: str,
        endpoint_reference: str,
        profiles: Sequence[str],
        capabilities: Sequence[str],
        status: str = INSTITUTION_REGISTERED,
        directorate_id: str | None = None,
        facility_type: str | None = None,
        authorized_until: str | None = None,
        institution_id: str | None = None,
    ) -> InstitutionRecord:
        if len(self._institutions) >= self.policy.max_institutions:
            raise FederationValidationError("institution registry depth cap reached")
        seed = f"{kind}:{endpoint_reference}:{directorate_id or ''}:{facility_type or ''}"
        stable_id = institution_id or f"{kind[:3].upper()}-{_digest(seed)[:20]}"
        record = InstitutionRecord(
            institution_id=stable_id,
            kind=kind,
            status=status,
            endpoint_reference=endpoint_reference,
            profiles=tuple(profiles),
            capabilities=tuple(capabilities),
            directorate_id=directorate_id,
            facility_type=facility_type,
            authorized_until=authorized_until,
        )
        if record.institution_id in self._institutions:
            existing = self._institutions[record.institution_id]
            if existing.provenance_digest != record.provenance_digest:
                raise FederationConflict("institution identifier reused with different metadata")
            return existing
        self._institutions[record.institution_id] = record
        _metric(outcome="completed")
        return record

    def set_status(
        self,
        institution_id: str,
        status: str,
        *,
        actor_reference: str,
        reason_code_value: str,
        authorized_until: str | None = None,
    ) -> InstitutionRecord:
        _opaque(actor_reference, "actor_reference")
        _opaque(reason_code_value, "reason_code_value")
        current = self._institutions.get(institution_id)
        if current is None:
            raise FederationDenied("unknown institution")
        if status not in _INSTITUTION_STATES:
            raise FederationValidationError("unsupported institution lifecycle state")
        if status != current.status and status not in _INSTITUTION_TRANSITIONS[current.status]:
            raise FederationDenied("institution lifecycle transition is not allowed")
        updated = replace(
            current,
            status=status,
            authorized_until=authorized_until or current.authorized_until,
            provenance_digest="",
        )
        self._institutions[institution_id] = updated
        _metric(outcome="completed")
        return updated

    def add_trust(
        self,
        source_institution_id: str,
        target_institution_id: str,
        *,
        scope: Sequence[str],
        expires_at: str,
        actor_reference: str,
        at: str | None = None,
    ) -> TrustRelation:
        _opaque(actor_reference, "actor_reference")
        if len(self._trust) >= self.policy.max_trust_relations:
            raise FederationValidationError("trust relation depth cap reached")
        for identifier in (source_institution_id, target_institution_id):
            institution = self._institutions.get(identifier)
            if institution is None or institution.status != INSTITUTION_AUTHORIZED:
                raise FederationDenied("trust requires authorized institutions")
        relation = TrustRelation(
            source_institution_id=source_institution_id,
            target_institution_id=target_institution_id,
            scope=tuple(scope),
            expires_at=expires_at,
        )
        if _parse_iso(relation.expires_at) <= (_parse_iso(at) if at else _now()):
            raise FederationValidationError("trust expiration is not in the future")
        key = (source_institution_id, target_institution_id)
        existing = self._trust.get(key)
        if existing is not None and existing.digest() != relation.digest():
            raise FederationConflict("trust relation was already defined with different scope")
        self._trust[key] = relation
        _metric(outcome="completed")
        return relation

    def revoke_trust(
        self, source_institution_id: str, target_institution_id: str, *, actor_reference: str
    ) -> None:
        _opaque(actor_reference, "actor_reference")
        key = (source_institution_id, target_institution_id)
        relation = self._trust.get(key)
        if relation is None:
            raise FederationDenied("no explicit trust relation to revoke")
        self._trust[key] = replace(relation, status=TRUST_REVOKED)
        _metric(outcome="completed")

    def assert_authorized(self, institution_id: str, *, at: str | None = None) -> InstitutionRecord:
        institution = self._institutions.get(institution_id)
        if institution is None:
            raise FederationDenied("unknown institution")
        if institution.status not in _ACTIVE_INSTITUTION_STATES:
            raise FederationDenied("institution is not authorized")
        if institution.authorized_until is not None:
            moment = _parse_iso(at) if at else _now()
            if _parse_iso(institution.authorized_until) <= moment:
                raise FederationDenied("institution authorization is expired")
        return institution

    def assert_trust(
        self, source_institution_id: str, target_institution_id: str, *, category: str, at: str
    ) -> TrustRelation:
        self.assert_authorized(source_institution_id, at=at)
        self.assert_authorized(target_institution_id, at=at)
        relation = self._trust.get((source_institution_id, target_institution_id))
        if relation is None or relation.status != TRUST_ACTIVE:
            raise FederationDenied("no active explicit trust relation")
        if category not in relation.scope:
            raise FederationDenied("trust scope does not include the requested category")
        if _parse_iso(relation.expires_at) <= _parse_iso(at):
            raise FederationDenied("trust relation is expired")
        return relation

    def discover(self, institution_id: str, *, at: str | None = None) -> dict[str, Any]:
        institution = self.assert_authorized(institution_id, at=at)
        return institution.to_public_dict()

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": FEDERATION_SCHEMA,
            "institutions": [item.to_snapshot_dict() for item in self._institutions.values()],
            "trust": [
                {
                    "source_institution_id": relation.source_institution_id,
                    "target_institution_id": relation.target_institution_id,
                    "scope": list(relation.scope),
                    "expires_at": relation.expires_at,
                    "status": relation.status,
                    "digest": relation.digest(),
                }
                for relation in self._trust.values()
            ],
        }

    def restore(self, snapshot: Mapping[str, Any]) -> None:
        if snapshot.get("schema") != FEDERATION_SCHEMA:
            raise FederationIntegrityError("unsupported federation snapshot schema")
        raw_institutions = snapshot.get("institutions", [])
        raw_trust = snapshot.get("trust", [])
        if not isinstance(raw_institutions, Sequence) or not isinstance(raw_trust, Sequence):
            raise FederationIntegrityError("snapshot sections must be sequences")
        if len(raw_institutions) > self.policy.max_institutions or len(raw_trust) > self.policy.max_trust_relations:
            raise FederationIntegrityError("snapshot exceeds configured bounds")
        institutions: dict[str, InstitutionRecord] = {}
        for item in raw_institutions:
            if not isinstance(item, Mapping):
                raise FederationIntegrityError("institution entry is not a mapping")
            record = InstitutionRecord(
                institution_id=str(item["institution_id"]),
                kind=str(item["kind"]),
                status=str(item["status"]),
                endpoint_reference=str(item["endpoint_reference"]),
                profiles=tuple(item.get("profiles", ())),
                capabilities=tuple(item.get("capabilities", ())),
                directorate_id=item.get("directorate_id"),
                facility_type=item.get("facility_type"),
                authorized_until=item.get("authorized_until"),
                provenance_digest=str(item["provenance_digest"]),
            )
            if record.institution_id in institutions:
                raise FederationIntegrityError("duplicate institution in snapshot")
            if record.provenance_digest != record._compute_digest():
                raise FederationIntegrityError("institution provenance digest is invalid")
            institutions[record.institution_id] = record
        trust: dict[tuple[str, str], TrustRelation] = {}
        for item in raw_trust:
            if not isinstance(item, Mapping):
                raise FederationIntegrityError("trust entry is not a mapping")
            relation = TrustRelation(
                source_institution_id=str(item["source_institution_id"]),
                target_institution_id=str(item["target_institution_id"]),
                scope=tuple(item.get("scope", ())),
                expires_at=str(item["expires_at"]),
                status=str(item.get("status", TRUST_ACTIVE)),
            )
            if relation.source_institution_id not in institutions or relation.target_institution_id not in institutions:
                raise FederationIntegrityError("trust relation references unknown institution")
            key = (relation.source_institution_id, relation.target_institution_id)
            if key in trust:
                raise FederationIntegrityError("duplicate trust relation in snapshot")
            if str(item.get("digest", "")) != relation.digest():
                raise FederationIntegrityError("trust relation digest is invalid")
            trust[key] = relation
        self._institutions = institutions
        self._trust = trust


class FederatedOwnershipLedger:
    """Append-only custody metadata; never a clinical record store."""

    def __init__(self, registry: FederatedInstitutionRegistry, policy: FederationPolicy | None = None) -> None:
        self.registry = registry
        self.policy = policy or FederationPolicy()
        self._records: dict[str, FederatedRecord] = {}
        self._lineage: dict[str, tuple[str, ...]] = {}

    def register(self, record: FederatedRecord) -> FederatedRecord:
        self.registry.assert_authorized(record.institution_id)
        existing = self._records.get(record.record_id)
        if existing is not None:
            if existing.integrity_digest != record.integrity_digest:
                raise FederationConflict("record identifier reused with different metadata")
            return existing
        if len(self._records) >= self.policy.max_records:
            raise FederationValidationError("record ledger depth cap reached")
        self._records[record.record_id] = record
        self._lineage[record.record_id] = (record.record_id,)
        _metric(outcome="completed")
        return record

    def assert_owned(self, record_id: str, institution_id: str) -> FederatedRecord:
        record = self._records.get(record_id)
        if record is None:
            raise FederationDenied("unknown federated record")
        if record.institution_id != institution_id:
            raise FederationDenied("record custody belongs to another institution")
        return record

    def supersede(self, record_id: str, replacement: FederatedRecord) -> FederatedRecord:
        original = self._records.get(record_id)
        if original is None:
            raise FederationDenied("unknown federated record")
        if replacement.record_id == record_id:
            raise FederationConflict("correction must use a new opaque record identifier")
        if replacement.record_id in self._records:
            raise FederationConflict("replacement record identifier is already registered")
        if replacement.institution_id != original.institution_id:
            raise FederationDenied("cross-institution correction is denied")
        if replacement.category != original.category or replacement.patient_reference != original.patient_reference:
            raise FederationDenied("correction changed category or patient reference")
        if replacement.revision <= original.revision or replacement.event_sequence <= original.event_sequence:
            raise FederationConflict("correction must advance revision and event ordering")
        registered = self.register(replacement)
        self._lineage[registered.record_id] = (*self._lineage[record_id], registered.record_id)
        return registered

    def detect_conflict(self, record: FederatedRecord) -> FederatedRecord:
        existing = self._records.get(record.record_id)
        if existing is None:
            return record
        if record.event_sequence < existing.event_sequence:
            raise FederationConflict("stale event cannot overwrite a newer revision")
        if existing.integrity_digest != record.integrity_digest:
            raise FederationConflict("conflicting clinical revision requires reconciliation")
        return existing

    def lineage(self, record_id: str) -> tuple[str, ...]:
        if record_id not in self._lineage:
            raise FederationDenied("unknown federated record")
        return self._lineage[record_id]

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": FEDERATION_SCHEMA,
            "records": [record.to_public_dict() for record in self._records.values()],
            "lineage": {key: list(value) for key, value in self._lineage.items()},
        }

    def restore(self, snapshot: Mapping[str, Any]) -> None:
        if snapshot.get("schema") != FEDERATION_SCHEMA:
            raise FederationIntegrityError("unsupported ownership snapshot schema")
        raw_records = snapshot.get("records", [])
        raw_lineage = snapshot.get("lineage", {})
        if not isinstance(raw_records, Sequence) or not isinstance(raw_lineage, Mapping):
            raise FederationIntegrityError("ownership snapshot sections are malformed")
        if len(raw_records) > self.policy.max_records:
            raise FederationIntegrityError("ownership snapshot exceeds record bounds")
        ledger = FederatedOwnershipLedger(self.registry, self.policy)
        for item in raw_records:
            if not isinstance(item, Mapping):
                raise FederationIntegrityError("record entry is not a mapping")
            record = FederatedRecord(
                record_id=str(item["record_id"]),
                institution_id=str(item["institution_id"]),
                patient_reference=str(item["patient_reference"]),
                category=str(item["category"]),
                revision=int(item["revision"]),
                event_sequence=int(item["event_sequence"]),
                recorded_at=str(item["recorded_at"]),
                classification=str(item["classification"]),
                disclosure_policy=str(item["disclosure_policy"]),
                payload_digest=str(item["payload_digest"]),
                integrity_digest=str(item["integrity_digest"]),
            )
            if record.integrity_digest != record._compute_digest():
                raise FederationIntegrityError("record integrity digest is invalid")
            ledger.register(record)
        for key, value in raw_lineage.items():
            chain = tuple(str(item) for item in value) if isinstance(value, Sequence) else ()
            if not chain or chain[0] != str(key) or any(item not in ledger._records for item in chain):
                raise FederationIntegrityError("ownership lineage is invalid")
            ledger._lineage[str(key)] = chain
        if set(ledger._lineage) != set(ledger._records):
            raise FederationIntegrityError("ownership lineage coverage is incomplete")
        self._records = ledger._records
        self._lineage = ledger._lineage


class FederatedPolicyEngine:
    """Deny-by-default disclosure evaluator over federated metadata."""

    def __init__(
        self,
        registry: FederatedInstitutionRegistry,
        ledger: FederatedOwnershipLedger,
        federation_policy: FederationPolicy | None = None,
    ) -> None:
        self.registry = registry
        self.ledger = ledger
        self.policy = federation_policy or FederationPolicy()
        self._decisions: dict[str, DisclosureDecision] = {}

    def evaluate(self, request: DisclosureRequest, *, target_institution_id: str) -> DisclosureDecision:
        deny = lambda code: DisclosureDecision(  # noqa: E731 - bounded local factory
            allowed=False,
            reason_code=code,
            categories=(),
            expires_at=request.at,
            audit_reference=request.audit_reference,
            decision_digest="",
        )
        try:
            self.registry.assert_authorized(request.requesting_institution_id, at=request.at)
            self.registry.assert_trust(
                request.requesting_institution_id,
                target_institution_id,
                category=request.category,
                at=request.at,
            )
            if request.role not in PROFESSIONAL_ROLES:
                return deny("authorization_denied")
            if request.purpose not in APPROVED_PURPOSES:
                return deny("validation_failed")
            if not request.relationship_reference:
                return deny("authorization_denied")
            if request.category == "public_health_aggregate":
                return deny("authorization_denied")
            if not request.minimum_necessary:
                return deny("authorization_denied")
            if not request.patient_reference or not request.record_reference:
                return deny("validation_failed")
            grant = request.emergency_grant
            if grant is not None:
                try:
                    approver = self.registry.discover(grant.approver_reference, at=request.at)
                except FederationDenied:
                    return deny("authorization_denied")
                if approver.get("kind") not in {KIND_NATIONAL, KIND_DIRECTORATE}:
                    return deny("authorization_denied")
                if _parse_iso(grant.expires_at) <= _parse_iso(request.at):
                    return deny("authorization_denied")
                if grant.reason_code not in EMERGENCY_REASONS:
                    return deny("authorization_denied")
            if request.consent_status != CONSENT_ACTIVE:
                if grant is None:
                    return deny("authorization_denied")
                if request.category not in grant.categories:
                    return deny("authorization_denied")
            now = _parse_iso(request.at)
            expires_at = (now + timedelta(seconds=self.policy.decision_window_seconds)).isoformat()
            if grant is not None:
                expires_at = min(expires_at, grant.expires_at)
            decision = DisclosureDecision(
                allowed=True,
                reason_code="none",
                categories=(request.category,),
                expires_at=expires_at,
                audit_reference=request.audit_reference,
                decision_digest="",
                source_institution_id=request.requesting_institution_id,
                target_institution_id=target_institution_id,
                requester_reference=request.requester_reference,
                patient_reference=request.patient_reference,
                record_reference=request.record_reference,
                category=request.category,
                purpose=request.purpose,
                role=request.role,
                request_digest=_digest(request.__dict__),
            )
            object.__setattr__(
                decision,
                "decision_digest",
                _digest(
                    {
                        "request": decision.request_digest,
                        "target_institution_id": target_institution_id,
                        "categories": decision.categories,
                        "expires_at": decision.expires_at,
                        "binding": _digest(decision.binding_fields()),
                    }
                ),
            )
            self._decisions[decision.decision_digest] = decision
            _metric(outcome="completed")
            return decision
        except FederationDenied as exc:
            code = _safe_reason(str(exc))
            _metric(outcome="rejected", reason=str(exc))
            return deny(code)

    def assert_allowed(self, request: DisclosureRequest, *, target_institution_id: str) -> DisclosureDecision:
        decision = self.evaluate(request, target_institution_id=target_institution_id)
        if not decision.allowed:
            raise FederationDenied(f"disclosure denied: {decision.reason_code}")
        return decision

    def decision(self, digest_value: str) -> DisclosureDecision:
        decision = self._decisions.get(digest_value)
        if decision is None:
            raise FederationDenied("unknown disclosure decision")
        return decision

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": FEDERATION_SCHEMA,
            "decisions": [decision.to_public_dict() for decision in self._decisions.values()],
        }

    def restore(self, snapshot: Mapping[str, Any]) -> None:
        if snapshot.get("schema") != FEDERATION_SCHEMA:
            raise FederationIntegrityError("unsupported disclosure snapshot schema")
        raw_decisions = snapshot.get("decisions", [])
        if not isinstance(raw_decisions, Sequence):
            raise FederationIntegrityError("disclosure decisions must be a sequence")
        restored: dict[str, DisclosureDecision] = {}
        for item in raw_decisions:
            if not isinstance(item, Mapping):
                raise FederationIntegrityError("decision entry is not a mapping")
            decision = DisclosureDecision(
                allowed=bool(item["allowed"]),
                reason_code=str(item["reason_code"]),
                categories=tuple(item.get("categories", ())),
                expires_at=str(item["expires_at"]),
                audit_reference=str(item["audit_reference"]),
                decision_digest=str(item["decision_digest"]),
                source_institution_id=str(item.get("source_institution_id", "")),
                target_institution_id=str(item.get("target_institution_id", "")),
                requester_reference=str(item.get("requester_reference", "")),
                patient_reference=str(item.get("patient_reference", "")),
                record_reference=str(item.get("record_reference", "")),
                category=str(item.get("category", "")),
                purpose=str(item.get("purpose", "")),
                role=str(item.get("role", "")),
                request_digest=str(item.get("request_digest", "")),
            )
            if not decision.allowed or not set(decision.categories) <= DATA_CATEGORIES:
                raise FederationIntegrityError("invalid restored disclosure decision")
            if not decision.source_institution_id or not decision.target_institution_id:
                raise FederationIntegrityError("restored disclosure decision is unbound")
            if not decision.patient_reference or not decision.record_reference:
                raise FederationIntegrityError("restored disclosure decision is unbound")
            _digest_value(decision.request_digest, "request_digest")
            # The digest is recomputed from fields, never trusted from the snapshot.
            _timestamp(decision.expires_at, "expires_at")
            expected = _digest(
                {
                    "request": decision.request_digest,
                    "target_institution_id": decision.target_institution_id,
                    "categories": decision.categories,
                    "expires_at": decision.expires_at,
                    "binding": _digest(decision.binding_fields()),
                }
            )
            if expected != decision.decision_digest:
                raise FederationIntegrityError("disclosure decision digest does not match its fields")
            if decision.decision_digest in restored:
                raise FederationIntegrityError("duplicate disclosure decision")
            restored[decision.decision_digest] = decision
        self._decisions = restored


Transport = Callable[[dict[str, Any]], dict[str, Any]]


def _default_transport(envelope: dict[str, Any]) -> dict[str, Any]:
    _reject_sensitive(envelope)
    return {"status": "delivered", "envelope_digest": envelope["envelope_digest"]}


class FederatedExchangeBroker:
    """Bounded in-process exchange with dedupe, retry, ack and reconciliation."""

    def __init__(
        self,
        registry: FederatedInstitutionRegistry,
        policy_engine: FederatedPolicyEngine,
        transport: Transport | None = None,
        federation_policy: FederationPolicy | None = None,
    ) -> None:
        self.registry = registry
        self.policy_engine = policy_engine
        self.transport = transport or _default_transport
        self.policy = federation_policy or FederationPolicy()
        self._receipts: dict[str, ExchangeReceipt] = {}
        self._dedupe: dict[str, str] = {}
        self._by_envelope: dict[str, ExchangeEnvelope] = {}
        self._audit: list[dict[str, Any]] = []

    def _authorize_envelope(self, envelope: ExchangeEnvelope, *, at: str) -> None:
        """Revalidate the full authorization context before any delivery attempt."""

        self.registry.assert_authorized(envelope.source_institution_id, at=at)
        self.registry.assert_authorized(envelope.destination_institution_id, at=at)
        self.registry.assert_trust(
            envelope.source_institution_id,
            envelope.destination_institution_id,
            category=envelope.category,
            at=at,
        )
        self.policy_engine.decision(envelope.decision_digest).authorizes(envelope, at=at)

    def _reserve_audit(self) -> None:
        if len(self._audit) >= self.policy.max_audit_events:
            raise FederationValidationError("audit depth cap reached")

    def _audit_event(self, *, envelope_id: str, state: str, reason: str, actor_reference: str) -> str:
        _opaque(actor_reference, "actor_reference")
        if len(self._audit) >= self.policy.max_audit_events:
            raise FederationValidationError("audit depth cap reached")
        previous = self._audit[-1]["digest"] if self._audit else "0" * 64
        event = {
            "envelope_id": envelope_id,
            "state": state,
            "reason": _safe_reason(reason),
            "actor_reference": actor_reference,
            "previous_digest": previous,
        }
        digest = _digest(event)
        self._audit.append({**event, "digest": digest})
        return digest

    def send(self, envelope: ExchangeEnvelope, *, at: str, actor_reference: str) -> ExchangeReceipt:
        _timestamp(at, "at")
        existing_key = self._dedupe.get(envelope.idempotency_key)
        if existing_key is not None:
            receipt = self._receipts[existing_key]
            if receipt.envelope_digest != envelope.digest():
                raise FederationConflict("idempotency key reused with different envelope content")
            self._audit_event(
                envelope_id=envelope.envelope_id,
                state=receipt.status,
                reason="duplicate_command",
                actor_reference=actor_reference,
            )
            _metric(outcome="completed", reason="duplicate_command")
            return receipt
        if len(self._receipts) >= self.policy.max_envelopes:
            raise FederationValidationError("exchange envelope depth cap reached")
        if _parse_iso(envelope.expires_at) <= _parse_iso(at):
            raise FederationDenied("exchange envelope is expired")
        self._authorize_envelope(envelope, at=at)
        self._reserve_audit()
        receipt = ExchangeReceipt(
            envelope_id=envelope.envelope_id,
            idempotency_key=envelope.idempotency_key,
            status=EXCHANGE_CREATED,
            attempts=0,
            reason_code="none",
            envelope_digest=envelope.digest(),
            updated_at=at,
        )
        self._receipts[envelope.envelope_id] = receipt
        self._dedupe[envelope.idempotency_key] = envelope.envelope_id
        self._by_envelope[envelope.envelope_id] = envelope
        return self._attempt_send(receipt, at=at, actor_reference=actor_reference)

    def _attempt_send(self, receipt: ExchangeReceipt, *, at: str, actor_reference: str) -> ExchangeReceipt:
        envelope = self._by_envelope[receipt.envelope_id]
        # Every attempt revalidates trust, institution status and decision
        # binding; revocation between retries must never result in delivery.
        try:
            self._authorize_envelope(envelope, at=at)
        except (FederationDenied, FederationValidationError) as exc:
            receipt.status = EXCHANGE_DEAD_LETTER
            receipt.reason_code = _safe_reason(str(exc))
            receipt.next_retry_at = None
            receipt.updated_at = at
            self._reserve_audit()
            self._audit_event(
                envelope_id=envelope.envelope_id,
                state=receipt.status,
                reason=str(exc),
                actor_reference=actor_reference,
            )
            _metric(outcome="rejected", reason=str(exc))
            return receipt
        self._reserve_audit()
        receipt.attempts += 1
        receipt.status = EXCHANGE_SENT
        receipt.updated_at = at
        try:
            response = self.transport(envelope.to_public_dict())
            _reject_sensitive(response)
            if response.get("status") != "delivered" or response.get("envelope_digest") != envelope.digest():
                raise FederationError("destination returned an invalid delivery response")
            receipt.status = EXCHANGE_DELIVERED
            receipt.next_retry_at = None
            receipt.reason_code = "none"
            self._audit_event(
                envelope_id=envelope.envelope_id,
                state=receipt.status,
                reason="none",
                actor_reference=actor_reference,
            )
            _metric(outcome="completed")
        except Exception as exc:  # bounded synthetic transport failure
            receipt.reason_code = _safe_reason(str(exc))
            if receipt.attempts >= self.policy.max_retries:
                receipt.status = EXCHANGE_DEAD_LETTER
                receipt.next_retry_at = None
            else:
                receipt.status = EXCHANGE_RETRY_SCHEDULED
                delay = self.policy.retry_base_seconds * (2 ** (receipt.attempts - 1))
                receipt.next_retry_at = _parse_iso(at).timestamp() + delay
            self._audit_event(
                envelope_id=envelope.envelope_id,
                state=receipt.status,
                reason=str(exc),
                actor_reference=actor_reference,
            )
            _metric(outcome="rejected", reason=str(exc))
        return receipt

    def retry_due(self, *, at: str, actor_reference: str) -> int:
        moment = _parse_iso(at).timestamp()
        due = [
            receipt
            for receipt in self._receipts.values()
            if receipt.status == EXCHANGE_RETRY_SCHEDULED
            and receipt.next_retry_at is not None
            and receipt.next_retry_at <= moment
        ]
        for receipt in due:
            self._attempt_send(receipt, at=at, actor_reference=actor_reference)
        return len(due)

    def acknowledge(
        self, envelope_id: str, *, institution_id: str, at: str, actor_reference: str
    ) -> ExchangeReceipt:
        receipt = self._receipt(env_or_id=envelope_id)
        envelope = self._by_envelope[envelope_id]
        if institution_id != envelope.destination_institution_id:
            raise FederationDenied("only the destination institution can acknowledge")
        self.registry.assert_authorized(institution_id, at=at)
        if receipt.status != EXCHANGE_DELIVERED:
            raise FederationDenied("only a delivered envelope can be acknowledged")
        receipt.status = EXCHANGE_ACKNOWLEDGED
        receipt.acknowledged = True
        receipt.updated_at = at
        self._audit_event(
            envelope_id=envelope_id,
            state=receipt.status,
            reason="none",
            actor_reference=actor_reference,
        )
        return receipt

    def accept(
        self, envelope_id: str, *, institution_id: str, at: str, actor_reference: str, accepted: bool
    ) -> ExchangeReceipt:
        receipt = self._acknowledged_receipt(envelope_id, institution_id)
        receipt.accepted = accepted
        receipt.status = EXCHANGE_DELIVERED if accepted else EXCHANGE_DEAD_LETTER
        receipt.reason_code = "none" if accepted else "referral_rejected"
        receipt.updated_at = at
        self._audit_event(
            envelope_id=envelope_id,
            state=receipt.status,
            reason=receipt.reason_code,
            actor_reference=actor_reference,
        )
        return receipt

    def receive(
        self,
        envelope: ExchangeEnvelope,
        *,
        at: str,
        actor_reference: str,
        ownership: FederatedOwnershipLedger,
    ) -> FederatedRecord:
        self._authorize_envelope(envelope, at=at)
        candidate = FederatedRecord(
            record_id=envelope.record_reference,
            institution_id=envelope.source_institution_id,
            patient_reference=envelope.patient_reference,
            category=envelope.category,
            revision=envelope.revision,
            event_sequence=envelope.event_sequence,
            recorded_at=at,
            classification="synthetic_federated",
            disclosure_policy="minimum_necessary",
            payload_digest=envelope.provenance_digest,
        )
        existing = self._receipts.get(envelope.envelope_id)
        if existing is not None and existing.envelope_digest != envelope.digest():
            raise FederationConflict("envelope identifier reused with different content")
        try:
            known = ownership.detect_conflict(candidate)
        except FederationConflict:
            self._record_inbound_conflict(envelope, at=at, actor_reference=actor_reference)
            raise
        ownership.register(known)
        self._audit_event(
            envelope_id=envelope.envelope_id,
            state="received",
            reason="none",
            actor_reference=actor_reference,
        )
        return known

    def _record_inbound_conflict(
        self, envelope: ExchangeEnvelope, *, at: str, actor_reference: str
    ) -> ExchangeReceipt:
        receipt = self._receipts.get(envelope.envelope_id)
        if receipt is None:
            receipt = ExchangeReceipt(
                envelope_id=envelope.envelope_id,
                idempotency_key=envelope.idempotency_key,
                status=EXCHANGE_CONFLICT,
                attempts=0,
                reason_code="clinical_version_conflict",
                envelope_digest=envelope.digest(),
                updated_at=at,
            )
            self._receipts[envelope.envelope_id] = receipt
            self._dedupe[envelope.idempotency_key] = envelope.envelope_id
        else:
            receipt.status = EXCHANGE_CONFLICT
            receipt.reason_code = "clinical_version_conflict"
            receipt.updated_at = at
        self._by_envelope[envelope.envelope_id] = envelope
        self._reserve_audit()
        self._audit_event(
            envelope_id=envelope.envelope_id,
            state=receipt.status,
            reason=receipt.reason_code,
            actor_reference=actor_reference,
        )
        _metric(outcome="rejected", reason=receipt.reason_code)
        return receipt

    def reconcile(
        self,
        envelope_id: str,
        *,
        reviewer_reference: str,
        at: str,
        resolution_digest: str,
    ) -> ExchangeReceipt:
        _opaque(reviewer_reference, "reviewer_reference")
        _digest_value(resolution_digest, "resolution_digest")
        receipt = self._receipt(env_or_id=envelope_id)
        if receipt.status != EXCHANGE_CONFLICT:
            raise FederationDenied("only a conflicting envelope can be reconciled")
        receipt.status = EXCHANGE_DELIVERED
        receipt.reason_code = "none"
        receipt.updated_at = at
        self._audit_event(
            envelope_id=envelope_id,
            state=receipt.status,
            reason="reconciled",
            actor_reference=reviewer_reference,
        )
        return receipt

    def mark_conflict(self, envelope_id: str, *, actor_reference: str, at: str) -> ExchangeReceipt:
        receipt = self._receipt(env_or_id=envelope_id)
        receipt.status = EXCHANGE_CONFLICT
        receipt.reason_code = "clinical_version_conflict"
        receipt.updated_at = at
        self._audit_event(
            envelope_id=envelope_id,
            state=receipt.status,
            reason=receipt.reason_code,
            actor_reference=actor_reference,
        )
        _metric(outcome="rejected", reason=receipt.reason_code)
        return receipt

    def _receipt(self, *, env_or_id: str) -> ExchangeReceipt:
        receipt = self._receipts.get(env_or_id)
        if receipt is None:
            raise FederationDenied("unknown exchange envelope")
        return receipt

    def _acknowledged_receipt(self, envelope_id: str, institution_id: str) -> ExchangeReceipt:
        receipt = self._receipt(env_or_id=envelope_id)
        envelope = self._by_envelope[envelope_id]
        if institution_id != envelope.destination_institution_id:
            raise FederationDenied("only the destination institution can decide")
        if not receipt.acknowledged:
            raise FederationDenied("referral must be acknowledged before acceptance")
        return receipt

    def summary(self) -> dict[str, Any]:
        states = Counter(receipt.status for receipt in self._receipts.values())
        return {
            "total": len(self._receipts),
            "states": dict(sorted(states.items())),
            "acknowledged": sum(1 for receipt in self._receipts.values() if receipt.acknowledged),
            "accepted": sum(1 for receipt in self._receipts.values() if receipt.accepted),
            "audit_events": len(self._audit),
        }

    def audit_chain(self) -> dict[str, Any]:
        previous = "0" * 64
        for index, event in enumerate(self._audit, start=1):
            if event.get("previous_digest") != previous:
                return {"status": "INVALID", "sequence": index, "reason": "chain_link_mismatch"}
            expected = _digest({key: value for key, value in event.items() if key != "digest"})
            if event["digest"] != expected:
                return {"status": "INVALID", "sequence": index, "reason": "digest_mismatch"}
            previous = event["digest"]
        return {"status": "VALID", "sequence": len(self._audit), "tail_digest": previous}

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": FEDERATION_SCHEMA,
            "receipts": {key: receipt.to_public_dict() for key, receipt in self._receipts.items()},
            "envelopes": {
                key: envelope.to_snapshot_dict() for key, envelope in self._by_envelope.items()
            },
            "dedupe": dict(self._dedupe),
            "audit": list(self._audit),
        }

    def restore(self, snapshot: Mapping[str, Any]) -> None:
        if snapshot.get("schema") != FEDERATION_SCHEMA:
            raise FederationIntegrityError("unsupported exchange snapshot schema")
        raw_receipts = snapshot.get("receipts", {})
        raw_envelopes = snapshot.get("envelopes", {})
        raw_dedupe = snapshot.get("dedupe", {})
        raw_audit = snapshot.get("audit", [])
        if (
            not isinstance(raw_receipts, Mapping)
            or not isinstance(raw_envelopes, Mapping)
            or not isinstance(raw_dedupe, Mapping)
        ):
            raise FederationIntegrityError("exchange snapshot sections are malformed")
        if len(raw_receipts) > self.policy.max_envelopes or len(raw_audit) > self.policy.max_audit_events:
            raise FederationIntegrityError("exchange snapshot exceeds configured bounds")
        receipts: dict[str, ExchangeReceipt] = {}
        for key, item in raw_receipts.items():
            if not isinstance(item, Mapping) or key != item.get("envelope_id"):
                raise FederationIntegrityError("receipt key does not match its envelope")
            receipt = ExchangeReceipt(
                envelope_id=str(item["envelope_id"]),
                idempotency_key=str(item["idempotency_key"]),
                status=str(item["status"]),
                attempts=int(item["attempts"]),
                reason_code=str(item["reason_code"]),
                acknowledged=bool(item.get("acknowledged", False)),
                accepted=bool(item.get("accepted", False)),
                envelope_digest=str(item["envelope_digest"]),
                next_retry_at=item.get("next_retry_at"),
                updated_at=str(item["updated_at"]),
            )
            if receipt.attempts < 0 or receipt.attempts > self.policy.max_retries:
                raise FederationIntegrityError("restored receipt attempt count is invalid")
            receipts[receipt.envelope_id] = receipt
        envelopes: dict[str, ExchangeEnvelope] = {}
        for key, item in raw_envelopes.items():
            if not isinstance(item, Mapping) or key != item.get("envelope_id"):
                raise FederationIntegrityError("envelope key does not match its identifier")
            envelope = ExchangeEnvelope.from_snapshot_dict(item)
            envelopes[envelope.envelope_id] = envelope
        for key, receipt in receipts.items():
            envelope = envelopes.get(key)
            if envelope is None or envelope.digest() != receipt.envelope_digest:
                raise FederationIntegrityError("receipt does not match its restored envelope")
        for dedupe_key, envelope_id in raw_dedupe.items():
            envelope = envelopes.get(str(envelope_id))
            if envelope is None or envelope.idempotency_key != dedupe_key:
                raise FederationIntegrityError("dedupe marker does not match its restored envelope")
        if not isinstance(raw_audit, Sequence):
            raise FederationIntegrityError("audit section must be a sequence")
        broker = FederatedExchangeBroker(
            self.registry, self.policy_engine, self.transport, self.policy
        )
        previous = "0" * 64
        for event in raw_audit:
            if not isinstance(event, Mapping):
                raise FederationIntegrityError("audit entry is not a mapping")
            if str(event.get("previous_digest", "")) != previous:
                raise FederationIntegrityError("audit chain link is invalid")
            expected = _digest({key: value for key, value in event.items() if key != "digest"})
            if str(event.get("digest", "")) != expected:
                raise FederationIntegrityError("audit digest is invalid")
            broker._audit.append(dict(event))
            previous = str(event["digest"])
        self._receipts = receipts
        self._by_envelope = envelopes
        self._dedupe = dict(raw_dedupe)
        self._audit = broker._audit


class FederatedReferralRouter:
    """Referral lifecycle with explicit acknowledgement and acceptance."""

    def __init__(
        self,
        registry: FederatedInstitutionRegistry,
        policy_engine: FederatedPolicyEngine,
        broker: FederatedExchangeBroker,
    ) -> None:
        self.registry = registry
        self.policy_engine = policy_engine
        self.broker = broker
        self._referrals: dict[str, ReferralState] = {}

    @staticmethod
    def _disclosure_request(referral: ReferralRequest, *, requester_reference: str) -> DisclosureRequest:
        return DisclosureRequest(
            requester_reference=requester_reference,
            requesting_institution_id=referral.source_facility_id,
            role="physician",
            relationship_reference="synthetic-relationship-ref",
            purpose="referral",
            category="referral",
            legal_basis_reference="synthetic-treatment-basis",
            consent_status=CONSENT_ACTIVE,
            audit_reference=f"audit-{referral.correlation_id}",
            minimum_necessary=True,
            at=referral.expires_at,
            patient_reference=referral.patient_reference,
            record_reference=referral.referral_id,
        )

    def create(
        self,
        referral: ReferralRequest,
        *,
        requester_reference: str,
        at: str,
        actor_reference: str,
    ) -> ReferralState:
        if referral.referral_id in self._referrals:
            raise FederationConflict("referral identifier already exists")
        if _parse_iso(at) >= _parse_iso(referral.expires_at):
            raise FederationDenied("referral request is expired at creation")
        source = self.registry.assert_authorized(referral.source_facility_id, at=at)
        destination = self.registry.assert_authorized(referral.destination_facility_id, at=at)
        if source.kind != KIND_FACILITY or destination.kind != KIND_FACILITY:
            raise FederationDenied("referrals require facility endpoints")
        if (
            referral.destination_directorate_id is not None
            and destination.directorate_id != referral.destination_directorate_id
        ):
            raise FederationDenied("destination is outside the addressed directorate")
        self.registry.assert_trust(
            referral.source_facility_id,
            referral.destination_facility_id,
            category="referral",
            at=at,
        )
        request = self._disclosure_request(referral, requester_reference=requester_reference)
        request = replace(request, at=at, audit_reference=f"audit-{referral.correlation_id}")
        decision = self.policy_engine.assert_allowed(
            request, target_institution_id=referral.destination_facility_id
        )
        state = ReferralState(request=referral, status=REFERRAL_CREATED)
        self._referrals[referral.referral_id] = state
        envelope = ExchangeEnvelope(
            envelope_id=f"ref-{referral.referral_id}",
            idempotency_key=f"referral:{referral.referral_id}",
            correlation_id=referral.correlation_id,
            source_institution_id=referral.source_facility_id,
            destination_institution_id=referral.destination_facility_id,
            message_type="referral",
            patient_reference=referral.patient_reference,
            record_reference=referral.referral_id,
            category="referral",
            revision=1,
            event_sequence=1,
            expires_at=referral.expires_at,
            decision_digest=decision.decision_digest,
            provenance_digest=_digest(referral.__dict__),
            requester_reference=requester_reference,
        )
        state.status = REFERRAL_ROUTED
        state.envelope_id = envelope.envelope_id
        receipt = self.broker.send(envelope, at=at, actor_reference=actor_reference)
        if receipt.status == EXCHANGE_DELIVERED:
            state.status = REFERRAL_TRANSMITTED
        else:
            state.reason_code = receipt.reason_code
        return state

    def acknowledge(
        self, referral_id: str, *, institution_id: str, at: str, actor_reference: str
    ) -> ReferralState:
        state = self._state(referral_id)
        if state.status != REFERRAL_TRANSMITTED:
            raise FederationDenied("only a transmitted referral can be acknowledged")
        self.broker.acknowledge(
            state.envelope_id or "",
            institution_id=institution_id,
            at=at,
            actor_reference=actor_reference,
        )
        state.status = REFERRAL_ACKNOWLEDGED
        state.acknowledged_by = institution_id
        return state

    def accept_or_reject(
        self,
        referral_id: str,
        *,
        institution_id: str,
        at: str,
        actor_reference: str,
        accepted: bool,
    ) -> ReferralState:
        state = self._state(referral_id)
        if state.status != REFERRAL_ACKNOWLEDGED or state.acknowledged_by != institution_id:
            raise FederationDenied("destination must acknowledge before deciding")
        self.broker.accept(
            state.envelope_id or "",
            institution_id=institution_id,
            at=at,
            actor_reference=actor_reference,
            accepted=accepted,
        )
        state.status = REFERRAL_ACCEPTED if accepted else REFERRAL_REJECTED
        state.decision_by = institution_id
        state.reason_code = "none" if accepted else "referral_rejected"
        return state

    def cancel(self, referral_id: str, *, at: str, actor_reference: str) -> ReferralState:
        state = self._state(referral_id)
        if state.status in {REFERRAL_ACCEPTED, REFERRAL_REJECTED, REFERRAL_CANCELLED}:
            raise FederationDenied("terminal referral cannot be cancelled")
        state.status = REFERRAL_CANCELLED
        state.reason_code = "cancelled"
        self.broker._audit_event(
            envelope_id=state.envelope_id or referral_id,
            state=state.status,
            reason=state.reason_code,
            actor_reference=actor_reference,
        )
        return state

    def expire(self, referral_id: str, *, at: str, actor_reference: str) -> ReferralState:
        state = self._state(referral_id)
        if state.status in {REFERRAL_ACCEPTED, REFERRAL_REJECTED, REFERRAL_CANCELLED}:
            return state
        if _parse_iso(at) < _parse_iso(state.request.expires_at):
            raise FederationDenied("referral is not yet expired")
        state.status = REFERRAL_EXPIRED
        state.reason_code = "expired"
        self.broker._audit_event(
            envelope_id=state.envelope_id or referral_id,
            state=state.status,
            reason=state.reason_code,
            actor_reference=actor_reference,
        )
        return state

    def _state(self, referral_id: str) -> ReferralState:
        state = self._referrals.get(referral_id)
        if state is None:
            raise FederationDenied("unknown referral")
        return state

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": FEDERATION_SCHEMA,
            "referrals": {key: value.to_public_dict() for key, value in self._referrals.items()},
        }

    def restore(self, snapshot: Mapping[str, Any]) -> None:
        if snapshot.get("schema") != FEDERATION_SCHEMA:
            raise FederationIntegrityError("unsupported referral snapshot schema")
        raw = snapshot.get("referrals", {})
        if not isinstance(raw, Mapping):
            raise FederationIntegrityError("referral snapshot must be a mapping")
        restored: dict[str, ReferralState] = {}
        for key, item in raw.items():
            if not isinstance(item, Mapping) or key != item.get("referral_id"):
                raise FederationIntegrityError("referral key does not match its identifier")
            request = ReferralRequest(
                referral_id=str(item["referral_id"]),
                source_facility_id=str(item["source_facility_id"]),
                destination_facility_id=str(item["destination_facility_id"]),
                destination_directorate_id=item.get("destination_directorate_id"),
                patient_reference=str(item["patient_reference"]),
                purpose="referral",
                priority=str(item["priority"]),
                reason_code=str(item.get("reason_code", "none")),
                expires_at=str(item["expires_at"]),
                correlation_id=str(item["correlation_id"]),
            )
            state = ReferralState(
                request=request,
                status=str(item["status"]),
                acknowledged_by=item.get("acknowledged_by"),
                decision_by=item.get("decision_by"),
                envelope_id=item.get("envelope_id"),
                reason_code=str(item.get("reason_code", "none")),
            )
            restored[key] = state
        self._referrals = restored


@dataclass(frozen=True)
class FederatedFHIRPrecheck:
    """Bounded summary only; never echoes bundle content or raw errors."""

    valid: bool
    resource_types: tuple[str, ...]
    reference_count: int
    reason_code: str


def precheck_fhir_bundle(
    bundle: Mapping[str, Any],
    *,
    expected_patient_reference: str,
    expected_organization_id: str | None = None,
) -> FederatedFHIRPrecheck:
    """Delegate payload shape checks to the canonical synthetic guard.

    This is a pre-check, not a FHIR conformance claim. Raw validation text is
    deliberately discarded and replaced by a bounded reason code.
    """

    _opaque(expected_patient_reference, "expected_patient_reference")
    if expected_organization_id is not None:
        _opaque(expected_organization_id, "expected_organization_id")
    try:
        result = _durable.FHIRDisclosureGuard().validate(
            bundle,
            expected_patient_reference=expected_patient_reference,
            expected_organization_id=expected_organization_id,
        )
    except Exception:
        _metric(outcome="rejected", reason="validation_failed")
        raise FederationValidationError("federated FHIR pre-check failed") from None
    reason = "none" if result.valid else "validation_failed"
    _metric(outcome="completed" if result.valid else "rejected", reason=reason)
    return FederatedFHIRPrecheck(
        valid=result.valid,
        resource_types=result.resource_types,
        reference_count=result.reference_count,
        reason_code=reason,
    )


class FederatedObservability:
    """Institution-level counters without patient or clinical payloads."""

    def __init__(self, broker: FederatedExchangeBroker) -> None:
        self.broker = broker
        self._denials: Counter[tuple[str, str]] = Counter()
        self._availability: Counter[str] = Counter()

    def record_denial(self, *, institution_id: str, reason: str) -> None:
        _opaque(institution_id, "institution_id")
        self._denials[(institution_id, _safe_reason(reason))] += 1

    def record_availability(self, *, institution_id: str) -> None:
        _opaque(institution_id, "institution_id")
        self._availability[institution_id] += 1

    def snapshot(self) -> dict[str, Any]:
        summary = self.broker.summary()
        result = {
            "schema": FEDERATION_SCHEMA,
            "exchange": summary,
            "audit_integrity": self.broker.audit_chain()["status"],
            "denials": [
                {"institution_id": institution, "reason_code": reason, "count": count}
                for (institution, reason), count in sorted(self._denials.items())
            ],
            "availability": [
                {"institution_id": institution, "checks": count}
                for institution, count in sorted(self._availability.items())
            ],
        }
        _reject_sensitive(result)
        return result


@dataclass
class FederatedCoreCoordinator:
    """Composes the additive federation contracts over canonical services."""

    registry: FederatedInstitutionRegistry = field(default_factory=FederatedInstitutionRegistry)
    ledger: FederatedOwnershipLedger | None = None
    policy_engine: FederatedPolicyEngine | None = None
    broker: FederatedExchangeBroker | None = None
    referrals: FederatedReferralRouter | None = None
    observability: FederatedObservability | None = None

    def __post_init__(self) -> None:
        self.ledger = self.ledger or FederatedOwnershipLedger(self.registry)
        self.policy_engine = self.policy_engine or FederatedPolicyEngine(self.registry, self.ledger)
        self.broker = self.broker or FederatedExchangeBroker(self.registry, self.policy_engine)
        self.referrals = self.referrals or FederatedReferralRouter(
            self.registry, self.policy_engine, self.broker
        )
        self.observability = self.observability or FederatedObservability(self.broker)

    def authorize(self, request: DisclosureRequest, *, target_institution_id: str) -> DisclosureDecision:
        decision = self.policy_engine.evaluate(request, target_institution_id=target_institution_id)
        if not decision.allowed:
            self.observability.record_denial(
                institution_id=request.requesting_institution_id, reason=decision.reason_code
            )
            raise FederationDenied(f"disclosure denied: {decision.reason_code}")
        return decision

    def register(self, record: FederatedRecord) -> FederatedRecord:
        return self.ledger.register(record)

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": FEDERATION_SCHEMA,
            "registry": self.registry.snapshot(),
            "ownership": self.ledger.snapshot(),
            "disclosure": self.policy_engine.snapshot(),
            "exchange": self.broker.snapshot(),
            "referrals": self.referrals.snapshot(),
            "observability": self.observability.snapshot(),
        }

    def restore(self, snapshot: Mapping[str, Any]) -> None:
        if snapshot.get("schema") != FEDERATION_SCHEMA:
            raise FederationIntegrityError("unsupported coordinator snapshot schema")
        self.registry.restore(snapshot["registry"])
        self.ledger.restore(snapshot["ownership"])
        self.policy_engine.restore(snapshot["disclosure"])
        self.broker.restore(snapshot["exchange"])
        self.referrals.restore(snapshot["referrals"])
