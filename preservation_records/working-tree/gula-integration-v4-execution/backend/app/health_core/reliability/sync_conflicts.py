"""Isolated offline-sync conflict disposition with hash-chained accounting.

This is an independent design, not a copy of ``integration/conflicts.py``: it works
with arrival-ordered sync candidates, an explicit named policy, a quarantining
model (no clinical merge), and one hash-chained audit record per candidate —
including the adopted candidate. Every candidate receives exactly one disposition.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from app.health_core.common import DomainEvent
from app.health_core.common.errors import InvalidSyntheticReferenceError
from app.health_core.reliability.audit import (
    AuditLog,
    AuditRecord,
    AuditVerification,
    verify_chain,
)
from app.health_core.reliability.errors import ConflictAccountingError
from app.health_core.reliability.hashing import (
    canonical_json_bytes,
    require_synthetic_id,
    sha256_hex,
)


class SyncPolicy(StrEnum):
    """Explicit, deterministic conflict dispositions (no semantic merging)."""

    QUARANTINE_ALL = "quarantine_all"
    FIRST_WRITER_WINS = "first_writer_wins"
    HIGHEST_VERSION_WINS = "highest_version_wins"
    LATEST_ARRIVAL_WINS = "latest_arrival_wins"


class SyncOutcome(StrEnum):
    """Fate of one candidate event."""

    ADOPTED = "adopted"
    QUARANTINED = "quarantined"


class DispositionReason(StrEnum):
    """Stable reason codes recorded for each candidate."""

    ADOPTED_BY_POLICY = "adopted_by_policy"
    LOST_TO_WINNER = "lost_to_winner"
    QUARANTINED_BY_POLICY = "quarantined_by_policy"


@dataclass(frozen=True, slots=True)
class SyncCandidate:
    """A divergent event arriving from a synthetic offline node."""

    candidate_id: str
    event: DomainEvent
    arrival_index: int
    source_node: str
    payload_digest: str

    def __post_init__(self) -> None:
        if self.arrival_index < 1:
            raise ValueError("arrival_index must start at 1")
        expected = sha256_hex(canonical_json_bytes(self.event.payload))
        if self.payload_digest != expected:
            raise ConflictAccountingError("candidate payload digest does not match its event")


def make_candidate(
    *, event: DomainEvent, arrival_index: int, source_node: str, candidate_id: str
) -> SyncCandidate:
    """Build a validated candidate with a freshly computed payload digest."""
    require_synthetic_id(candidate_id, field="candidate_id")
    require_synthetic_id(source_node, field="source_node")
    require_synthetic_id(event.event_id, field="event_id")
    if not isinstance(event.tenant_id, str) or not event.tenant_id.startswith("SYN-"):
        raise InvalidSyntheticReferenceError(
            "candidate tenant must be a synthetic reference", details={"field": "tenant_id"}
        )
    return SyncCandidate(
        candidate_id=candidate_id,
        event=event,
        arrival_index=arrival_index,
        source_node=source_node,
        payload_digest=sha256_hex(canonical_json_bytes(event.payload)),
    )


@dataclass(frozen=True, slots=True)
class CandidateDisposition:
    """One candidate's explicit outcome and its chained audit position."""

    candidate_id: str
    event_id: str
    outcome: SyncOutcome
    reason: DispositionReason
    audit_sequence: int


@dataclass(frozen=True, slots=True)
class ResolutionLedger:
    """Complete, auditable disposition of one conflict set."""

    ledger_id: str
    policy: SyncPolicy
    winner_candidate_id: str | None
    dispositions: tuple[CandidateDisposition, ...]
    audit: tuple[AuditRecord, ...]
    audit_head: str

    def verify_audit(self) -> AuditVerification:
        """Verify the ledger's hash chain against its recorded head."""
        return verify_chain(
            self.audit, expected_head=self.audit_head, expected_count=len(self.audit)
        )


def _winner(candidates: Sequence[SyncCandidate], policy: SyncPolicy) -> SyncCandidate | None:
    if policy is SyncPolicy.QUARANTINE_ALL:
        return None
    if policy is SyncPolicy.FIRST_WRITER_WINS:
        return min(candidates, key=lambda item: (item.arrival_index, item.candidate_id))
    if policy is SyncPolicy.LATEST_ARRIVAL_WINS:
        return max(candidates, key=lambda item: (item.arrival_index, item.candidate_id))
    return max(
        candidates,
        key=lambda item: (item.event.version, item.event.occurred_at, item.candidate_id),
    )


def resolve_sync_conflict(
    candidates: Sequence[SyncCandidate],
    policy: SyncPolicy,
    *,
    recorded_at: str,
    resolver_id: str,
) -> ResolutionLedger:
    """Resolve a conflict set deterministically, with one audit record per candidate."""
    if not candidates:
        raise ConflictAccountingError("a conflict set must contain at least one candidate")
    require_synthetic_id(resolver_id, field="resolver_id")
    if not isinstance(recorded_at, str) or not recorded_at:
        raise ConflictAccountingError("recorded_at must be a non-empty timestamp")
    ids = [item.candidate_id for item in candidates]
    event_ids = [item.event.event_id for item in candidates]
    arrivals = [item.arrival_index for item in candidates]
    if len(set(ids)) != len(ids) or len(set(event_ids)) != len(event_ids):
        raise ConflictAccountingError("candidate and event ids must be unique in a conflict set")
    if len(set(arrivals)) != len(arrivals):
        raise ConflictAccountingError("arrival indexes must be unique in a conflict set")
    tenants = {item.event.tenant_id for item in candidates}
    if len(tenants) != 1:
        raise ConflictAccountingError("a conflict set cannot mix tenants")

    ordered = tuple(sorted(candidates, key=lambda item: item.candidate_id))
    winner = _winner(ordered, policy)
    winner_id = winner.candidate_id if winner is not None else None
    log = AuditLog()
    dispositions: list[CandidateDisposition] = []
    for item in ordered:
        if winner is None:
            outcome = SyncOutcome.QUARANTINED
            reason = DispositionReason.QUARANTINED_BY_POLICY
        elif item.candidate_id == winner_id:
            outcome = SyncOutcome.ADOPTED
            reason = DispositionReason.ADOPTED_BY_POLICY
        else:
            outcome = SyncOutcome.QUARANTINED
            reason = DispositionReason.LOST_TO_WINNER
        record = log.append(
            subject_id=item.candidate_id,
            actor=item.source_node,
            action=policy.value,
            summary=reason.value,
            recorded_at=recorded_at,
            payload={
                "event_id": item.event.event_id,
                "outcome": outcome.value,
                "reason": reason.value,
                "winner_candidate_id": winner_id,
                "resolver_id": resolver_id,
            },
        )
        dispositions.append(
            CandidateDisposition(
                candidate_id=item.candidate_id,
                event_id=item.event.event_id,
                outcome=outcome,
                reason=reason,
                audit_sequence=record.sequence,
            )
        )
    ledger_id = f"SYN-LED-{sha256_hex(canonical_json_bytes([policy.value, sorted(ids)]))[:16].upper()}"
    ledger = ResolutionLedger(
        ledger_id=ledger_id,
        policy=policy,
        winner_candidate_id=winner_id,
        dispositions=tuple(dispositions),
        audit=log.records,
        audit_head=log.head,
    )
    assert_full_accounting(ledger)
    return ledger


def assert_full_accounting(ledger: ResolutionLedger) -> None:
    """Fail closed if any candidate lacks a disposition, audit entry or chain link."""
    disposition_ids = [item.candidate_id for item in ledger.dispositions]
    audited_ids = [record.subject_id for record in ledger.audit]
    if len(set(disposition_ids)) != len(disposition_ids) or len(audited_ids) != len(disposition_ids):
        raise ConflictAccountingError("disposition/audit counts are inconsistent")
    if set(disposition_ids) != set(audited_ids):
        raise ConflictAccountingError("a candidate has no matching audit record")
    for item in ledger.dispositions:
        if not 1 <= item.audit_sequence <= len(ledger.audit):
            raise ConflictAccountingError("disposition has an invalid audit sequence")
        linked = ledger.audit[item.audit_sequence - 1]
        if linked.subject_id != item.candidate_id or linked.sequence != item.audit_sequence:
            raise ConflictAccountingError("disposition does not link to its audit record")
    if not ledger.verify_audit().ok:
        raise ConflictAccountingError("resolution audit chain failed verification")
