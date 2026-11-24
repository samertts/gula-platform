"""Tests for synthetic diagnoses and clinical observations."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.health_core.clinical import ClinicalContext, DiagnosisStatus, Severity
from app.health_core.clinical.errors import ClinicalValidationError
from app.health_core.common import (
    AggregateType,
    DuplicateEntityError,
    EventType,
    ForbiddenSyntheticOperationError,
    InvalidStateTransitionError,
)


@pytest.fixture
def clinical_with_encounter(synthetic_registry, synthetic_tenant, synthetic_patient):
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
    return context, encounter


def _record_diagnosis(context, tenant_id, patient_ref, encounter_id, key="SYN-DIA-0001"):
    return context.diagnoses.record(
        tenant_id=tenant_id,
        idempotency_key=key,
        patient_ref=patient_ref,
        encounter_id=encounter_id,
        code="j18.9",
        description="synthetic pneumonia",
        severity=Severity.HIGH,
    )


def test_diagnosis_record_validates_code_and_emits_event(
    clinical_with_encounter, synthetic_tenant, synthetic_patient
):
    context, encounter = clinical_with_encounter
    diagnosis = _record_diagnosis(
        context, synthetic_tenant, synthetic_patient.ref, encounter.encounter_id
    )
    assert diagnosis.code == "J18.9"
    assert diagnosis.description == "synthetic pneumonia"
    assert diagnosis.severity is Severity.HIGH
    assert diagnosis.status is DiagnosisStatus.ACTIVE
    assert diagnosis.is_active() is True
    assert context.diagnoses.list_for_encounter(
        tenant_id=synthetic_tenant, encounter_id=encounter.encounter_id
    ) == (diagnosis,)
    events = [
        event
        for event in context.event_history()
        if event.event_type == EventType.DIAGNOSIS_RECORDED
    ]
    assert len(events) == 1
    assert events[0].aggregate_type == AggregateType.DIAGNOSIS
    assert events[0].aggregate_id == diagnosis.diagnosis_id
    assert events[0].payload["code"] == "J18.9"


def test_invalid_icd_code_is_rejected(clinical_with_encounter, synthetic_tenant, synthetic_patient):
    context, encounter = clinical_with_encounter
    with pytest.raises(ClinicalValidationError):
        context.diagnoses.record(
            tenant_id=synthetic_tenant,
            idempotency_key="SYN-DIA-0002",
            patient_ref=synthetic_patient.ref,
            encounter_id=encounter.encounter_id,
            code="NOT-A-CODE",
            description="synthetic finding",
            severity="low",
        )


def test_resolve_diagnosis_is_idempotent_and_emits_transition(
    clinical_with_encounter, synthetic_tenant, synthetic_patient
):
    context, encounter = clinical_with_encounter
    diagnosis = _record_diagnosis(
        context, synthetic_tenant, synthetic_patient.ref, encounter.encounter_id
    )
    kwargs = {
        "tenant_id": synthetic_tenant,
        "diagnosis_id": diagnosis.diagnosis_id,
        "idempotency_key": "SYN-TRN-0010",
    }
    resolved = context.diagnoses.resolve(**kwargs)
    replay = context.diagnoses.resolve(**kwargs)
    assert replay is resolved
    assert resolved.status is DiagnosisStatus.RESOLVED
    assert resolved.version == 2
    assert resolved.resolved_at is not None
    assert resolved.is_active() is False
    recorded = [
        event
        for event in context.event_history()
        if event.event_type == EventType.DIAGNOSIS_RECORDED
    ]
    resolved = [
        event
        for event in context.event_history()
        if event.event_type == EventType.DIAGNOSIS_RESOLVED
    ]
    assert len(recorded) == 1
    assert len(resolved) == 1
    assert resolved[0].payload["transition"] == "resolve"


def test_second_unkeyed_resolve_of_same_diagnosis_is_illegal(
    clinical_with_encounter, synthetic_tenant, synthetic_patient
):
    context, encounter = clinical_with_encounter
    diagnosis = _record_diagnosis(
        context, synthetic_tenant, synthetic_patient.ref, encounter.encounter_id
    )
    context.diagnoses.resolve(
        tenant_id=synthetic_tenant,
        diagnosis_id=diagnosis.diagnosis_id,
        idempotency_key="SYN-TRN-0011",
    )
    with pytest.raises(InvalidStateTransitionError):
        context.diagnoses.resolve(
            tenant_id=synthetic_tenant,
            diagnosis_id=diagnosis.diagnosis_id,
            idempotency_key="SYN-TRN-0012",
        )


def test_diagnosis_cannot_span_another_patients_encounter(
    clinical_with_encounter, synthetic_registry, synthetic_tenant, synthetic_patient
):
    context, encounter = clinical_with_encounter
    other = synthetic_registry.register_patient(tenant_id=synthetic_tenant, label="fixture-beta")
    with pytest.raises(ForbiddenSyntheticOperationError):
        context.diagnoses.record(
            tenant_id=synthetic_tenant,
            idempotency_key="SYN-DIA-0003",
            patient_ref=other.ref,
            encounter_id=encounter.encounter_id,
            code="J18.9",
            description="synthetic finding",
            severity="low",
        )
    assert synthetic_patient.ref != other.ref


def test_diagnosis_duplicate_key_conflict_is_rejected(
    clinical_with_encounter, synthetic_tenant, synthetic_patient
):
    context, encounter = clinical_with_encounter
    kwargs = {
        "tenant_id": synthetic_tenant,
        "idempotency_key": "SYN-DIA-0004",
        "patient_ref": synthetic_patient.ref,
        "encounter_id": encounter.encounter_id,
        "code": "J18.9",
        "description": "synthetic pneumonia",
        "severity": Severity.HIGH,
    }
    first = context.diagnoses.record(**kwargs)
    replay = context.diagnoses.record(**kwargs)
    assert replay is first
    with pytest.raises(DuplicateEntityError):
        context.diagnoses.record(**{**kwargs, "code": "A09.9"})


def _record_observation(
    context,
    tenant_id,
    patient_ref,
    encounter_id,
    key,
    moment,
    *,
    code="8867-4",
    value=72,
    unit="bpm",
):
    return context.observations.record(
        tenant_id=tenant_id,
        idempotency_key=key,
        patient_ref=patient_ref,
        encounter_id=encounter_id,
        code=code,
        display="synthetic heart rate",
        value=value,
        unit=unit,
        recorded_at=moment,
    )


def test_observation_record_validates_unit_and_emits_event(
    clinical_with_encounter, synthetic_tenant, synthetic_patient
):
    context, encounter = clinical_with_encounter
    observation = _record_observation(
        context,
        synthetic_tenant,
        synthetic_patient.ref,
        encounter.encounter_id,
        "SYN-OBS-0001",
        datetime(2026, 1, 2, 10, 0, tzinfo=UTC),
    )
    assert observation.code == "8867-4"
    assert observation.unit == "bpm"
    assert observation.value == 72.0
    events = [
        event
        for event in context.event_history()
        if event.event_type == EventType.OBSERVATION_RECORDED
    ]
    assert len(events) == 1
    assert events[0].aggregate_type == AggregateType.OBSERVATION
    assert events[0].aggregate_id == "SYN-OBS-0001"


def test_observation_validation_rejects_bad_code_unit_and_value(
    clinical_with_encounter, synthetic_tenant, synthetic_patient
):
    context, encounter = clinical_with_encounter
    moment = datetime(2026, 1, 2, 10, 0, tzinfo=UTC)
    with pytest.raises(ClinicalValidationError):
        _record_observation(
            context,
            synthetic_tenant,
            synthetic_patient.ref,
            encounter.encounter_id,
            "SYN-OBS-0002",
            moment,
            code="heart-rate",
        )
    with pytest.raises(ClinicalValidationError):
        _record_observation(
            context,
            synthetic_tenant,
            synthetic_patient.ref,
            encounter.encounter_id,
            "SYN-OBS-0003",
            moment,
            unit="kg",
        )
    with pytest.raises(ClinicalValidationError):
        _record_observation(
            context,
            synthetic_tenant,
            synthetic_patient.ref,
            encounter.encounter_id,
            "SYN-OBS-0004",
            moment,
            value=float("nan"),
        )
    with pytest.raises(ClinicalValidationError):
        _record_observation(
            context,
            synthetic_tenant,
            synthetic_patient.ref,
            encounter.encounter_id,
            "SYN-OBS-0005",
            datetime(2026, 1, 2, 10, 0),
        )


def test_observations_are_ordered_by_recorded_at_and_filterable(
    clinical_with_encounter, synthetic_tenant, synthetic_patient
):
    context, encounter = clinical_with_encounter
    late = _record_observation(
        context,
        synthetic_tenant,
        synthetic_patient.ref,
        encounter.encounter_id,
        "SYN-OBS-0010",
        datetime(2026, 1, 2, 12, 0, tzinfo=UTC),
    )
    early = _record_observation(
        context,
        synthetic_tenant,
        synthetic_patient.ref,
        encounter.encounter_id,
        "SYN-OBS-0011",
        datetime(2026, 1, 2, 8, 0, tzinfo=UTC),
        code="8310-5",
        value=37.2,
        unit="Cel",
    )
    ordered = context.observations.query(
        tenant_id=synthetic_tenant, patient_ref=synthetic_patient.ref
    )
    assert [item.observation_id for item in ordered] == [
        early.observation_id,
        late.observation_id,
    ]
    filtered = context.observations.query(
        tenant_id=synthetic_tenant,
        patient_ref=synthetic_patient.ref,
        encounter_id=encounter.encounter_id,
        code="8310-5",
    )
    assert filtered == (early,)


def test_observation_cannot_span_another_patients_encounter(
    clinical_with_encounter, synthetic_registry, synthetic_tenant
):
    context, encounter = clinical_with_encounter
    other = synthetic_registry.register_patient(tenant_id=synthetic_tenant, label="fixture-gamma")
    with pytest.raises(ForbiddenSyntheticOperationError):
        _record_observation(
            context,
            synthetic_tenant,
            other.ref,
            encounter.encounter_id,
            "SYN-OBS-0020",
            datetime(2026, 1, 2, 9, 0, tzinfo=UTC),
        )
