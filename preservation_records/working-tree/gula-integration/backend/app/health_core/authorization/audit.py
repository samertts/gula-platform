"""Append-only, hash-chained audit log for authorization decisions.

Records are frozen and the log exposes only immutable snapshots, so a caller
cannot edit or delete history through its API. Each record binds to its
predecessor with a SHA-256 hash over a canonical JSON payload.

:func:`verify_audit_chain` is an *internal consistency* check. It detects edits
to a surviving record's payload or hash, records that have been reordered, and
deletions that leave a gap in the sequence or predecessor links (including
deletion of the first record).

It does NOT detect tail truncation: removing the last N records leaves the
surviving prefix internally consistent. It also does NOT detect a coherent
forgery in which the whole chain is rebuilt with recomputed hashes and matching
predecessor links. The chain is unsigned, its hash is public, and the log lives
only in this process, so nothing outside the forged data contradicts it. Making
truncation and full-chain forgery detectable requires an external keyed and
durable anchor (for example a keyed MAC or signature plus an append-only store
outside this process). Until such an anchor exists, this chain is an integrity
check, not a tamper-proof audit trail.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from app.health_core.common.ids import new_synthetic_id

__all__ = [
    "GENESIS_HASH",
    "AuditRecord",
    "AuditVerification",
    "AuthorizationAuditLog",
    "compute_record_hash",
    "verify_audit_chain",
]

GENESIS_HASH = "SYN-GENESIS"


def _canonical_bytes(payload: dict[str, object]) -> bytes:
    """Serialise a payload deterministically for hashing."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def compute_record_hash(payload: dict[str, object], previous_hash: str) -> str:
    """Return the SHA-256 binding of a record payload to its predecessor."""
    return hashlib.sha256(_canonical_bytes(payload) + b"|" + previous_hash.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """One immutable, hash-chained authorization decision record."""

    sequence: int
    record_id: str
    principal_id: str
    tenant_id: str
    action: str
    resource_id: str
    decision: str
    policy_id: str
    reason: str
    occurred_at: str
    previous_hash: str
    record_hash: str

    def canonical_payload(self) -> dict[str, object]:
        """Return every hash-bound field except the hash itself."""
        return {
            "sequence": self.sequence,
            "record_id": self.record_id,
            "principal_id": self.principal_id,
            "tenant_id": self.tenant_id,
            "action": self.action,
            "resource_id": self.resource_id,
            "decision": self.decision,
            "policy_id": self.policy_id,
            "reason": self.reason,
            "occurred_at": self.occurred_at,
            "previous_hash": self.previous_hash,
        }


@dataclass(frozen=True, slots=True)
class AuditVerification:
    """Result of verifying a whole audit chain."""

    is_valid: bool
    errors: tuple[str, ...]
    records_checked: int

    def raise_if_invalid(self) -> None:
        """Raise ``AssertionError`` with the precise integrity failures."""
        if not self.is_valid:
            raise AssertionError(f"audit chain integrity failure: {list(self.errors)}")


def verify_audit_chain(records: Sequence[AuditRecord]) -> AuditVerification:
    """Recompute every hash and predecessor link; detect any tampering."""
    errors: list[str] = []
    for index, record in enumerate(records):
        label = record.record_id
        if record.sequence != index + 1:
            errors.append(f"{label}: expected sequence {index + 1}, got {record.sequence}")
        expected_previous = GENESIS_HASH if index == 0 else records[index - 1].record_hash
        if record.previous_hash != expected_previous:
            errors.append(f"{label}: predecessor hash does not match the chain")
        recomputed = compute_record_hash(record.canonical_payload(), record.previous_hash)
        if recomputed != record.record_hash:
            errors.append(f"{label}: record hash does not match its payload")
    return AuditVerification(
        is_valid=not errors,
        errors=tuple(errors),
        records_checked=len(records),
    )


class AuthorizationAuditLog:
    """In-memory append-only store of authorization decision records."""

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def append(
        self,
        *,
        principal_id: str,
        tenant_id: str,
        action: str,
        resource_id: str,
        decision: str,
        policy_id: str,
        reason: str,
        occurred_at: str | None = None,
    ) -> AuditRecord:
        """Append one decision record with a fresh hash-chain link."""
        previous_hash = self._records[-1].record_hash if self._records else GENESIS_HASH
        sequence = len(self._records) + 1
        record_id = new_synthetic_id("AUD")
        moment = occurred_at or datetime.now(UTC).isoformat()
        payload: dict[str, object] = {
            "sequence": sequence,
            "record_id": record_id,
            "principal_id": principal_id,
            "tenant_id": tenant_id,
            "action": action,
            "resource_id": resource_id,
            "decision": decision,
            "policy_id": policy_id,
            "reason": reason,
            "occurred_at": moment,
            "previous_hash": previous_hash,
        }
        record = AuditRecord(
            sequence=sequence,
            record_id=record_id,
            principal_id=principal_id,
            tenant_id=tenant_id,
            action=action,
            resource_id=resource_id,
            decision=decision,
            policy_id=policy_id,
            reason=reason,
            occurred_at=moment,
            previous_hash=previous_hash,
            record_hash=compute_record_hash(payload, previous_hash),
        )
        self._records.append(record)
        return record

    def records(self) -> tuple[AuditRecord, ...]:
        """Return an immutable snapshot of the full history."""
        return tuple(self._records)

    def verify(self) -> AuditVerification:
        """Verify the integrity of the entire internal chain."""
        return verify_audit_chain(self.records())

    def __len__(self) -> int:
        return len(self._records)
