"""Tests for the single-patient synthetic medical-record aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.health_core.clinical import (
    ClinicalContext,
    MedicalRecordView,
    RecordScope,
)
from app.health_core.common import (
    AggregateType,
    EventType,
    ForbiddenSyntheticOperationError,
    TenantMismatchError,
    UnknownPatientError,
)


@pytest.fixture
def populated_context(synthetic_registry, synthetic_tenant, synthetic_patient):
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
    encounter = context.encounters.create(
        tenant_id=synthetic_tenant,
        idempotency_key="SYN-ENC-0001",
        patient_ref=synthetic_patient.ref,
        practitioner_id="SYN-PRC-0001",
        facility_id="SYN-FAC-0001",
        reason="synthetic consultation",
    )
    context.diagnoses.record(
        tenant_id=synthetic_tenant,
        idempotency_key="SYN-DIA-0001",
        patient_ref=synthetic_patient.ref,
        encounter_id=encounter.encounter_id,
        code="J18.9",
        description="synthetic pneumonia",
        severity="moderate",
    )
    context.observations.record(
        tenant_id=synthetic_tenant,
        idempotency_key="SYN-OBS-0001",
        patient_ref=synthetic_patient.ref,
        encounter_id=encounter.encounter_id,
        code="8867-4",
        display="synthetic heart rate",
        value=78,
        unit="bpm",
        recorded_at=datetime(2026, 1, 2, 9, 0, tzinfo=UTC),
    )
    context.encounters.add_note(
        tenant_id=synthetic_tenant,
        encounter_id=encounter.encounter_id,
        idempotency_key="SYN-NOT-0001",
        author_practitioner_id="SYN-PRC-0001",
        text="synthetic assessment",
    )
    return context


def test_aggregate_collects_all_clinical_data_for_one_patient(
    populated_context, synthetic_tenant, synthetic_patient
):
    scope = RecordScope(tenant_id=synthetic_tenant, patient_refs=(synthetic_patient.ref,))
    view = populated_context.medical_records.aggregate(scope=scope)
    assert isinstance(view, MedicalRecordView)
    assert view.patient_ref == synthetic_patient.ref
    assert view.tenant_id == synthetic_tenant
    assert len(view.encounters) == 1
    assert len(view.diagnoses) == 1
    assert len(view.observations) == 1
    assert len(view.notes) == 1
    assert view.item_count == 4
    assert view.encounters[0].patient_ref == synthetic_patient.ref
    assert view.notes[0].patient_ref == synthetic_patient.ref


def test_open_emits_medical_record_opened_event(
    populated_context, synthetic_tenant, synthetic_patient
):
    scope = RecordScope(tenant_id=synthetic_tenant, patient_refs=(synthetic_patient.ref,))
    view = populated_context.medical_records.open(scope=scope)
    events = [
        event
        for event in populated_context.event_history()
        if event.event_type == EventType.MEDICAL_RECORD_OPENED
    ]
    assert len(events) == 1
    assert events[0].aggregate_type == AggregateType.MEDICAL_RECORD
    assert events[0].aggregate_id == synthetic_patient.ref
    assert events[0].tenant_id == synthetic_tenant
    assert events[0].payload["encounter_count"] == 1
    assert view.item_count == 4


def test_multi_patient_scope_is_refused(
    populated_context, synthetic_registry, synthetic_tenant, synthetic_patient
):
    other = synthetic_registry.register_patient(tenant_id=synthetic_tenant, label="fixture-beta")
    scope = RecordScope(
        tenant_id=synthetic_tenant,
        patient_refs=(synthetic_patient.ref, other.ref),
    )
    with pytest.raises(ForbiddenSyntheticOperationError) as exc:
        populated_context.medical_records.aggregate(scope=scope)
    assert exc.value.code == "FORBIDDEN_SYNTHETIC_OPERATION"


def test_cross_tenant_scope_is_refused(populated_context, synthetic_tenant, synthetic_patient):
    scope = RecordScope(
        tenant_id="SYN-LAB-9999",
        patient_refs=(synthetic_patient.ref,),
    )
    with pytest.raises(TenantMismatchError):
        populated_context.medical_records.aggregate(scope=scope)
    assert synthetic_tenant != "SYN-LAB-9999"


def test_unknown_patient_scope_is_refused(populated_context, synthetic_tenant):
    scope = RecordScope(tenant_id=synthetic_tenant, patient_refs=("SYN-PAT-ABSENT",))
    with pytest.raises(UnknownPatientError):
        populated_context.medical_records.aggregate(scope=scope)


def test_empty_scope_is_refused(populated_context, synthetic_tenant):
    scope = RecordScope(tenant_id=synthetic_tenant, patient_refs=())
    with pytest.raises(ForbiddenSyntheticOperationError):
        populated_context.medical_records.open(scope=scope)
