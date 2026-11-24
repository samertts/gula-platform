"""Tests for the synthetic practitioner registry."""

from __future__ import annotations

import pytest
from app.health_core.clinical import (
    ClinicalContext,
    PractitionerRegistry,
    PractitionerRole,
)
from app.health_core.clinical.errors import ClinicalValidationError
from app.health_core.common import (
    AggregateType,
    DuplicateEntityError,
    EventType,
    InvalidSyntheticReferenceError,
    TenantMismatchError,
)


def test_register_practitioner_emits_event_and_is_active(synthetic_registry, synthetic_tenant):
    context = ClinicalContext(identity=synthetic_registry)
    practitioner = context.practitioners.register(
        tenant_id=synthetic_tenant,
        idempotency_key="SYN-PRC-0001",
        role=PractitionerRole.PHYSICIAN,
        qualification="MBBS",
    )
    assert practitioner.practitioner_id == "SYN-PRC-0001"
    assert practitioner.tenant_id == synthetic_tenant
    assert practitioner.role is PractitionerRole.PHYSICIAN
    assert practitioner.qualification == "MBBS"
    assert practitioner.active is True
    assert context.practitioners.active_for_tenant(synthetic_tenant) == (practitioner,)

    events = context.event_history()
    assert len(events) == 1
    event = events[0]
    assert event.event_type == EventType.PRACTITIONER_REGISTERED
    assert event.aggregate_type == AggregateType.PRACTITIONER
    assert event.aggregate_id == "SYN-PRC-0001"
    assert event.tenant_id == synthetic_tenant
    assert event.payload["qualification"] == "MBBS"


def test_register_replay_returns_original_without_new_event(synthetic_registry, synthetic_tenant):
    context = ClinicalContext(identity=synthetic_registry)
    kwargs = {
        "tenant_id": synthetic_tenant,
        "idempotency_key": "SYN-PRC-0002",
        "role": "nurse",
        "qualification": "BSc Nursing",
    }
    first = context.practitioners.register(**kwargs)
    replay = context.practitioners.register(**kwargs)
    assert replay == first
    assert replay is first
    assert len(context.event_history()) == 1


def test_duplicate_key_with_different_arguments_is_rejected(synthetic_registry, synthetic_tenant):
    context = ClinicalContext(identity=synthetic_registry)
    context.practitioners.register(
        tenant_id=synthetic_tenant,
        idempotency_key="SYN-PRC-0003",
        role="physician",
        qualification="MBBS",
    )
    with pytest.raises(DuplicateEntityError) as exc:
        context.practitioners.register(
            tenant_id=synthetic_tenant,
            idempotency_key="SYN-PRC-0003",
            role="physician",
            qualification="MD",
        )
    assert exc.value.code == "DUPLICATE_ENTITY"
    assert len(context.event_history()) == 1


def test_cross_tenant_practitioner_lookup_is_refused(synthetic_registry, synthetic_tenant):
    context = ClinicalContext(identity=synthetic_registry)
    context.practitioners.register(
        tenant_id=synthetic_tenant,
        idempotency_key="SYN-PRC-0004",
        role="physician",
        qualification="MBBS",
    )
    with pytest.raises(TenantMismatchError):
        context.practitioners.get(tenant_id="SYN-LAB-9999", practitioner_id="SYN-PRC-0004")


def test_unsupported_role_is_rejected(synthetic_registry, synthetic_tenant):
    context = ClinicalContext(identity=synthetic_registry)
    with pytest.raises(ClinicalValidationError):
        context.practitioners.register(
            tenant_id=synthetic_tenant,
            idempotency_key="SYN-PRC-0005",
            role="unlicensed-wizard",
            qualification="MBBS",
        )


def test_empty_qualification_is_rejected(synthetic_registry, synthetic_tenant):
    context = ClinicalContext(identity=synthetic_registry)
    with pytest.raises(ClinicalValidationError):
        context.practitioners.register(
            tenant_id=synthetic_tenant,
            idempotency_key="SYN-PRC-0006",
            role="physician",
            qualification="   ",
        )


def test_non_synthetic_idempotency_key_is_rejected(synthetic_registry, synthetic_tenant):
    context = ClinicalContext(identity=synthetic_registry)
    with pytest.raises(InvalidSyntheticReferenceError):
        context.practitioners.register(
            tenant_id=synthetic_tenant,
            idempotency_key="PRC-12345",
            role="physician",
            qualification="MBBS",
        )


def test_inactive_practitioner_is_registered_but_not_listed_as_active(
    synthetic_registry, synthetic_tenant
):
    context = ClinicalContext(identity=synthetic_registry)
    practitioner = context.practitioners.register(
        tenant_id=synthetic_tenant,
        idempotency_key="SYN-PRC-0007",
        role="radiologist",
        qualification="DMRD",
        active=False,
    )
    assert practitioner.active is False
    assert context.practitioners.active_for_tenant(synthetic_tenant) == ()
    assert (
        context.practitioners.get(tenant_id=synthetic_tenant, practitioner_id="SYN-PRC-0007")
        == practitioner
    )
    assert context.event_history()[0].payload["active"] is False
    assert isinstance(context.practitioners, PractitionerRegistry)
