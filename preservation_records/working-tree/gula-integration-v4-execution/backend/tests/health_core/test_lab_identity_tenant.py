"""Tenant isolation and synthetic-identity guard tests for the lab workflow."""

from __future__ import annotations

import inspect
from dataclasses import fields
from typing import Protocol

import pytest
from app.health_core.common.errors import (
    InvalidSyntheticReferenceError,
    TenantMismatchError,
    UnknownPatientError,
)
from app.health_core.common.ids import new_synthetic_id
from app.health_core.identity.synthetic import SyntheticPatientRegistry
from app.health_core.lab import (
    FutureAnalyzerGateway,
    FuturePatientLookup,
    FutureResultPublisher,
    LabOrder,
    LabResult,
    LabWorkflowService,
    Specimen,
    SpecimenStatus,
    Verification,
)
from app.health_core.lab.errors import InvalidActorError


@pytest.fixture
def service(synthetic_registry: SyntheticPatientRegistry) -> LabWorkflowService:
    return LabWorkflowService(identity=synthetic_registry)


@pytest.fixture
def actor() -> str:
    return new_synthetic_id("ACT")


@pytest.fixture
def placed_order(service, synthetic_patient, synthetic_tenant, actor):
    return service.place_order(
        tenant_id=synthetic_tenant,
        patient_ref=synthetic_patient.ref,
        test_codes=["GLU"],
        idempotency_key=new_synthetic_id("KEY"),
        actor_id=actor,
    )


def _ready_specimen(service, synthetic_patient, synthetic_tenant, actor):
    order = service.place_order(
        tenant_id=synthetic_tenant,
        patient_ref=synthetic_patient.ref,
        test_codes=["GLU"],
        idempotency_key=new_synthetic_id("KEY"),
        actor_id=actor,
    )
    specimen = service.register_specimen(
        tenant_id=synthetic_tenant,
        order_id=order.order_id,
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
    return order, specimen


def test_unknown_patient_on_order_fails_closed(service, synthetic_tenant, actor):
    with pytest.raises(UnknownPatientError):
        service.place_order(
            tenant_id=synthetic_tenant,
            patient_ref="SYN-PAT-DOESNOTEXIST",
            test_codes=["GLU"],
            idempotency_key=new_synthetic_id("KEY"),
            actor_id=actor,
        )


def test_cross_tenant_patient_reference_refused(
    service, synthetic_registry, synthetic_tenant, actor
):
    other = synthetic_registry.register_patient(tenant_id="SYN-LAB-9999", label="beta")
    with pytest.raises(TenantMismatchError):
        service.place_order(
            tenant_id=synthetic_tenant,
            patient_ref=other.ref,
            test_codes=["GLU"],
            idempotency_key=new_synthetic_id("KEY"),
            actor_id=actor,
        )


def test_order_and_specimen_are_tenant_scoped(
    service, synthetic_patient, synthetic_tenant, actor
):
    order, specimen = _ready_specimen(service, synthetic_patient, synthetic_tenant, actor)
    with pytest.raises(TenantMismatchError):
        service.get_order(tenant_id="SYN-LAB-9999", order_id=order.order_id)
    with pytest.raises(TenantMismatchError):
        service.get_specimen(tenant_id="SYN-LAB-9999", specimen_id=specimen.specimen_id)
    with pytest.raises(TenantMismatchError):
        service.provenance(tenant_id="SYN-LAB-9999", aggregate_id=order.order_id)
    assert service.list_orders(tenant_id="SYN-LAB-9999") == ()
    assert service.list_specimens(tenant_id="SYN-LAB-9999") == ()


def test_results_and_verifications_are_tenant_scoped(
    service, synthetic_patient, synthetic_tenant, actor
):
    order, specimen = _ready_specimen(service, synthetic_patient, synthetic_tenant, actor)
    result = service.record_result(
        tenant_id=synthetic_tenant,
        order_id=order.order_id,
        specimen_id=specimen.specimen_id,
        patient_ref=synthetic_patient.ref,
        test_code="GLU",
        value=90.0,
        unit="mg/dL",
        idempotency_key=new_synthetic_id("KEY"),
        actor_id=actor,
    )
    verification = service.verify_result(
        tenant_id=synthetic_tenant,
        result_id=result.result_id,
        reviewer_id=new_synthetic_id("REV"),
        decision="verified",
        idempotency_key=new_synthetic_id("KEY"),
    )
    with pytest.raises(TenantMismatchError):
        service.get_result(tenant_id="SYN-LAB-9999", result_id=result.result_id)
    with pytest.raises(TenantMismatchError):
        service.get_verification(
            tenant_id="SYN-LAB-9999", verification_id=verification.verification_id
        )
    assert service.list_results(tenant_id="SYN-LAB-9999") == ()


def test_real_looking_barcodes_are_rejected(service, synthetic_tenant, placed_order, actor):
    for barcode in ("1234567890", "ABC123456789", "98765432101"):
        with pytest.raises(InvalidSyntheticReferenceError):
            service.register_specimen(
                tenant_id=synthetic_tenant,
                order_id=placed_order.order_id,
                barcode=barcode,
                actor_id=actor,
            )


def test_non_barcode_synthetic_reference_is_rejected(
    service, synthetic_tenant, placed_order, actor
):
    with pytest.raises(InvalidSyntheticReferenceError):
        service.register_specimen(
            tenant_id=synthetic_tenant,
            order_id=placed_order.order_id,
            barcode=new_synthetic_id("PAT"),
            actor_id=actor,
        )


def test_non_synthetic_actor_is_rejected(service, synthetic_patient, synthetic_tenant):
    with pytest.raises(InvalidActorError):
        service.place_order(
            tenant_id=synthetic_tenant,
            patient_ref=synthetic_patient.ref,
            test_codes=["GLU"],
            idempotency_key=new_synthetic_id("KEY"),
            actor_id="actor-1",
        )


def test_non_synthetic_idempotency_key_is_rejected(
    service, synthetic_patient, synthetic_tenant, actor
):
    with pytest.raises(InvalidSyntheticReferenceError):
        service.place_order(
            tenant_id=synthetic_tenant,
            patient_ref=synthetic_patient.ref,
            test_codes=["GLU"],
            idempotency_key="key-1",
            actor_id=actor,
        )


def test_entities_carry_no_real_identifier_fields():
    forbidden_fragments = ("citizen", "national", "nhid", "nid", "phone")
    for model in (LabOrder, Specimen, LabResult, Verification):
        names = {item.name for item in fields(model)}
        assert not any(fragment in name for fragment in forbidden_fragments for name in names)
        if model in (LabOrder, Specimen, LabResult):
            assert "patient" in names


def test_future_integrations_are_declaration_only():
    assert issubclass(FuturePatientLookup, Protocol)
    assert issubclass(FutureAnalyzerGateway, Protocol)
    assert issubclass(FutureResultPublisher, Protocol)
    signature = inspect.signature(LabWorkflowService.__init__)
    assert "identity" in signature.parameters
    assert "analyzer" not in signature.parameters
