"""Tests for deterministic conflict resolution and its audit trail."""

from __future__ import annotations

from dataclasses import replace

import pytest
from app.health_core.common import (
    AggregateType,
    DomainEvent,
    EventType,
    InvalidStateTransitionError,
)
from app.health_core.identity import DEFAULT_SYNTHETIC_TENANT
from app.health_core.integration import (
    ConflictCase,
    ConflictStrategy,
    Disposition,
    assert_no_silent_drops,
    resolve_conflict,
)


def _event(event_id: str, occurred_at: str, tenant_id: str = DEFAULT_SYNTHETIC_TENANT) -> DomainEvent:
    return DomainEvent(
        event_id=event_id,
        event_type=EventType.RESULT_RECORDED,
        aggregate_type=AggregateType.LAB_RESULT,
        aggregate_id="SYN-RES-0001",
        tenant_id=tenant_id,
        occurred_at=occurred_at,
        version=1,
        payload={"fixture": event_id},
    )


def _case(events: tuple[DomainEvent, ...]) -> ConflictCase:
    return ConflictCase(
        conflict_id="SYN-CONF-0001",
        aggregate_key=f"{DEFAULT_SYNTHETIC_TENANT}/lab_result/SYN-RES-0001",
        tenant_id=DEFAULT_SYNTHETIC_TENANT,
        events=events,
        expected_version=2,
        observed_version=1,
    )


def test_reject_strategy_rejects_every_event_with_audit() -> None:
    case = _case(
        (
            _event("SYN-EVT-A", "2026-11-18T10:00:00+00:00"),
            _event("SYN-EVT-B", "2026-11-18T11:00:00+00:00"),
        )
    )
    decision = resolve_conflict(case, ConflictStrategy.REJECT)
    assert decision.accepted_event is None
    assert [item.disposition for item in decision.dispositions] == [
        Disposition.REJECTED,
        Disposition.REJECTED,
    ]
    assert len(decision.audit) == 2
    assert len({record.audit_id for record in decision.audit}) == 2
    assert decision.decision_id.startswith("SYN-DEC-")


def test_keep_first_accepts_earliest_event_by_occurred_at() -> None:
    earlier = _event("SYN-EVT-A", "2026-11-18T10:00:00+00:00")
    later = _event("SYN-EVT-B", "2026-11-18T11:00:00+00:00")
    decision = resolve_conflict(_case((later, earlier)), ConflictStrategy.KEEP_FIRST)
    assert decision.accepted_event == earlier
    assert [item.disposition for item in decision.dispositions] == [
        Disposition.ACCEPTED,
        Disposition.SUPERSEDED,
    ]
    assert len(decision.audit) == 1
    assert decision.audit[0].event_id == later.event_id


def test_keep_last_with_audit_accepts_latest_event() -> None:
    earlier = _event("SYN-EVT-A", "2026-11-18T10:00:00+00:00")
    later = _event("SYN-EVT-B", "2026-11-18T11:00:00+00:00")
    decision = resolve_conflict(
        _case((earlier, later)), ConflictStrategy.KEEP_LAST_WITH_AUDIT
    )
    assert decision.accepted_event == later
    assert [item.disposition for item in decision.dispositions] == [
        Disposition.SUPERSEDED,
        Disposition.ACCEPTED,
    ]
    assert len(decision.audit) == 1
    assert decision.audit[0].event_id == earlier.event_id
    assert decision.audit[0].action is Disposition.SUPERSEDED


@pytest.mark.parametrize("strategy", tuple(ConflictStrategy))
def test_every_strategy_accounts_for_every_event(strategy: ConflictStrategy) -> None:
    events = (
        _event("SYN-EVT-A", "2026-11-18T10:00:00+00:00"),
        _event("SYN-EVT-B", "2026-11-18T11:00:00+00:00"),
        _event("SYN-EVT-C", "2026-11-18T12:00:00+00:00"),
    )
    decision = resolve_conflict(_case(events), strategy)
    assert len(decision.dispositions) == len(events)
    assert {item.event_id for item in decision.dispositions} == {
        event.event_id for event in events
    }
    assert_no_silent_drops(decision)


def test_resolution_is_deterministic_regardless_of_input_order() -> None:
    events = (
        _event("SYN-EVT-C", "2026-11-18T12:00:00+00:00"),
        _event("SYN-EVT-A", "2026-11-18T10:00:00+00:00"),
        _event("SYN-EVT-B", "2026-11-18T11:00:00+00:00"),
    )
    first = resolve_conflict(_case(events), ConflictStrategy.KEEP_LAST_WITH_AUDIT)
    second = resolve_conflict(
        _case(tuple(reversed(events))), ConflictStrategy.KEEP_LAST_WITH_AUDIT
    )
    assert first == second


def test_decision_id_varies_by_strategy() -> None:
    events = (
        _event("SYN-EVT-A", "2026-11-18T10:00:00+00:00"),
        _event("SYN-EVT-B", "2026-11-18T11:00:00+00:00"),
    )
    first = resolve_conflict(_case(events), ConflictStrategy.KEEP_FIRST)
    second = resolve_conflict(_case(events), ConflictStrategy.KEEP_LAST_WITH_AUDIT)
    assert first.decision_id != second.decision_id


def test_silent_drop_validator_fails_closed() -> None:
    case = _case(
        (
            _event("SYN-EVT-A", "2026-11-18T10:00:00+00:00"),
            _event("SYN-EVT-B", "2026-11-18T11:00:00+00:00"),
        )
    )
    decision = resolve_conflict(case, ConflictStrategy.KEEP_FIRST)
    with pytest.raises(InvalidStateTransitionError):
        assert_no_silent_drops(replace(decision, dispositions=()))
    with pytest.raises(InvalidStateTransitionError):
        assert_no_silent_drops(replace(decision, audit=()))


def test_audit_records_carry_strategy_tenant_and_reason() -> None:
    case = _case(
        (
            _event("SYN-EVT-A", "2026-11-18T10:00:00+00:00"),
            _event("SYN-EVT-B", "2026-11-18T11:00:00+00:00"),
        )
    )
    decision = resolve_conflict(case, ConflictStrategy.KEEP_FIRST)
    record = decision.audit[0]
    assert record.strategy is ConflictStrategy.KEEP_FIRST
    assert record.tenant_id == DEFAULT_SYNTHETIC_TENANT
    assert record.conflict_id == case.conflict_id
    assert record.reason


def test_conflict_case_rejects_invalid_candidate_sets() -> None:
    event = _event("SYN-EVT-A", "2026-11-18T10:00:00+00:00")
    with pytest.raises(ValueError):
        _case(())
    with pytest.raises(ValueError):
        _case((event, event))
    with pytest.raises(ValueError):
        _case((event, _event("SYN-EVT-B", "2026-11-18T11:00:00+00:00", "SYN-LAB-9999")))


def test_single_event_conflict_is_always_accepted_by_keep_strategies() -> None:
    event = _event("SYN-EVT-A", "2026-11-18T10:00:00+00:00")
    case = _case((event,))
    for strategy in (ConflictStrategy.KEEP_FIRST, ConflictStrategy.KEEP_LAST_WITH_AUDIT):
        decision = resolve_conflict(case, strategy)
        assert decision.accepted_event == event
        assert decision.audit == ()
