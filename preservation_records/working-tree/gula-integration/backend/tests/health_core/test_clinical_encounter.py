"""Tests for the synthetic encounter lifecycle and clinical notes."""

from __future__ import annotations

import pytest
from app.health_core.clinical import ClinicalContext, EncounterStatus
from app.health_core.clinical.errors import ClinicalValidationError
from app.health_core.common import (
    AggregateType,
    DuplicateEntityError,
    EventType,
    InvalidStateTransitionError,
    TenantMismatchError,
    UnknownPatientError,
)


@pytest.fixture
def clinical(synthetic_registry, synthetic_tenant):
    context = ClinicalContext(identity=synthetic_registry)
    context.practitioners.register(
        tenant_id=synthetic_tenant,
        idempotency_key="SYN-PRC-0001",
        role="physician",
        qualification="MBBS",
    )
    organization = context.organizations.register_organization(
        tenant_id=synthetic_tenant,
        idempotency_key="SYN-ORG-0001",
        label="synthetic-hospital",
    )
    context.organizations.register_facility(
        tenant_id=synthetic_tenant,
        idempotency_key="SYN-FAC-0001",
        organization_id=organization.organization_id,
        label="synthetic-ward",
        facility_type="hospital",
    )
    return context


def _create(context, tenant_id, patient_ref, key="SYN-ENC-0001"):
    return context.encounters.create(
        tenant_id=tenant_id,
        idempotency_key=key,
        patient_ref=patient_ref,
        practitioner_id="SYN-PRC-0001",
        facility_id="SYN-FAC-0001",
        reason="synthetic consultation",
    )


def test_create_starts_planned_and_emits_created_event(
    clinical, synthetic_tenant, synthetic_patient
):
    encounter = _create(clinical, synthetic_tenant, synthetic_patient.ref)
    assert encounter.status is EncounterStatus.PLANNED
    assert encounter.version == 1
    assert encounter.patient_ref == synthetic_patient.ref
    assert encounter.facility_id == "SYN-FAC-0001"
    assert encounter.is_open() is True

    events = clinical.event_history()
    create_events = [event for event in events if event.event_type == EventType.ENCOUNTER_CREATED]
    assert len(create_events) == 1
    assert create_events[0].aggregate_type == AggregateType.ENCOUNTER
    assert create_events[0].aggregate_id == encounter.encounter_id
    assert create_events[0].tenant_id == synthetic_tenant
    assert create_events[0].payload["patient_ref"] == synthetic_patient.ref


def test_legal_lifecycle_chain_and_event_order(clinical, synthetic_tenant, synthetic_patient):
    encounter = _create(clinical, synthetic_tenant, synthetic_patient.ref)
    encounter = clinical.encounters.transition(
        tenant_id=synthetic_tenant,
        encounter_id=encounter.encounter_id,
        to_status=EncounterStatus.IN_PROGRESS,
        idempotency_key="SYN-TRN-0001",
    )
    encounter = clinical.encounters.transition(
        tenant_id=synthetic_tenant,
        encounter_id=encounter.encounter_id,
        to_status="admitted",
        idempotency_key="SYN-TRN-0002",
    )
    encounter = clinical.encounters.transition(
        tenant_id=synthetic_tenant,
        encounter_id=encounter.encounter_id,
        to_status=EncounterStatus.DISCHARGED,
        idempotency_key="SYN-TRN-0003",
    )
    assert encounter.status is EncounterStatus.DISCHARGED
    assert encounter.version == 4
    assert encounter.is_open() is False

    lifecycle = [
        event.event_type
        for event in clinical.event_history()
        if event.event_type
        in {
            item.value
            for item in (
                EventType.ENCOUNTER_CREATED,
                EventType.ENCOUNTER_STARTED,
                EventType.ENCOUNTER_ADMITTED,
                EventType.ENCOUNTER_DISCHARGED,
            )
        }
    ]
    assert lifecycle == [
        EventType.ENCOUNTER_CREATED,
        EventType.ENCOUNTER_STARTED,
        EventType.ENCOUNTER_ADMITTED,
        EventType.ENCOUNTER_DISCHARGED,
    ]
    transition_events = [
        event for event in clinical.event_history() if event.payload.get("transition")
    ]
    assert [event.payload["to_status"] for event in transition_events] == [
        EncounterStatus.IN_PROGRESS.value,
        EncounterStatus.ADMITTED.value,
        EncounterStatus.DISCHARGED.value,
    ]


def test_illegal_transition_is_refused_without_changing_state(
    clinical, synthetic_tenant, synthetic_patient
):
    encounter = _create(clinical, synthetic_tenant, synthetic_patient.ref)
    with pytest.raises(InvalidStateTransitionError) as exc:
        clinical.encounters.transition(
            tenant_id=synthetic_tenant,
            encounter_id=encounter.encounter_id,
            to_status=EncounterStatus.DISCHARGED,
            idempotency_key="SYN-TRN-0004",
        )
    assert exc.value.code == "INVALID_STATE_TRANSITION"
    assert exc.value.details["from_status"] == EncounterStatus.PLANNED.value
    current = clinical.encounters.get_encounter(
        tenant_id=synthetic_tenant, encounter_id=encounter.encounter_id
    )
    assert current == encounter
    assert len(clinical.event_history()) == 3


def test_create_with_unknown_patient_fails_closed(clinical, synthetic_tenant):
    with pytest.raises(UnknownPatientError):
        _create(clinical, synthetic_tenant, "SYN-PAT-ABSENT")


def test_create_with_cross_tenant_patient_fails_closed(
    clinical, synthetic_tenant, synthetic_patient
):
    with pytest.raises(TenantMismatchError):
        _create(clinical, "SYN-LAB-9999", synthetic_patient.ref)


def test_cross_tenant_encounter_lookup_is_refused(clinical, synthetic_tenant, synthetic_patient):
    encounter = _create(clinical, synthetic_tenant, synthetic_patient.ref)
    with pytest.raises(TenantMismatchError):
        clinical.encounters.get_encounter(
            tenant_id="SYN-LAB-9999", encounter_id=encounter.encounter_id
        )


def test_create_replay_and_conflict(clinical, synthetic_tenant, synthetic_patient):
    kwargs = {
        "tenant_id": synthetic_tenant,
        "idempotency_key": "SYN-ENC-0002",
        "patient_ref": synthetic_patient.ref,
        "practitioner_id": "SYN-PRC-0001",
        "facility_id": "SYN-FAC-0001",
        "reason": "synthetic consultation",
    }
    first = clinical.encounters.create(**kwargs)
    replay = clinical.encounters.create(**kwargs)
    assert replay is first
    with pytest.raises(DuplicateEntityError):
        clinical.encounters.create(**{**kwargs, "reason": "different reason"})
    assert len(clinical.event_history()) == 3


def test_transition_replay_and_conflict(clinical, synthetic_tenant, synthetic_patient):
    encounter = _create(clinical, synthetic_tenant, synthetic_patient.ref)
    kwargs = {
        "tenant_id": synthetic_tenant,
        "encounter_id": encounter.encounter_id,
        "to_status": EncounterStatus.IN_PROGRESS,
        "idempotency_key": "SYN-TRN-0005",
    }
    first = clinical.encounters.transition(**kwargs)
    replay = clinical.encounters.transition(**kwargs)
    assert replay is first
    with pytest.raises(DuplicateEntityError):
        clinical.encounters.transition(**{**kwargs, "to_status": EncounterStatus.ADMITTED})
    assert first.version == 2


def test_notes_are_scoped_to_encounter_and_emit_note_added(
    clinical, synthetic_tenant, synthetic_patient
):
    encounter = _create(clinical, synthetic_tenant, synthetic_patient.ref)
    note = clinical.encounters.add_note(
        tenant_id=synthetic_tenant,
        encounter_id=encounter.encounter_id,
        idempotency_key="SYN-NOT-0001",
        author_practitioner_id="SYN-PRC-0001",
        text="synthetic progress note",
    )
    assert note.patient_ref == synthetic_patient.ref
    assert note.encounter_id == encounter.encounter_id
    assert clinical.encounters.notes_for_encounter(
        tenant_id=synthetic_tenant, encounter_id=encounter.encounter_id
    ) == (note,)
    assert clinical.encounters.notes_for_patient(
        tenant_id=synthetic_tenant, patient_ref=synthetic_patient.ref
    ) == (note,)
    note_events = [
        event for event in clinical.event_history() if event.event_type == EventType.NOTE_ADDED
    ]
    assert len(note_events) == 1
    assert note_events[0].aggregate_type == AggregateType.ENCOUNTER
    assert note_events[0].aggregate_id == encounter.encounter_id


def test_encounter_with_inactive_practitioner_is_rejected(
    clinical, synthetic_tenant, synthetic_patient
):
    clinical.practitioners.register(
        tenant_id=synthetic_tenant,
        idempotency_key="SYN-PRC-0002",
        role="nurse",
        qualification="BSc Nursing",
        active=False,
    )
    with pytest.raises(ClinicalValidationError):
        clinical.encounters.create(
            tenant_id=synthetic_tenant,
            idempotency_key="SYN-ENC-0003",
            patient_ref=synthetic_patient.ref,
            practitioner_id="SYN-PRC-0002",
            facility_id="SYN-FAC-0001",
            reason="synthetic consultation",
        )
