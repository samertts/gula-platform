"""End-to-end synthetic lab workflow: order -> specimen -> result -> verification."""

from __future__ import annotations

import pytest
from app.health_core.common.event_types import AggregateType, EventType
from app.health_core.common.ids import new_synthetic_id
from app.health_core.identity.synthetic import SyntheticPatientRegistry
from app.health_core.lab import (
    LabWorkflowService,
    Priority,
    SpecimenStatus,
    VerificationDecision,
    VerificationStatus,
    catalogue_codes,
)
from app.health_core.lab import (
    TestExecutionStatus as ExecStatus,
)


@pytest.fixture
def service(synthetic_registry: SyntheticPatientRegistry) -> LabWorkflowService:
    return LabWorkflowService(identity=synthetic_registry)


@pytest.fixture
def actor() -> str:
    return new_synthetic_id("ACT")


@pytest.fixture
def reviewer() -> str:
    return new_synthetic_id("REV")


@pytest.fixture
def placed_order(service, synthetic_patient, synthetic_tenant, actor):
    return service.place_order(
        tenant_id=synthetic_tenant,
        patient_ref=synthetic_patient.ref,
        test_codes=["GLU", "WBC"],
        idempotency_key=new_synthetic_id("KEY"),
        priority=Priority.URGENT,
        actor_id=actor,
    )


def test_full_happy_path_order_to_verification(
    service, synthetic_patient, synthetic_tenant, actor, reviewer, placed_order
):
    order = placed_order
    assert order.order_id.startswith("SYN-ORD-")
    assert order.priority is Priority.URGENT
    assert order.test_codes == ("GLU", "WBC")

    barcode = new_synthetic_id("BAR")
    specimen = service.register_specimen(
        tenant_id=synthetic_tenant,
        order_id=order.order_id,
        barcode=barcode,
        actor_id=actor,
    )
    assert specimen.barcode == barcode
    assert specimen.status is SpecimenStatus.REGISTERED

    for target in (SpecimenStatus.COLLECTED, SpecimenStatus.RECEIVED):
        specimen = service.transition_specimen(
            tenant_id=synthetic_tenant,
            specimen_id=specimen.specimen_id,
            to_status=target,
            actor_id=actor,
        )
    assert specimen.status is SpecimenStatus.RECEIVED

    execution = service.enter_testing(
        tenant_id=synthetic_tenant, specimen_id=specimen.specimen_id, actor_id=actor
    )
    assert execution.status is ExecStatus.ENTERED
    assert (
        service.get_specimen(tenant_id=synthetic_tenant, specimen_id=specimen.specimen_id).status
        is SpecimenStatus.IN_TESTING
    )

    completed = service.complete_testing(
        tenant_id=synthetic_tenant, execution_id=execution.execution_id, actor_id=actor
    )
    assert completed.status is ExecStatus.COMPLETED
    assert completed.completed_at is not None
    assert (
        service.get_specimen(tenant_id=synthetic_tenant, specimen_id=specimen.specimen_id).status
        is SpecimenStatus.FINAL
    )

    result = service.record_result(
        tenant_id=synthetic_tenant,
        order_id=order.order_id,
        specimen_id=specimen.specimen_id,
        patient_ref=synthetic_patient.ref,
        test_code="GLU",
        value=92.0,
        unit="mg/dL",
        idempotency_key=new_synthetic_id("KEY"),
        actor_id=actor,
    )
    assert result.critical_flag is False
    assert result.version == 1

    verification = service.verify_result(
        tenant_id=synthetic_tenant,
        result_id=result.result_id,
        reviewer_id=reviewer,
        decision=VerificationDecision.VERIFIED,
        idempotency_key=new_synthetic_id("KEY"),
    )
    assert verification.status is VerificationStatus.VERIFIED
    assert verification.reviewer_id == reviewer
    assert service.verification_for_result(
        tenant_id=synthetic_tenant, result_id=result.result_id
    ) == verification


def test_order_cancellation_lifecycle(service, synthetic_tenant, placed_order, actor):
    cancelled = service.cancel_order(
        tenant_id=synthetic_tenant,
        order_id=placed_order.order_id,
        reason="duplicate request",
        actor_id=actor,
    )
    assert cancelled.status.value == "cancelled"
    assert cancelled.cancellation_reason == "duplicate request"
    assert cancelled.cancelled_at is not None
    assert service.list_orders(tenant_id=synthetic_tenant) == (cancelled,)

    events = service.provenance(
        tenant_id=synthetic_tenant, aggregate_id=placed_order.order_id
    )
    assert [event.event_type for event in events] == [
        EventType.LAB_ORDER_PLACED,
        EventType.LAB_ORDER_CANCELLED,
    ]


def test_cannot_register_specimen_on_cancelled_order(
    service, synthetic_tenant, placed_order, actor
):
    from app.health_core.common.errors import InvalidStateTransitionError

    service.cancel_order(
        tenant_id=synthetic_tenant,
        order_id=placed_order.order_id,
        reason="cancelled by requester",
        actor_id=actor,
    )
    with pytest.raises(InvalidStateTransitionError):
        service.register_specimen(
            tenant_id=synthetic_tenant,
            order_id=placed_order.order_id,
            barcode=new_synthetic_id("BAR"),
            actor_id=actor,
        )


def test_specimen_rejection_with_reason_reaches_final(
    service, synthetic_tenant, placed_order, actor
):
    specimen = service.register_specimen(
        tenant_id=synthetic_tenant,
        order_id=placed_order.order_id,
        barcode=new_synthetic_id("BAR"),
        actor_id=actor,
    )
    for target in (SpecimenStatus.COLLECTED, SpecimenStatus.RECEIVED):
        specimen = service.transition_specimen(
            tenant_id=synthetic_tenant,
            specimen_id=specimen.specimen_id,
            to_status=target,
            actor_id=actor,
        )
    rejected = service.transition_specimen(
        tenant_id=synthetic_tenant,
        specimen_id=specimen.specimen_id,
        to_status=SpecimenStatus.REJECTED,
        actor_id=actor,
        reason="haemolysed sample",
    )
    assert rejected.status is SpecimenStatus.REJECTED
    assert rejected.rejection_reason == "haemolysed sample"
    final = service.transition_specimen(
        tenant_id=synthetic_tenant,
        specimen_id=specimen.specimen_id,
        to_status=SpecimenStatus.FINAL,
        actor_id=actor,
    )
    assert final.status is SpecimenStatus.FINAL


def test_custody_chain_records_actor_timestamp_and_reason(
    service, synthetic_tenant, placed_order, actor
):
    specimen = service.register_specimen(
        tenant_id=synthetic_tenant,
        order_id=placed_order.order_id,
        barcode=new_synthetic_id("BAR"),
        actor_id=actor,
    )
    for target in (SpecimenStatus.COLLECTED, SpecimenStatus.RECEIVED):
        service.transition_specimen(
            tenant_id=synthetic_tenant,
            specimen_id=specimen.specimen_id,
            to_status=target,
            actor_id=actor,
        )
    service.transition_specimen(
        tenant_id=synthetic_tenant,
        specimen_id=specimen.specimen_id,
        to_status=SpecimenStatus.REJECTED,
        actor_id=actor,
        reason="insufficient volume",
    )
    chain = service.custody_chain(
        tenant_id=synthetic_tenant, specimen_id=specimen.specimen_id
    )
    assert len(chain) == 4
    assert chain[0].from_status is None
    assert chain[0].to_status is SpecimenStatus.REGISTERED
    assert all(entry.actor_id == actor for entry in chain)
    assert all(entry.occurred_at.endswith("+00:00") for entry in chain)
    assert all(entry.entry_id.startswith("SYN-CUST-") for entry in chain)
    assert chain[-1].reason == "insufficient volume"


def test_provenance_covers_full_specimen_lifecycle(
    service, synthetic_tenant, placed_order, actor
):
    specimen = service.register_specimen(
        tenant_id=synthetic_tenant,
        order_id=placed_order.order_id,
        barcode=new_synthetic_id("BAR"),
        actor_id=actor,
    )
    for target in (SpecimenStatus.COLLECTED, SpecimenStatus.RECEIVED):
        service.transition_specimen(
            tenant_id=synthetic_tenant,
            specimen_id=specimen.specimen_id,
            to_status=target,
            actor_id=actor,
        )
    execution = service.enter_testing(
        tenant_id=synthetic_tenant, specimen_id=specimen.specimen_id, actor_id=actor
    )
    service.complete_testing(
        tenant_id=synthetic_tenant, execution_id=execution.execution_id, actor_id=actor
    )
    events = service.provenance(
        tenant_id=synthetic_tenant, aggregate_id=specimen.specimen_id
    )
    assert [event.event_type for event in events] == [
        EventType.SPECIMEN_REGISTERED,
        EventType.SPECIMEN_COLLECTED,
        EventType.SPECIMEN_RECEIVED,
        "specimen.in_testing",
        "test.entered",
        "specimen.final",
        "test.completed",
    ]
    assert all(event.aggregate_type == AggregateType.SPECIMEN for event in events)
    assert all(event.tenant_id == synthetic_tenant for event in events)


def test_illegal_specimen_transitions_are_rejected(
    service, synthetic_tenant, placed_order, actor
):
    from app.health_core.common.errors import InvalidStateTransitionError

    specimen = service.register_specimen(
        tenant_id=synthetic_tenant,
        order_id=placed_order.order_id,
        barcode=new_synthetic_id("BAR"),
        actor_id=actor,
    )
    with pytest.raises(InvalidStateTransitionError):
        service.transition_specimen(
            tenant_id=synthetic_tenant,
            specimen_id=specimen.specimen_id,
            to_status=SpecimenStatus.RECEIVED,
            actor_id=actor,
        )
    with pytest.raises(InvalidStateTransitionError):
        service.transition_specimen(
            tenant_id=synthetic_tenant,
            specimen_id=specimen.specimen_id,
            to_status=SpecimenStatus.IN_TESTING,
            actor_id=actor,
        )


def test_rejection_requires_reason(service, synthetic_tenant, placed_order, actor):
    from app.health_core.lab.errors import LabWorkflowError

    specimen = service.register_specimen(
        tenant_id=synthetic_tenant,
        order_id=placed_order.order_id,
        barcode=new_synthetic_id("BAR"),
        actor_id=actor,
    )
    service.transition_specimen(
        tenant_id=synthetic_tenant,
        specimen_id=specimen.specimen_id,
        to_status=SpecimenStatus.COLLECTED,
        actor_id=actor,
    )
    service.transition_specimen(
        tenant_id=synthetic_tenant,
        specimen_id=specimen.specimen_id,
        to_status=SpecimenStatus.RECEIVED,
        actor_id=actor,
    )
    with pytest.raises(LabWorkflowError):
        service.transition_specimen(
            tenant_id=synthetic_tenant,
            specimen_id=specimen.specimen_id,
            to_status=SpecimenStatus.REJECTED,
            actor_id=actor,
        )


def test_test_codes_are_normalised_and_validated(
    service, synthetic_patient, synthetic_tenant, actor
):
    order = service.place_order(
        tenant_id=synthetic_tenant,
        patient_ref=synthetic_patient.ref,
        test_codes=["glu", " glu ", "wbc", "GLU"],
        idempotency_key=new_synthetic_id("KEY"),
        actor_id=actor,
    )
    assert order.test_codes == ("GLU", "WBC")
    assert "GLU" in catalogue_codes()


def test_unknown_order_and_specimen_fail_closed(service, synthetic_tenant, actor):
    from app.health_core.lab.errors import UnknownLabEntityError

    with pytest.raises(UnknownLabEntityError):
        service.get_order(
            tenant_id=synthetic_tenant, order_id=new_synthetic_id("ORD")
        )
    with pytest.raises(UnknownLabEntityError):
        service.get_specimen(
            tenant_id=synthetic_tenant, specimen_id=new_synthetic_id("SPC")
        )
