"""Cross-module conformance: real WS-A/WS-B output validated by WS-C contracts.

This is the integration test that the per-workstream suites cannot provide:
each workstream tested its own module in isolation. Here, entities and domain
events produced by the *real* clinical and lab services are fed into the *real*
contract validators. A divergence in event vocabulary, payload keys or
identifier shape fails this module.

Synthetic data only: no DB, no MPI, no network, no production activation.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.health_core.clinical import (
    ClinicalContext,
    Encounter,
    EncounterStatus,
    RecordScope,
)
from app.health_core.clinical.services import TRANSITION_EVENTS
from app.health_core.common import DomainEvent, EventType
from app.health_core.contracts import (
    ERROR_CATALOGUE,
    ERROR_RESPONSE_BODIES,
    EVENT_CATALOGUE,
    FHIR_ISSUE_CODE_BY_ERROR_CODE,
    IDEMPOTENCY_POLICIES,
    LabResultCreateRequest,
    LabResultResponse,
    SyntheticRef,
    validate_domain_event,
)
from app.health_core.contracts.models import EncounterResponse
from app.health_core.identity import SyntheticPatientRegistry
from app.health_core.lab import (
    LabResult,
    LabWorkflowService,
    Priority,
    SpecimenStatus,
    VerificationDecision,
)
from app.health_core.lab import models as lab_models
from pydantic import TypeAdapter

TENANT = "SYN-LAB-0001"
PRACTITIONER = "SYN-PRC-0001"
FACILITY = "SYN-FAC-0001"
ACTOR = "SYN-ACT-00000001"
REVIEWER = "SYN-REV-00000001"


class _Slices:
    """Real artefacts produced by the two domain workstreams."""

    def __init__(self) -> None:
        self.registry = SyntheticPatientRegistry()
        self.patient = self.registry.register_patient(tenant_id=TENANT, label="conformance")
        self.clinical_events: list[DomainEvent] = []
        self.lab_events: list[DomainEvent] = []
        self.encounter: Encounter
        self.result: LabResult
        self._build_clinical()
        self._build_lab()

    def _build_clinical(self) -> None:
        clinical = ClinicalContext(identity=self.registry)
        clinical.practitioners.register(
            tenant_id=TENANT,
            idempotency_key="SYN-PRC-0001",
            role="physician",
            qualification="MBBS",
        )
        org = clinical.organizations.register_organization(
            tenant_id=TENANT,
            idempotency_key="SYN-ORG-0001",
            label="synthetic-hospital",
        )
        clinical.organizations.register_facility(
            tenant_id=TENANT,
            idempotency_key=FACILITY,
            organization_id=org.organization_id,
            label="synthetic-ward",
            facility_type="hospital",
        )
        self.encounter = clinical.encounters.create(
            tenant_id=TENANT,
            idempotency_key="SYN-ENC-0001",
            patient_ref=self.patient.ref,
            practitioner_id=PRACTITIONER,
            facility_id=FACILITY,
            reason="conformance check",
        )
        self.encounter = clinical.encounters.transition(
            tenant_id=TENANT,
            encounter_id=self.encounter.encounter_id,
            to_status=EncounterStatus.IN_PROGRESS,
            idempotency_key="SYN-TRN-0001",
        )
        clinical.encounters.add_note(
            tenant_id=TENANT,
            encounter_id=self.encounter.encounter_id,
            idempotency_key="SYN-NOT-0001",
            author_practitioner_id=PRACTITIONER,
            text="conformance note",
        )
        clinical.diagnoses.record(
            tenant_id=TENANT,
            idempotency_key="SYN-DIA-0001",
            patient_ref=self.patient.ref,
            encounter_id=self.encounter.encounter_id,
            code="E11.9",
            description="synthetic diabetes",
            severity="moderate",
        )
        clinical.observations.record(
            tenant_id=TENANT,
            idempotency_key="SYN-OBS-0001",
            patient_ref=self.patient.ref,
            encounter_id=self.encounter.encounter_id,
            code="8867-4",
            display="Heart rate",
            value=78.0,
            unit="bpm",
            recorded_at=datetime.now(UTC),
        )
        clinical.medical_records.open(
            scope=RecordScope(tenant_id=TENANT, patient_refs=(self.patient.ref,))
        )
        self.clinical_events = list(clinical.event_history())

    def _build_lab(self) -> None:
        lab = LabWorkflowService(identity=self.registry)
        order = lab.place_order(
            tenant_id=TENANT,
            patient_ref=self.patient.ref,
            test_codes=["GLU", "WBC"],
            idempotency_key="SYN-KEY-0001",
            priority=Priority.URGENT,
            actor_id=ACTOR,
        )
        specimen = lab.register_specimen(
            tenant_id=TENANT,
            order_id=order.order_id,
            barcode="SYN-BAR-00000001",
            actor_id=ACTOR,
        )
        for target in (SpecimenStatus.COLLECTED, SpecimenStatus.RECEIVED):
            specimen = lab.transition_specimen(
                tenant_id=TENANT,
                specimen_id=specimen.specimen_id,
                to_status=target,
                actor_id=ACTOR,
            )
        execution = lab.enter_testing(
            tenant_id=TENANT, specimen_id=specimen.specimen_id, actor_id=ACTOR
        )
        lab.complete_testing(
            tenant_id=TENANT, execution_id=execution.execution_id, actor_id=ACTOR
        )
        self.result = lab.record_result(
            tenant_id=TENANT,
            order_id=order.order_id,
            specimen_id=specimen.specimen_id,
            patient_ref=self.patient.ref,
            test_code="GLU",
            value=92.0,
            unit="mg/dL",
            idempotency_key="SYN-KEY-0002",
            actor_id=ACTOR,
        )
        lab.verify_result(
            tenant_id=TENANT,
            result_id=self.result.result_id,
            reviewer_id=REVIEWER,
            decision=VerificationDecision.VERIFIED,
            idempotency_key="SYN-KEY-0003",
        )
        self.lab_events = list(lab.all_events(tenant_id=TENANT))


@pytest.fixture(scope="module")
def slices() -> _Slices:
    return _Slices()


def test_real_clinical_events_conform_to_ws_c_catalogue(slices: _Slices) -> None:
    assert len(slices.clinical_events) == 8
    for event in slices.clinical_events:
        validate_domain_event(event)


def test_real_lab_events_conform_to_ws_c_catalogue(slices: _Slices) -> None:
    assert len(slices.lab_events) == 11
    for event in slices.lab_events:
        validate_domain_event(event)


def test_every_emitted_event_type_is_in_shared_vocabulary(slices: _Slices) -> None:
    for event in (*slices.clinical_events, *slices.lab_events):
        assert EventType(event.event_type) is not None


def test_every_emitted_event_type_has_a_catalogue_definition(slices: _Slices) -> None:
    for event in (*slices.clinical_events, *slices.lab_events):
        assert EventType(event.event_type) in EVENT_CATALOGUE


def test_workstream_local_event_constants_alias_shared_vocabulary() -> None:
    """Guard the single source of truth: no workstream-local event strings."""
    assert EventType.SPECIMEN_IN_TESTING.value == lab_models.SPECIMEN_IN_TESTING_EVENT
    assert EventType.SPECIMEN_FINAL.value == lab_models.SPECIMEN_FINAL_EVENT
    assert EventType.TEST_ENTERED.value == lab_models.TEST_ENTERED_EVENT
    assert EventType.TEST_COMPLETED.value == lab_models.TEST_COMPLETED_EVENT
    assert EventType.VERIFICATION_PENDING.value == lab_models.VERIFICATION_PENDING_EVENT
    assert (
        EventType.RESULT_VERIFICATION_REJECTED.value
        == lab_models.RESULT_VERIFICATION_REJECTED_EVENT
    )


def test_real_entity_and_tenant_ids_satisfy_ws_c_synthetic_ref(slices: _Slices) -> None:
    adapter: TypeAdapter[str] = TypeAdapter(SyntheticRef)
    real_refs = (
        slices.patient.ref,
        TENANT,
        slices.encounter.encounter_id,
        slices.result.result_id,
        slices.result.order_id,
        slices.result.specimen_id,
    )
    for ref in real_refs:
        assert adapter.validate_python(ref) == ref


def test_real_encounter_fits_ws_c_response_model(slices: _Slices) -> None:
    response = EncounterResponse(
        ref=slices.encounter.encounter_id,
        tenant_id=slices.encounter.tenant_id,
        patient_ref=slices.encounter.patient_ref,
        practitioner_ref=slices.encounter.practitioner_id,
        facility_ref=slices.encounter.facility_id,
        reason=slices.encounter.reason,
        status=slices.encounter.status.value,
    )
    assert response.ref == slices.encounter.encounter_id
    assert response.tenant_id == TENANT


def test_real_lab_result_fits_ws_c_response_model(slices: _Slices) -> None:
    response = LabResultResponse(
        ref=slices.result.result_id,
        tenant_id=slices.result.tenant_id,
        order_ref=slices.result.order_id,
        specimen_ref=slices.result.specimen_id,
        test_code=slices.result.test_code,
        value_text=str(slices.result.value),
        unit=slices.result.unit,
        abnormal_flag=slices.result.critical_flag,
    )
    assert response.ref == slices.result.result_id
    assert response.order_ref == slices.result.order_id


def test_real_lab_result_fits_ws_c_request_model(slices: _Slices) -> None:
    request = LabResultCreateRequest(
        tenant_id=TENANT,
        order_ref=slices.result.order_id,
        specimen_ref=slices.result.specimen_id,
        test_code=slices.result.test_code,
        value_text=str(slices.result.value),
        unit=slices.result.unit,
    )
    assert request.specimen_ref == slices.result.specimen_id


def test_error_contract_documents_both_wire_bodies() -> None:
    bodies = {body.name: body for body in ERROR_RESPONSE_BODIES}
    assert set(bodies) == {"canonical_json", "fhir_operation_outcome"}
    assert bodies["canonical_json"].content_type == "application/json"
    assert "code" in bodies["canonical_json"].shape
    assert "detail_ar" in bodies["canonical_json"].shape
    assert bodies["fhir_operation_outcome"].content_type == "application/fhir+json"
    assert "resourceType=OperationOutcome" in bodies["fhir_operation_outcome"].shape


def test_fhir_issue_code_mapping_covers_every_shared_error_code() -> None:
    assert set(ERROR_CATALOGUE) <= set(FHIR_ISSUE_CODE_BY_ERROR_CODE)
    assert FHIR_ISSUE_CODE_BY_ERROR_CODE["DUPLICATE_ENTITY"] == "conflict"
    assert FHIR_ISSUE_CODE_BY_ERROR_CODE["UNKNOWN_PATIENT"] == "not-found"


def test_idempotency_contract_documents_both_policies() -> None:
    policies = {policy.name: policy for policy in IDEMPOTENCY_POLICIES}
    assert set(policies) == {"general", "clinical"}
    general = policies["general"]
    assert general.key_header_required is False
    assert general.max_key_length == 255
    clinical = policies["clinical"]
    assert clinical.key_header_required is True
    assert clinical.max_key_length == 128
    assert clinical.if_match_header == "If-Match"
    assert clinical.missing_if_match_status == 428
    assert clinical.stale_version_status == 409


def test_every_encounter_lifecycle_transition_emits_a_catalogue_valid_event() -> None:
    """F-01 regression: all six transition targets must emit catalogue-valid events.

    The previous conformance fixture only exercised PLANNED -> IN_PROGRESS, so the
    four richer lifecycle payloads (admit/transfer/discharge/cancel) were never
    validated and silently violated their own catalogue definitions.
    """
    registry = SyntheticPatientRegistry()
    patient = registry.register_patient(tenant_id=TENANT, label="lifecycle-conformance")
    clinical = ClinicalContext(identity=registry)
    clinical.practitioners.register(
        tenant_id=TENANT,
        idempotency_key=PRACTITIONER,
        role="physician",
        qualification="MBBS",
    )
    organization = clinical.organizations.register_organization(
        tenant_id=TENANT,
        idempotency_key="SYN-ORG-0001",
        label="synthetic-hospital",
    )
    clinical.organizations.register_facility(
        tenant_id=TENANT,
        idempotency_key=FACILITY,
        organization_id=organization.organization_id,
        label="synthetic-ward",
        facility_type="hospital",
    )
    transfer_facility = "SYN-FAC-0002"
    clinical.organizations.register_facility(
        tenant_id=TENANT,
        idempotency_key=transfer_facility,
        organization_id=organization.organization_id,
        label="synthetic-receiving-ward",
        facility_type="hospital",
    )

    encounter = clinical.encounters.create(
        tenant_id=TENANT,
        idempotency_key="SYN-ENC-0001",
        patient_ref=patient.ref,
        practitioner_id=PRACTITIONER,
        facility_id=FACILITY,
        reason="admitted for conformance",
    )
    # PLANNED -> IN_PROGRESS -> ADMITTED -> TRANSFERRED -> ADMITTED -> DISCHARGED
    # covers STARTED/ADMITTED/TRANSFERRED/DISCHARGED in one legal chain.
    for index, (target, kwargs) in enumerate(
        (
            (EncounterStatus.IN_PROGRESS, {}),
            (EncounterStatus.ADMITTED, {}),
            (
                EncounterStatus.TRANSFERRED,
                {"to_facility_ref": transfer_facility},
            ),
            (EncounterStatus.ADMITTED, {}),
            (EncounterStatus.DISCHARGED, {"disposition": "routine"}),
        ),
        start=1,
    ):
        encounter = clinical.encounters.transition(
            tenant_id=TENANT,
            encounter_id=encounter.encounter_id,
            to_status=target,
            idempotency_key=f"SYN-TRN-{index:04d}",
            **kwargs,
        )
    assert encounter.status is EncounterStatus.DISCHARGED

    # CANCELLED is terminal, so exercise it on a second encounter.
    cancelled_encounter = clinical.encounters.create(
        tenant_id=TENANT,
        idempotency_key="SYN-ENC-0002",
        patient_ref=patient.ref,
        practitioner_id=PRACTITIONER,
        facility_id=FACILITY,
        reason="cancelled before admission",
    )
    clinical.encounters.transition(
        tenant_id=TENANT,
        encounter_id=cancelled_encounter.encounter_id,
        to_status=EncounterStatus.CANCELLED,
        idempotency_key="SYN-TRN-0006",
    )

    transition_types = set(TRANSITION_EVENTS.values())
    emitted = [
        event
        for event in clinical.event_history()
        if EventType(event.event_type) in transition_types
    ]
    assert len(emitted) == 6
    assert {EventType(event.event_type) for event in emitted} == transition_types
    for event in emitted:
        validate_domain_event(event)  # fail closed on any catalogue violation

    admitted = next(e for e in emitted if EventType(e.event_type) is EventType.ENCOUNTER_ADMITTED)
    assert admitted.payload["facility_ref"] == FACILITY
    transferred = next(
        e for e in emitted if EventType(e.event_type) is EventType.ENCOUNTER_TRANSFERRED
    )
    assert transferred.payload["from_facility_ref"] == FACILITY
    assert transferred.payload["to_facility_ref"] == transfer_facility
    discharged = next(
        e for e in emitted if EventType(e.event_type) is EventType.ENCOUNTER_DISCHARGED
    )
    assert discharged.payload["disposition"] == "routine"
    cancelled = next(
        e for e in emitted if EventType(e.event_type) is EventType.ENCOUNTER_CANCELLED
    )
    assert cancelled.payload["reason"] == "cancelled before admission"
