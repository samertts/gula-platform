"""Result validation, critical flags, amendments and verification provenance."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from app.health_core.common.errors import InvalidStateTransitionError
from app.health_core.common.event_types import AggregateType, EventType
from app.health_core.common.ids import new_synthetic_id
from app.health_core.identity.synthetic import SyntheticPatientRegistry
from app.health_core.lab import (
    LabWorkflowService,
    Priority,
    SpecimenStatus,
    VerificationDecision,
    VerificationStatus,
)
from app.health_core.lab.errors import InvalidResultError, LabWorkflowError, UnknownTestCodeError


@pytest.fixture
def service(synthetic_registry: SyntheticPatientRegistry) -> LabWorkflowService:
    return LabWorkflowService(identity=synthetic_registry)


@pytest.fixture
def actor() -> str:
    return new_synthetic_id("ACT")


def _ready_order_and_specimen(service, patient, tenant, actor, codes=("GLU",)):
    order = service.place_order(
        tenant_id=tenant,
        patient_ref=patient.ref,
        test_codes=list(codes),
        idempotency_key=new_synthetic_id("KEY"),
        priority=Priority.ROUTINE,
        actor_id=actor,
    )
    specimen = service.register_specimen(
        tenant_id=tenant,
        order_id=order.order_id,
        barcode=new_synthetic_id("BAR"),
        actor_id=actor,
    )
    for target in (SpecimenStatus.COLLECTED, SpecimenStatus.RECEIVED):
        specimen = service.transition_specimen(
            tenant_id=tenant,
            specimen_id=specimen.specimen_id,
            to_status=target,
            actor_id=actor,
        )
    return order, specimen


def _record(service, patient, tenant, order, specimen, actor, value=90.0, code="GLU", unit="mg/dL"):
    return service.record_result(
        tenant_id=tenant,
        order_id=order.order_id,
        specimen_id=specimen.specimen_id,
        patient_ref=patient.ref,
        test_code=code,
        value=value,
        unit=unit,
        idempotency_key=new_synthetic_id("KEY"),
        actor_id=actor,
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [(450.0, True), (30.0, True), (92.0, False), (70.0, False)],
)
def test_critical_flag_calculation(
    service, synthetic_patient, synthetic_tenant, actor, value, expected
):
    order, specimen = _ready_order_and_specimen(
        service, synthetic_patient, synthetic_tenant, actor
    )
    result = _record(
        service, synthetic_patient, synthetic_tenant, order, specimen, actor, value=value
    )
    assert result.critical_flag is expected
    assert result.reference_low == 70.0
    assert result.reference_high == 99.0


def test_unknown_test_code_rejected(service, synthetic_patient, synthetic_tenant, actor):
    order, specimen = _ready_order_and_specimen(
        service, synthetic_patient, synthetic_tenant, actor
    )
    with pytest.raises(UnknownTestCodeError):
        _record(
            service,
            synthetic_patient,
            synthetic_tenant,
            order,
            specimen,
            actor,
            code="NOT-IN-CATALOGUE",
        )


def test_unit_mismatch_rejected(service, synthetic_patient, synthetic_tenant, actor):
    order, specimen = _ready_order_and_specimen(
        service, synthetic_patient, synthetic_tenant, actor
    )
    with pytest.raises(InvalidResultError):
        _record(
            service,
            synthetic_patient,
            synthetic_tenant,
            order,
            specimen,
            actor,
            unit="mmol/L",
        )


def test_unordered_test_code_rejected(service, synthetic_patient, synthetic_tenant, actor):
    order, specimen = _ready_order_and_specimen(
        service, synthetic_patient, synthetic_tenant, actor
    )
    with pytest.raises(LabWorkflowError):
        _record(
            service,
            synthetic_patient,
            synthetic_tenant,
            order,
            specimen,
            actor,
            code="WBC",
            unit="10^3/uL",
        )


def test_non_finite_value_rejected(service, synthetic_patient, synthetic_tenant, actor):
    order, specimen = _ready_order_and_specimen(
        service, synthetic_patient, synthetic_tenant, actor
    )
    with pytest.raises(InvalidResultError):
        _record(
            service,
            synthetic_patient,
            synthetic_tenant,
            order,
            specimen,
            actor,
            value=float("nan"),
        )


def test_result_on_rejected_specimen_rejected(
    service, synthetic_patient, synthetic_tenant, actor
):
    order, specimen = _ready_order_and_specimen(
        service, synthetic_patient, synthetic_tenant, actor
    )
    service.transition_specimen(
        tenant_id=synthetic_tenant,
        specimen_id=specimen.specimen_id,
        to_status=SpecimenStatus.REJECTED,
        actor_id=actor,
        reason="contaminated",
    )
    with pytest.raises(InvalidStateTransitionError):
        _record(service, synthetic_patient, synthetic_tenant, order, specimen, actor)


def test_amendment_history_is_immutable_and_recomputes_critical(
    service, synthetic_patient, synthetic_tenant, actor
):
    order, specimen = _ready_order_and_specimen(
        service, synthetic_patient, synthetic_tenant, actor
    )
    original = _record(
        service, synthetic_patient, synthetic_tenant, order, specimen, actor, value=92.0
    )
    corrected = service.correct_result(
        tenant_id=synthetic_tenant,
        result_id=original.result_id,
        new_value=450.0,
        reason="transcription corrected after review",
        actor_id=actor,
    )
    assert corrected.version == 2
    assert corrected.value == 450.0
    assert corrected.critical_flag is True
    assert len(corrected.amendments) == 1
    amendment = corrected.amendments[0]
    assert amendment.previous_value == 92.0
    assert amendment.new_value == 450.0
    assert amendment.reason == "transcription corrected after review"
    assert amendment.actor_id == actor
    assert amendment.version == 2
    assert amendment.amendment_id.startswith("SYN-AMD-")
    assert original.value == 92.0
    assert original.amendments == ()
    assert service.get_result(
        tenant_id=synthetic_tenant, result_id=original.result_id
    ) == corrected

    trail = service.provenance(tenant_id=synthetic_tenant, aggregate_id=original.result_id)
    assert [event.event_type for event in trail] == [
        EventType.RESULT_RECORDED,
        EventType.RESULT_CORRECTED,
    ]
    assert all(event.aggregate_type == AggregateType.LAB_RESULT for event in trail)


def test_amendment_requires_reason(service, synthetic_patient, synthetic_tenant, actor):
    order, specimen = _ready_order_and_specimen(
        service, synthetic_patient, synthetic_tenant, actor
    )
    result = _record(service, synthetic_patient, synthetic_tenant, order, specimen, actor)
    with pytest.raises(LabWorkflowError):
        service.correct_result(
            tenant_id=synthetic_tenant,
            result_id=result.result_id,
            new_value=88.0,
            reason="  ",
            actor_id=actor,
        )


def test_verification_rejected_with_reason(
    service, synthetic_patient, synthetic_tenant, actor
):
    order, specimen = _ready_order_and_specimen(
        service, synthetic_patient, synthetic_tenant, actor
    )
    result = _record(service, synthetic_patient, synthetic_tenant, order, specimen, actor)
    reviewer = new_synthetic_id("REV")
    verification = service.verify_result(
        tenant_id=synthetic_tenant,
        result_id=result.result_id,
        reviewer_id=reviewer,
        decision=VerificationDecision.REJECTED,
        idempotency_key=new_synthetic_id("KEY"),
        reason="instrument drift suspected",
    )
    assert verification.status is VerificationStatus.REJECTED
    assert verification.reason == "instrument drift suspected"
    trail = service.provenance(
        tenant_id=synthetic_tenant, aggregate_id=verification.verification_id
    )
    assert [event.event_type for event in trail] == [
        "verification.pending",
        "result.verification_rejected",
    ]
    assert all(event.aggregate_type == AggregateType.VERIFICATION for event in trail)


def test_verification_pending_to_verified_to_rejected(
    service, synthetic_patient, synthetic_tenant, actor
):
    order, specimen = _ready_order_and_specimen(
        service, synthetic_patient, synthetic_tenant, actor
    )
    result = _record(service, synthetic_patient, synthetic_tenant, order, specimen, actor)
    reviewer = new_synthetic_id("REV")
    verified = service.verify_result(
        tenant_id=synthetic_tenant,
        result_id=result.result_id,
        reviewer_id=reviewer,
        decision=VerificationDecision.VERIFIED,
        idempotency_key=new_synthetic_id("KEY"),
    )
    assert verified.status is VerificationStatus.VERIFIED
    rejected = service.transition_verification(
        tenant_id=synthetic_tenant,
        verification_id=verified.verification_id,
        to_status=VerificationStatus.REJECTED,
        reviewer_id=reviewer,
        reason="later quality-control failure",
    )
    assert rejected.status is VerificationStatus.REJECTED
    trail = service.provenance(
        tenant_id=synthetic_tenant, aggregate_id=verified.verification_id
    )
    assert [event.event_type for event in trail] == [
        "verification.pending",
        EventType.RESULT_VERIFIED,
        "result.verification_rejected",
    ]


def test_illegal_verification_transition_rejected(
    service, synthetic_patient, synthetic_tenant, actor
):
    order, specimen = _ready_order_and_specimen(
        service, synthetic_patient, synthetic_tenant, actor
    )
    result = _record(service, synthetic_patient, synthetic_tenant, order, specimen, actor)
    reviewer = new_synthetic_id("REV")
    rejected = service.verify_result(
        tenant_id=synthetic_tenant,
        result_id=result.result_id,
        reviewer_id=reviewer,
        decision=VerificationDecision.REJECTED,
        idempotency_key=new_synthetic_id("KEY"),
        reason="blocked",
    )
    with pytest.raises(InvalidStateTransitionError):
        service.transition_verification(
            tenant_id=synthetic_tenant,
            verification_id=rejected.verification_id,
            to_status=VerificationStatus.VERIFIED,
            reviewer_id=reviewer,
        )


def test_verification_reviewer_mismatch_rejected(
    service, synthetic_patient, synthetic_tenant, actor
):
    order, specimen = _ready_order_and_specimen(
        service, synthetic_patient, synthetic_tenant, actor
    )
    result = _record(service, synthetic_patient, synthetic_tenant, order, specimen, actor)
    verification = service.verify_result(
        tenant_id=synthetic_tenant,
        result_id=result.result_id,
        reviewer_id=new_synthetic_id("REV"),
        decision=VerificationDecision.VERIFIED,
        idempotency_key=new_synthetic_id("KEY"),
    )
    with pytest.raises(LabWorkflowError):
        service.transition_verification(
            tenant_id=synthetic_tenant,
            verification_id=verification.verification_id,
            to_status=VerificationStatus.REJECTED,
            reviewer_id=new_synthetic_id("REV"),
            reason="not the assigned reviewer",
        )


def test_events_are_immutable(service, synthetic_patient, synthetic_tenant, actor):
    order, _specimen = _ready_order_and_specimen(
        service, synthetic_patient, synthetic_tenant, actor
    )
    event = service.provenance(tenant_id=synthetic_tenant, aggregate_id=order.order_id)[0]
    with pytest.raises(FrozenInstanceError):
        event.event_type = "tampered"  # type: ignore[misc]
    payload = event.to_dict()
    payload["event_type"] = "tampered"
    assert event.event_type == EventType.LAB_ORDER_PLACED
    assert event.event_id.startswith("SYN-EVT-")
