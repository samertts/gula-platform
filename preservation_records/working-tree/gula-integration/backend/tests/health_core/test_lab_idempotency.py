"""Idempotency and uniqueness guarantees of the synthetic lab workflow."""

from __future__ import annotations

import pytest
from app.health_core.common.errors import DuplicateEntityError
from app.health_core.common.ids import new_synthetic_id
from app.health_core.identity.synthetic import SyntheticPatientRegistry
from app.health_core.lab import (
    LabWorkflowService,
    Priority,
    SpecimenStatus,
    VerificationDecision,
)


@pytest.fixture
def service(synthetic_registry: SyntheticPatientRegistry) -> LabWorkflowService:
    return LabWorkflowService(identity=synthetic_registry)


@pytest.fixture
def actor() -> str:
    return new_synthetic_id("ACT")


@pytest.fixture
def placed_order(service, synthetic_patient, synthetic_tenant, actor):
    return _place(service, synthetic_patient, synthetic_tenant, actor)


def _place(service, patient, tenant, actor, codes=("GLU",), key=None):
    return service.place_order(
        tenant_id=tenant,
        patient_ref=patient.ref,
        test_codes=list(codes),
        idempotency_key=key or new_synthetic_id("KEY"),
        priority=Priority.ROUTINE,
        actor_id=actor,
    )


def _ready_specimen(service, order, tenant, actor, barcode=None):
    specimen = service.register_specimen(
        tenant_id=tenant,
        order_id=order.order_id,
        barcode=barcode or new_synthetic_id("BAR"),
        actor_id=actor,
    )
    for target in (SpecimenStatus.COLLECTED, SpecimenStatus.RECEIVED):
        specimen = service.transition_specimen(
            tenant_id=tenant,
            specimen_id=specimen.specimen_id,
            to_status=target,
            actor_id=actor,
        )
    return specimen


def _record(service, patient, tenant, order, specimen, actor, key, value=90.0):
    return service.record_result(
        tenant_id=tenant,
        order_id=order.order_id,
        specimen_id=specimen.specimen_id,
        patient_ref=patient.ref,
        test_code="GLU",
        value=value,
        unit="mg/dL",
        idempotency_key=key,
        actor_id=actor,
    )


def test_duplicate_order_key_identical_replay_returns_original(
    service, synthetic_patient, synthetic_tenant, actor
):
    key = new_synthetic_id("KEY")
    first = _place(service, synthetic_patient, synthetic_tenant, actor, key=key)
    replay = _place(service, synthetic_patient, synthetic_tenant, actor, key=key)
    assert replay == first
    assert len(service.list_orders(tenant_id=synthetic_tenant)) == 1


def test_duplicate_order_key_conflict_raises(
    service, synthetic_patient, synthetic_tenant, actor
):
    key = new_synthetic_id("KEY")
    _place(service, synthetic_patient, synthetic_tenant, actor, key=key)
    with pytest.raises(DuplicateEntityError) as exc:
        _place(
            service,
            synthetic_patient,
            synthetic_tenant,
            actor,
            codes=("WBC",),
            key=key,
        )
    assert exc.value.code == "DUPLICATE_ENTITY"


def test_duplicate_barcode_identical_replay_returns_original(
    service, synthetic_patient, synthetic_tenant, actor
):
    order = _place(service, synthetic_patient, synthetic_tenant, actor)
    barcode = new_synthetic_id("BAR")
    first = service.register_specimen(
        tenant_id=synthetic_tenant,
        order_id=order.order_id,
        barcode=barcode,
        actor_id=actor,
    )
    replay = service.register_specimen(
        tenant_id=synthetic_tenant,
        order_id=order.order_id,
        barcode=barcode,
        actor_id=actor,
    )
    assert replay == first
    assert len(service.list_specimens(tenant_id=synthetic_tenant)) == 1


def test_duplicate_barcode_conflict_raises(
    service, synthetic_patient, synthetic_tenant, actor
):
    first_order = _place(service, synthetic_patient, synthetic_tenant, actor)
    second_order = _place(service, synthetic_patient, synthetic_tenant, actor)
    barcode = new_synthetic_id("BAR")
    service.register_specimen(
        tenant_id=synthetic_tenant,
        order_id=first_order.order_id,
        barcode=barcode,
        actor_id=actor,
    )
    with pytest.raises(DuplicateEntityError):
        service.register_specimen(
            tenant_id=synthetic_tenant,
            order_id=second_order.order_id,
            barcode=barcode,
            actor_id=actor,
        )


def test_duplicate_result_key_identical_replay_returns_original(
    service, synthetic_patient, synthetic_tenant, actor
):
    order = _place(service, synthetic_patient, synthetic_tenant, actor)
    specimen = _ready_specimen(service, order, synthetic_tenant, actor)
    key = new_synthetic_id("KEY")
    first = _record(service, synthetic_patient, synthetic_tenant, order, specimen, actor, key)
    replay = _record(service, synthetic_patient, synthetic_tenant, order, specimen, actor, key)
    assert replay == first
    assert len(service.list_results(tenant_id=synthetic_tenant)) == 1


def test_duplicate_result_key_conflict_raises(
    service, synthetic_patient, synthetic_tenant, actor
):
    order = _place(service, synthetic_patient, synthetic_tenant, actor)
    specimen = _ready_specimen(service, order, synthetic_tenant, actor)
    key = new_synthetic_id("KEY")
    _record(service, synthetic_patient, synthetic_tenant, order, specimen, actor, key)
    with pytest.raises(DuplicateEntityError):
        _record(
            service,
            synthetic_patient,
            synthetic_tenant,
            order,
            specimen,
            actor,
            key,
            value=105.0,
        )


def test_duplicate_verification_key_identical_replay_returns_original(
    service, synthetic_patient, synthetic_tenant, actor
):
    order = _place(service, synthetic_patient, synthetic_tenant, actor)
    specimen = _ready_specimen(service, order, synthetic_tenant, actor)
    result = _record(
        service, synthetic_patient, synthetic_tenant, order, specimen, actor,
        new_synthetic_id("KEY"),
    )
    reviewer = new_synthetic_id("REV")
    key = new_synthetic_id("KEY")
    first = service.verify_result(
        tenant_id=synthetic_tenant,
        result_id=result.result_id,
        reviewer_id=reviewer,
        decision=VerificationDecision.VERIFIED,
        idempotency_key=key,
    )
    replay = service.verify_result(
        tenant_id=synthetic_tenant,
        result_id=result.result_id,
        reviewer_id=reviewer,
        decision=VerificationDecision.VERIFIED,
        idempotency_key=key,
    )
    assert replay == first


def test_duplicate_verification_key_conflict_raises(
    service, synthetic_patient, synthetic_tenant, actor
):
    order = _place(service, synthetic_patient, synthetic_tenant, actor)
    specimen = _ready_specimen(service, order, synthetic_tenant, actor)
    result = _record(
        service, synthetic_patient, synthetic_tenant, order, specimen, actor,
        new_synthetic_id("KEY"),
    )
    reviewer = new_synthetic_id("REV")
    key = new_synthetic_id("KEY")
    service.verify_result(
        tenant_id=synthetic_tenant,
        result_id=result.result_id,
        reviewer_id=reviewer,
        decision=VerificationDecision.VERIFIED,
        idempotency_key=key,
    )
    with pytest.raises(DuplicateEntityError):
        service.verify_result(
            tenant_id=synthetic_tenant,
            result_id=result.result_id,
            reviewer_id=reviewer,
            decision=VerificationDecision.REJECTED,
            idempotency_key=key,
            reason="incorrect result",
        )


def test_replay_emits_no_extra_events(
    service, synthetic_patient, synthetic_tenant, actor
):
    key = new_synthetic_id("KEY")
    first = _place(service, synthetic_patient, synthetic_tenant, actor, key=key)
    before = service.all_events(tenant_id=synthetic_tenant)
    _place(service, synthetic_patient, synthetic_tenant, actor, key=key)
    after = service.all_events(tenant_id=synthetic_tenant)
    assert before == after
    assert len(service.provenance(tenant_id=synthetic_tenant, aggregate_id=first.order_id)) == 1


def test_repeat_cancel_is_idempotent(service, synthetic_tenant, actor, placed_order):
    first = service.cancel_order(
        tenant_id=synthetic_tenant,
        order_id=placed_order.order_id,
        reason="duplicate",
        actor_id=actor,
    )
    before = service.all_events(tenant_id=synthetic_tenant)
    second = service.cancel_order(
        tenant_id=synthetic_tenant,
        order_id=placed_order.order_id,
        reason="duplicate",
        actor_id=actor,
    )
    assert second == first
    assert service.all_events(tenant_id=synthetic_tenant) == before


def test_repeat_complete_testing_is_idempotent(
    service, synthetic_patient, synthetic_tenant, actor
):
    order = _place(service, synthetic_patient, synthetic_tenant, actor)
    specimen = service.register_specimen(
        tenant_id=synthetic_tenant,
        order_id=order.order_id,
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
    first = service.complete_testing(
        tenant_id=synthetic_tenant, execution_id=execution.execution_id, actor_id=actor
    )
    before = service.all_events(tenant_id=synthetic_tenant)
    second = service.complete_testing(
        tenant_id=synthetic_tenant, execution_id=execution.execution_id, actor_id=actor
    )
    assert second == first
    assert service.all_events(tenant_id=synthetic_tenant) == before
