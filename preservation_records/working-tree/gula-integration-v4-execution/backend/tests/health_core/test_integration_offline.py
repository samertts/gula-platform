"""Tests for the in-memory offline outbox and deterministic replay contract."""

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
    ApplyStatus,
    OfflineOutbox,
    ReplayJournal,
    aggregate_key,
    replay,
)


def _event(
    event_id: str,
    occurred_at: str,
    *,
    version: int = 1,
    aggregate_id: str = "SYN-AGG-0001",
    tenant_id: str = DEFAULT_SYNTHETIC_TENANT,
) -> DomainEvent:
    return DomainEvent(
        event_id=event_id,
        event_type=EventType.OBSERVATION_RECORDED,
        aggregate_type=AggregateType.OBSERVATION,
        aggregate_id=aggregate_id,
        tenant_id=tenant_id,
        occurred_at=occurred_at,
        version=version,
        payload={"fixture": event_id},
    )


def test_enqueue_assigns_monotonic_sequences() -> None:
    outbox = OfflineOutbox()
    first = outbox.enqueue(_event("SYN-EVT-A", "2026-11-18T10:00:00+00:00"))
    second = outbox.enqueue(_event("SYN-EVT-B", "2026-11-18T11:00:00+00:00"))
    assert (first.sequence, second.sequence) == (1, 2)
    assert len(outbox) == 2
    assert outbox.event_ids == frozenset({"SYN-EVT-A", "SYN-EVT-B"})


def test_duplicate_enqueue_is_idempotent() -> None:
    outbox = OfflineOutbox()
    event = _event("SYN-EVT-A", "2026-11-18T10:00:00+00:00")
    first = outbox.enqueue(event)
    second = outbox.enqueue(event)
    assert first is second
    assert len(outbox) == 1


def test_reused_event_id_with_different_payload_is_rejected() -> None:
    outbox = OfflineOutbox()
    event = _event("SYN-EVT-A", "2026-11-18T10:00:00+00:00")
    outbox.enqueue(event)
    changed = replace(event, payload={"fixture": "different"})
    with pytest.raises(InvalidStateTransitionError) as exc:
        outbox.enqueue(changed)
    assert exc.value.code == "INVALID_STATE_TRANSITION"


def test_replay_order_uses_occurred_at_then_sequence() -> None:
    outbox = OfflineOutbox()
    late = _event("SYN-EVT-LATE", "2026-11-18T12:00:00+00:00")
    early = _event("SYN-EVT-EARLY", "2026-11-18T10:00:00+00:00")
    same_a = _event("SYN-EVT-SAME-A", "2026-11-18T11:00:00+00:00")
    same_b = _event("SYN-EVT-SAME-B", "2026-11-18T11:00:00+00:00")
    for event in (late, early, same_a, same_b):
        outbox.enqueue(event)
    ordered = [entry.event.event_id for entry in outbox.ordered_entries()]
    assert ordered == [
        "SYN-EVT-EARLY",
        "SYN-EVT-SAME-A",
        "SYN-EVT-SAME-B",
        "SYN-EVT-LATE",
    ]
    assert [entry.event.event_id for entry in outbox.entries] == [
        "SYN-EVT-LATE",
        "SYN-EVT-EARLY",
        "SYN-EVT-SAME-A",
        "SYN-EVT-SAME-B",
    ]


def test_replay_applies_events_and_tracks_versions() -> None:
    outbox = OfflineOutbox()
    outbox.enqueue(_event("SYN-EVT-A", "2026-11-18T10:00:00+00:00", version=1))
    outbox.enqueue(
        _event("SYN-EVT-B", "2026-11-18T11:00:00+00:00", version=2)
    )
    journal = ReplayJournal()
    decisions = replay(outbox, journal)
    assert [decision.status for decision in decisions] == [
        ApplyStatus.APPLIED,
        ApplyStatus.APPLIED,
    ]
    key = aggregate_key(_event("SYN-EVT-A", "2026-11-18T10:00:00+00:00"))
    assert journal.version_of(key) == 2
    assert journal.applied_event_ids == frozenset({"SYN-EVT-A", "SYN-EVT-B"})


def test_second_replay_is_idempotent_by_event_id() -> None:
    outbox = OfflineOutbox()
    outbox.enqueue(_event("SYN-EVT-A", "2026-11-18T10:00:00+00:00"))
    journal = ReplayJournal()
    replay(outbox, journal)
    decisions = replay(outbox, journal)
    assert [decision.status for decision in decisions] == [ApplyStatus.DUPLICATE]
    assert len(journal.applied_event_ids) == 1


def test_divergent_same_version_is_detected() -> None:
    outbox = OfflineOutbox()
    outbox.enqueue(_event("SYN-EVT-A", "2026-11-18T10:00:00+00:00", version=1))
    outbox.enqueue(_event("SYN-EVT-B", "2026-11-18T11:00:00+00:00", version=1))
    decisions = replay(outbox)
    assert [decision.status for decision in decisions] == [
        ApplyStatus.APPLIED,
        ApplyStatus.CONFLICT,
    ]
    assert "divergent" in decisions[1].reason
    assert decisions[1].expected_version == 2
    assert decisions[1].observed_version == 1


def test_stale_version_is_detected() -> None:
    journal = ReplayJournal()
    journal.apply(_event("SYN-EVT-A", "2026-11-18T10:00:00+00:00", version=1))
    journal.apply(_event("SYN-EVT-B", "2026-11-18T11:00:00+00:00", version=2))
    decision = journal.apply(
        _event("SYN-EVT-C", "2026-11-18T12:00:00+00:00", version=1)
    )
    assert decision.status is ApplyStatus.CONFLICT
    assert "stale" in decision.reason


def test_version_gap_is_detected() -> None:
    journal = ReplayJournal()
    journal.apply(_event("SYN-EVT-A", "2026-11-18T10:00:00+00:00", version=1))
    decision = journal.apply(
        _event("SYN-EVT-B", "2026-11-18T11:00:00+00:00", version=3)
    )
    assert decision.status is ApplyStatus.CONFLICT
    assert "gap" in decision.reason


def test_tenant_scoped_aggregate_keys_are_independent() -> None:
    journal = ReplayJournal()
    first = journal.apply(
        _event(
            "SYN-EVT-A",
            "2026-11-18T10:00:00+00:00",
            tenant_id="SYN-LAB-0001",
            aggregate_id="SYN-AGG-SHARED",
        )
    )
    second = journal.apply(
        _event(
            "SYN-EVT-B",
            "2026-11-18T11:00:00+00:00",
            tenant_id="SYN-LAB-9999",
            aggregate_id="SYN-AGG-SHARED",
        )
    )
    assert first.status is second.status is ApplyStatus.APPLIED


def test_conflict_does_not_mutate_journal() -> None:
    journal = ReplayJournal()
    accepted = journal.apply(_event("SYN-EVT-A", "2026-11-18T10:00:00+00:00"))
    conflict = journal.apply(_event("SYN-EVT-B", "2026-11-18T11:00:00+00:00"))
    assert accepted.status is ApplyStatus.APPLIED
    assert conflict.status is ApplyStatus.CONFLICT
    assert journal.applied_event_ids == frozenset({"SYN-EVT-A"})
    assert journal.version_of(aggregate_key(_event("SYN-EVT-A", "x"))) == 1


def test_aggregate_key_format_includes_tenant_and_aggregate() -> None:
    key = aggregate_key(_event("SYN-EVT-A", "2026-11-18T10:00:00+00:00"))
    assert key == f"{DEFAULT_SYNTHETIC_TENANT}/observation/SYN-AGG-0001"
