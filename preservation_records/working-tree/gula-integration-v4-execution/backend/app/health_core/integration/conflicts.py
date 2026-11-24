"""Deterministic conflict resolution contract for divergent synthetic events.

Three explicit strategies are supported: reject everything, keep the first
event, or keep the last event with an audit record for every superseded event.
A decision always accounts for *every* candidate event; a validation helper
fails closed if an event would be dropped without a disposition and audit.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from enum import StrEnum

from app.health_core.common import DomainEvent, InvalidStateTransitionError


class ConflictStrategy(StrEnum):
    """Supported, explicitly named resolution strategies."""

    REJECT = "reject"
    KEEP_FIRST = "keep_first"
    KEEP_LAST_WITH_AUDIT = "keep_last_with_audit"


class Disposition(StrEnum):
    """What happened to one candidate event."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


@dataclass(frozen=True, slots=True)
class ConflictCase:
    """A set of divergent candidates for one tenant-scoped aggregate."""

    conflict_id: str
    aggregate_key: str
    tenant_id: str
    events: tuple[DomainEvent, ...]
    expected_version: int
    observed_version: int

    def __post_init__(self) -> None:
        if not self.events:
            raise ValueError("a conflict case must contain at least one event")
        if len({event.event_id for event in self.events}) != len(self.events):
            raise ValueError("a conflict case cannot repeat an event_id")
        if any(event.tenant_id != self.tenant_id for event in self.events):
            raise ValueError("a conflict case cannot mix tenants")


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """Immutable audit trail entry for a non-accepted event."""

    audit_id: str
    conflict_id: str
    event_id: str
    strategy: ConflictStrategy
    action: Disposition
    reason: str
    tenant_id: str


@dataclass(frozen=True, slots=True)
class EventDisposition:
    """Per-event decision, present even when the event is not accepted."""

    event_id: str
    disposition: Disposition
    reason: str
    audit_id: str | None


@dataclass(frozen=True, slots=True)
class ConflictDecision:
    """Deterministic resolution record with a full accounting of all events."""

    decision_id: str
    conflict: ConflictCase
    strategy: ConflictStrategy
    accepted_event: DomainEvent | None
    dispositions: tuple[EventDisposition, ...]
    audit: tuple[AuditRecord, ...]


def _deterministic_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16].upper()
    return f"SYN-{prefix}-{digest}"


def _replay_key(event: DomainEvent) -> tuple[str, str]:
    return event.occurred_at, event.event_id


def assert_no_silent_drops(decision: ConflictDecision) -> None:
    """Fail closed if any candidate event lacks a disposition and audit entry."""
    case_events = decision.conflict.events
    if len(decision.dispositions) != len(case_events):
        raise InvalidStateTransitionError(
            "disposition count does not match conflict candidates",
            details={"conflict_id": decision.conflict.conflict_id},
        )
    disposition_ids = {item.event_id for item in decision.dispositions}
    if disposition_ids != {event.event_id for event in case_events}:
        raise InvalidStateTransitionError(
            "disposition ids do not match conflict candidates",
            details={"conflict_id": decision.conflict.conflict_id},
        )
    dropped = [
        item for item in decision.dispositions if item.disposition is not Disposition.ACCEPTED
    ]
    audited_ids = {record.event_id for record in decision.audit}
    if any(item.event_id not in audited_ids for item in dropped):
        raise InvalidStateTransitionError(
            "a non-accepted event has no audit record",
            details={"conflict_id": decision.conflict.conflict_id},
        )
    if any(item.audit_id is None for item in dropped):
        raise InvalidStateTransitionError(
            "a non-accepted event has no audit reference",
            details={"conflict_id": decision.conflict.conflict_id},
        )


def resolve_conflict(case: ConflictCase, strategy: ConflictStrategy) -> ConflictDecision:
    """Resolve a conflict deterministically for the requested strategy."""
    ordered = tuple(sorted(case.events, key=_replay_key))
    if strategy is ConflictStrategy.REJECT:
        accepted: DomainEvent | None = None
    elif strategy is ConflictStrategy.KEEP_FIRST:
        accepted = ordered[0]
    else:
        accepted = ordered[-1]

    dispositions: list[EventDisposition] = []
    audits: list[AuditRecord] = []
    for event in ordered:
        if event == accepted:
            disposition = Disposition.ACCEPTED
            reason = f"selected by {strategy.value}"
            audit_id: str | None = None
        else:
            disposition = (
                Disposition.REJECTED
                if strategy is ConflictStrategy.REJECT
                else Disposition.SUPERSEDED
            )
            reason = f"{disposition.value} by {strategy.value}; event retained in audit trail"
            audit = AuditRecord(
                audit_id=_deterministic_id(
                    "AUD", case.conflict_id, event.event_id, disposition.value, strategy.value
                ),
                conflict_id=case.conflict_id,
                event_id=event.event_id,
                strategy=strategy,
                action=disposition,
                reason=reason,
                tenant_id=case.tenant_id,
            )
            audits.append(audit)
            audit_id = audit.audit_id
        dispositions.append(
            EventDisposition(
                event_id=event.event_id,
                disposition=disposition,
                reason=reason,
                audit_id=audit_id,
            )
        )

    decision = ConflictDecision(
        decision_id=_deterministic_id(
            "DEC",
            case.conflict_id,
            strategy.value,
            ",".join(event.event_id for event in ordered),
        ),
        conflict=replace(case, events=ordered),
        strategy=strategy,
        accepted_event=accepted,
        dispositions=tuple(dispositions),
        audit=tuple(audits),
    )
    assert_no_silent_drops(decision)
    return decision
