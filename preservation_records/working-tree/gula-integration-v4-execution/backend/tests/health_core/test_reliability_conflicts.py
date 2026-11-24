"""Isolated offline-sync conflict disposition tests with full audit accounting."""

from __future__ import annotations

from dataclasses import replace

import pytest
from app.health_core.common import AggregateType, DomainEvent, EventType
from app.health_core.common.errors import InvalidSyntheticReferenceError
from app.health_core.reliability import (
    ConflictAccountingError,
    DispositionReason,
    ResolutionLedger,
    SyncCandidate,
    SyncOutcome,
    SyncPolicy,
    assert_full_accounting,
    make_candidate,
    resolve_sync_conflict,
)

RECORDED_AT = "2026-01-01T00:00:00+00:00"
TENANT = "SYN-LAB-0001"
RESOLVER = "SYN-NODE-RESOLVER"


def _event(event_id: str, version: int, occurred_at: str) -> DomainEvent:
    return DomainEvent(
        event_id=event_id,
        event_type=EventType.RESULT_RECORDED,
        aggregate_type=AggregateType.LAB_RESULT,
        aggregate_id="SYN-RES-000001",
        tenant_id=TENANT,
        occurred_at=occurred_at,
        version=version,
        payload={"event_id": event_id, "version": version},
    )


def _candidates() -> tuple[SyncCandidate, ...]:
    early = _event("SYN-EVT-000001", 1, "2026-01-01T10:00:00+00:00")
    late_low = _event("SYN-EVT-000002", 1, "2026-01-01T11:00:00+00:00")
    late_high = _event("SYN-EVT-000003", 3, "2026-01-01T12:00:00+00:00")
    return (
        make_candidate(candidate_id="SYN-CND-000001", event=early, arrival_index=3,
                       source_node="SYN-NODE-000001"),
        make_candidate(candidate_id="SYN-CND-000002", event=late_low, arrival_index=1,
                       source_node="SYN-NODE-000002"),
        make_candidate(candidate_id="SYN-CND-000003", event=late_high, arrival_index=2,
                       source_node="SYN-NODE-000003"),
    )


def _resolve(policy: SyncPolicy) -> ResolutionLedger:
    return resolve_sync_conflict(
        _candidates(), policy, recorded_at=RECORDED_AT, resolver_id=RESOLVER
    )


def test_quarantine_all_records_an_explicit_disposition_for_every_candidate() -> None:
    ledger = _resolve(SyncPolicy.QUARANTINE_ALL)
    assert ledger.winner_candidate_id is None
    assert {item.outcome for item in ledger.dispositions} == {SyncOutcome.QUARANTINED}
    assert {item.reason for item in ledger.dispositions} == {
        DispositionReason.QUARANTINED_BY_POLICY
    }
    assert len(ledger.audit) == 3
    assert ledger.verify_audit().ok


def test_first_writer_wins_by_arrival_index() -> None:
    ledger = _resolve(SyncPolicy.FIRST_WRITER_WINS)
    assert ledger.winner_candidate_id == "SYN-CND-000002"
    winner = next(item for item in ledger.dispositions if item.candidate_id == ledger.winner_candidate_id)
    assert winner.outcome is SyncOutcome.ADOPTED
    assert winner.reason is DispositionReason.ADOPTED_BY_POLICY
    assert [item.outcome for item in ledger.dispositions].count(SyncOutcome.QUARANTINED) == 2
    assert all(item.reason is DispositionReason.LOST_TO_WINNER for item in ledger.dispositions
               if item.outcome is SyncOutcome.QUARANTINED)


def test_highest_version_and_latest_arrival_policies_differ_explicitly() -> None:
    by_version = _resolve(SyncPolicy.HIGHEST_VERSION_WINS)
    by_arrival = _resolve(SyncPolicy.LATEST_ARRIVAL_WINS)
    assert by_version.winner_candidate_id == "SYN-CND-000003"
    assert by_arrival.winner_candidate_id == "SYN-CND-000001"
    assert by_version.ledger_id != by_arrival.ledger_id


def test_ledger_has_one_chained_audit_record_per_candidate() -> None:
    ledger = _resolve(SyncPolicy.HIGHEST_VERSION_WINS)
    assert len(ledger.dispositions) == 3
    assert {item.audit_sequence for item in ledger.dispositions} == {1, 2, 3}
    assert {record.subject_id for record in ledger.audit} == {
        "SYN-CND-000001",
        "SYN-CND-000002",
        "SYN-CND-000003",
    }
    assert ledger.audit_head == ledger.audit[-1].record_hash
    assert ledger.verify_audit().verified_count == 3
    assert_full_accounting(ledger)


def test_missing_disposition_fails_accounting() -> None:
    ledger = _resolve(SyncPolicy.FIRST_WRITER_WINS)
    incomplete = replace(ledger, dispositions=ledger.dispositions[:-1])
    with pytest.raises(ConflictAccountingError):
        assert_full_accounting(incomplete)
    orphan_audit = replace(ledger, audit=ledger.audit[:-1])
    with pytest.raises(ConflictAccountingError):
        assert_full_accounting(orphan_audit)


def test_tampered_audit_chain_fails_accounting() -> None:
    ledger = _resolve(SyncPolicy.QUARANTINE_ALL)
    altered = replace(ledger.audit[1], summary="tampered_summary")
    tampered = replace(ledger, audit=(ledger.audit[0], altered, *ledger.audit[2:]))
    with pytest.raises(ConflictAccountingError):
        assert_full_accounting(tampered)


def test_resolution_is_deterministic_regardless_of_input_order() -> None:
    candidates = _candidates()
    forward = resolve_sync_conflict(
        candidates, SyncPolicy.HIGHEST_VERSION_WINS, recorded_at=RECORDED_AT, resolver_id=RESOLVER
    )
    reversed_order = resolve_sync_conflict(
        tuple(reversed(candidates)), SyncPolicy.HIGHEST_VERSION_WINS,
        recorded_at=RECORDED_AT, resolver_id=RESOLVER,
    )
    assert forward == reversed_order


def test_invalid_candidate_sets_are_rejected() -> None:
    with pytest.raises(ConflictAccountingError):
        resolve_sync_conflict((), SyncPolicy.QUARANTINE_ALL, recorded_at=RECORDED_AT,
                              resolver_id=RESOLVER)
    candidate = make_candidate(
        candidate_id="SYN-CND-000009", event=_event("SYN-EVT-000009", 1, RECORDED_AT),
        arrival_index=1, source_node="SYN-NODE-000009",
    )
    with pytest.raises(ConflictAccountingError):
        resolve_sync_conflict((candidate, candidate), SyncPolicy.QUARANTINE_ALL,
                              recorded_at=RECORDED_AT, resolver_id=RESOLVER)
    with pytest.raises(InvalidSyntheticReferenceError):
        make_candidate(candidate_id="CND-000010", event=_event("SYN-EVT-000010", 1, RECORDED_AT),
                       arrival_index=1, source_node="SYN-NODE-000010")


def test_candidate_digest_mismatch_is_rejected() -> None:
    candidate = make_candidate(
        candidate_id="SYN-CND-000011", event=_event("SYN-EVT-000011", 1, RECORDED_AT),
        arrival_index=1, source_node="SYN-NODE-000011",
    )
    with pytest.raises(ConflictAccountingError):
        replace(candidate, payload_digest="0" * 64)
