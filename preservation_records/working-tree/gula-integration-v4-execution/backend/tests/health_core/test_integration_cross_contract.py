"""End-to-end synthetic integration flow across the readiness contracts."""

from __future__ import annotations

from dataclasses import replace

from app.health_core.common import AggregateType, DomainEvent, EventType
from app.health_core.identity import PatientRef, SyntheticPatientRegistry
from app.health_core.integration import (
    DEFAULT_BOUNDARIES,
    DEFAULT_SURFACE_ANNOTATIONS,
    ApplyStatus,
    ConflictCase,
    ConflictStrategy,
    InMemorySyntheticApiClient,
    OfflineOutbox,
    ReplayJournal,
    replay,
    resolve_conflict,
    validate_boundaries,
    validate_surfaces,
)


def test_fake_client_events_replay_through_offline_outbox() -> None:
    registry = SyntheticPatientRegistry()
    tenant = "SYN-LAB-0001"
    patient: PatientRef = registry.register_patient(tenant_id=tenant, label="flow")
    client = InMemorySyntheticApiClient(registry)
    client.create_lab_order(
        tenant_id=tenant, patient_ref=patient, data={"fixture": "order"}
    )
    client.create_lab_result(
        tenant_id=tenant, patient_ref=patient, data={"fixture": "result"}
    )

    outbox = OfflineOutbox()
    for event in client.events:
        outbox.enqueue(event)
    journal = ReplayJournal()
    decisions = replay(outbox, journal)
    assert len(decisions) == 2
    assert all(decision.status is ApplyStatus.APPLIED for decision in decisions)
    assert len(journal.applied_event_ids) == 2


def test_divergent_event_is_resolved_then_applied_as_next_version() -> None:
    tenant = "SYN-LAB-0001"
    first = DomainEvent(
        event_id="SYN-EVT-A",
        event_type=EventType.RESULT_RECORDED,
        aggregate_type=AggregateType.LAB_RESULT,
        aggregate_id="SYN-RES-0001",
        tenant_id=tenant,
        occurred_at="2026-11-18T10:00:00+00:00",
        version=1,
    )
    second = replace(
        first,
        event_id="SYN-EVT-B",
        occurred_at="2026-11-18T11:00:00+00:00",
        payload={"fixture": "b"},
    )
    outbox = OfflineOutbox()
    outbox.enqueue(first)
    outbox.enqueue(second)
    journal = ReplayJournal()
    decisions = replay(outbox, journal)
    assert [item.status for item in decisions] == [
        ApplyStatus.APPLIED,
        ApplyStatus.CONFLICT,
    ]

    case = ConflictCase(
        conflict_id="SYN-CONF-FLOW",
        aggregate_key=f"{tenant}/lab_result/SYN-RES-0001",
        tenant_id=tenant,
        events=(first, second),
        expected_version=2,
        observed_version=1,
    )
    decision = resolve_conflict(case, ConflictStrategy.KEEP_LAST_WITH_AUDIT)
    assert decision.accepted_event == second
    assert len(decision.audit) == 1
    accepted = decision.accepted_event
    assert accepted is not None
    assert journal.apply(replace(accepted, version=2)).status is ApplyStatus.APPLIED


def test_default_auth_and_accessibility_gates_pass_together() -> None:
    assert validate_boundaries(DEFAULT_BOUNDARIES).is_valid
    assert validate_surfaces(DEFAULT_SURFACE_ANNOTATIONS).is_valid
