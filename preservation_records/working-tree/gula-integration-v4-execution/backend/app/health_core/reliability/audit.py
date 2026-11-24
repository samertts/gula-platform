"""Hash-chained, append-only audit records for isolated reliability designs.

Each record stores only a digest of its optional payload, never the payload itself,
and every record links to the hash of its predecessor. An append-only head/count
anchor maintained by :meth:`AuditLog.append` lets verification detect interior
field edits, reorders, middle/first deletion, and tail deletion. The chain is
unsigned and the anchor is a process-local value with no external, durable or
keyed backing: an in-process actor who can rewrite the private record list and
recompute hashes (and reset the in-process anchor) can produce a fully coherent
rehash forgery that verifies as valid. That is outside this design's detection
scope. SHA-256 only; no external dependency.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from enum import StrEnum

from app.health_core.reliability.hashing import (
    canonical_json_bytes,
    require_synthetic_id,
    require_text,
    sha256_hex,
)

GENESIS_HASH = "0" * 64


class AuditFailure(StrEnum):
    """Stable reason codes returned by chain verification."""

    GENESIS_MISMATCH = "genesis_mismatch"
    HASH_MISMATCH = "hash_mismatch"
    BROKEN_LINK = "broken_link"
    SEQUENCE_GAP = "sequence_gap"
    OUT_OF_ORDER = "out_of_order"
    HEAD_MISMATCH = "head_mismatch"
    COUNT_MISMATCH = "count_mismatch"


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """One immutable audit record. ``payload_digest`` never holds raw content."""

    sequence: int
    subject_id: str
    actor: str
    action: str
    summary: str
    recorded_at: str
    previous_hash: str
    payload_digest: str
    record_hash: str

    def body(self) -> dict[str, object]:
        """Return the exact fields covered by ``record_hash``."""
        return {
            "sequence": self.sequence,
            "subject_id": self.subject_id,
            "actor": self.actor,
            "action": self.action,
            "summary": self.summary,
            "recorded_at": self.recorded_at,
            "previous_hash": self.previous_hash,
            "payload_digest": self.payload_digest,
        }


@dataclass(frozen=True, slots=True)
class AuditVerification:
    """Structured verification result (no exception-only failure path)."""

    ok: bool
    verified_count: int
    failure: AuditFailure | None
    detail: str


def chain_head(records: Sequence[AuditRecord]) -> str:
    """Return the chain head, or the genesis hash for an empty chain."""
    return records[-1].record_hash if records else GENESIS_HASH


def _failure(failure: AuditFailure, detail: str, count: int) -> AuditVerification:
    return AuditVerification(ok=False, verified_count=count, failure=failure, detail=detail)


def verify_chain(
    records: Sequence[AuditRecord],
    *,
    expected_head: str | None = None,
    expected_count: int | None = None,
) -> AuditVerification:
    """Verify sequence, link integrity, hashes and (optionally) a trusted head."""
    if expected_count is not None and len(records) != expected_count:
        return _failure(
            AuditFailure.COUNT_MISMATCH,
            f"expected {expected_count} records, found {len(records)}",
            len(records),
        )
    if not records:
        if expected_head is not None and expected_head != GENESIS_HASH:
            return _failure(AuditFailure.HEAD_MISMATCH, "empty chain head mismatch", 0)
        return AuditVerification(ok=True, verified_count=0, failure=None, detail="empty chain")

    first = records[0]
    if first.sequence != 1 or first.previous_hash != GENESIS_HASH:
        return _failure(AuditFailure.GENESIS_MISMATCH, "first record is not chained to genesis", 0)
    for index, record in enumerate(records):
        recomputed = sha256_hex(canonical_json_bytes(record.body()))
        if recomputed != record.record_hash:
            return _failure(
                AuditFailure.HASH_MISMATCH,
                f"record {record.sequence} fields were modified",
                index,
            )
        if index:
            previous = records[index - 1]
            if record.sequence < previous.sequence + 1:
                return _failure(
                    AuditFailure.OUT_OF_ORDER,
                    f"record {record.sequence} appears after {previous.sequence}",
                    index,
                )
            if record.sequence > previous.sequence + 1:
                return _failure(
                    AuditFailure.SEQUENCE_GAP,
                    f"gap between records {previous.sequence} and {record.sequence}",
                    index,
                )
            if record.previous_hash != previous.record_hash:
                return _failure(
                    AuditFailure.BROKEN_LINK,
                    f"record {record.sequence} does not link to its predecessor",
                    index,
                )
    if expected_head is not None and chain_head(records) != expected_head:
        return _failure(AuditFailure.HEAD_MISMATCH, "chain head does not match trusted head", len(records))
    return AuditVerification(
        ok=True, verified_count=len(records), failure=None, detail="chain verified"
    )


class AuditLog:
    """Append-only in-memory audit log with append-only in-process anchors."""

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []
        self._anchored_head: str = GENESIS_HASH
        self._anchored_count: int = 0

    @property
    def records(self) -> tuple[AuditRecord, ...]:
        """Defensive tuple of all records in append order."""
        return tuple(self._records)

    @property
    def head(self) -> str:
        """Append-only anchor set by ``append``; never recomputed from records.

        It makes tail deletion detectable, but it is an in-process value: a fully
        coherent rehash forgery by an actor who can also reset this anchor is not
        detectable, because the chain is unsigned and has no external/keyed anchor.
        """
        return self._anchored_head

    @property
    def count(self) -> int:
        """Append-only count of records appended, not the live list length."""
        return self._anchored_count

    def append(
        self,
        *,
        subject_id: str,
        actor: str,
        action: str,
        summary: str,
        recorded_at: str,
        payload: dict[str, object] | None = None,
    ) -> AuditRecord:
        """Append one record; raw ``payload`` is reduced to a SHA-256 digest."""
        safe_subject = require_synthetic_id(subject_id, field="subject_id")
        safe_actor = require_synthetic_id(actor, field="actor")
        safe_action = require_text(action, field="action")
        safe_summary = require_text(summary, field="summary")
        if not isinstance(recorded_at, str) or not recorded_at:
            raise ValueError("recorded_at must be a non-empty string")
        payload_digest = sha256_hex(canonical_json_bytes(payload or {}))
        record = AuditRecord(
            sequence=len(self._records) + 1,
            subject_id=safe_subject,
            actor=safe_actor,
            action=safe_action,
            summary=safe_summary,
            recorded_at=recorded_at,
            previous_hash=self.head,
            payload_digest=payload_digest,
            record_hash=GENESIS_HASH,
        )
        sealed = replace(record, record_hash=sha256_hex(canonical_json_bytes(record.body())))
        self._records.append(sealed)
        self._anchored_head = sealed.record_hash
        self._anchored_count = len(self._records)
        return sealed

    def verify(self) -> AuditVerification:
        """Verify chain integrity against the append-only in-process anchors.

        Detection of a fully coherent rehash forgery is explicitly out of scope
        because the chain is unsigned (see the module docstring).
        """
        return verify_chain(
            self.records,
            expected_head=self._anchored_head,
            expected_count=self._anchored_count,
        )
