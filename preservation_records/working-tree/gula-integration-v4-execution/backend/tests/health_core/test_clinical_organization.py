"""Tests for the synthetic organisation/facility registry and hierarchy."""

from __future__ import annotations

import pytest
from app.health_core.clinical import ClinicalContext
from app.health_core.clinical.errors import ClinicalValidationError, UnknownClinicalEntityError
from app.health_core.common import (
    AggregateType,
    DuplicateEntityError,
    EventType,
    ForbiddenSyntheticOperationError,
    TenantMismatchError,
)


def _register_organization(context: ClinicalContext, tenant_id: str, key: str = "SYN-ORG-0001"):
    return context.organizations.register_organization(
        tenant_id=tenant_id,
        idempotency_key=key,
        label="synthetic-health-directorate",
    )


def test_facility_belongs_to_organization_and_is_listed(synthetic_registry, synthetic_tenant):
    context = ClinicalContext(identity=synthetic_registry)
    organization = _register_organization(context, synthetic_tenant)
    facility = context.organizations.register_facility(
        tenant_id=synthetic_tenant,
        idempotency_key="SYN-FAC-0001",
        organization_id=organization.organization_id,
        label="synthetic-hospital",
        facility_type="hospital",
    )
    assert facility.tenant_id == synthetic_tenant
    assert facility.organization_id == organization.organization_id
    assert context.organizations.facilities_for_organization(
        tenant_id=synthetic_tenant, organization_id=organization.organization_id
    ) == (facility,)
    assert (
        context.organizations.require_facility(
            tenant_id=synthetic_tenant, facility_id=facility.facility_id
        )
        == facility
    )


def test_facility_registration_emits_facility_event(synthetic_registry, synthetic_tenant):
    context = ClinicalContext(identity=synthetic_registry)
    organization = _register_organization(context, synthetic_tenant)
    context.organizations.register_facility(
        tenant_id=synthetic_tenant,
        idempotency_key="SYN-FAC-0002",
        organization_id=organization.organization_id,
        label="synthetic-clinic",
        facility_type="clinic",
    )
    events = context.event_history()
    assert len(events) == 1
    assert events[0].event_type == EventType.FACILITY_REGISTERED
    assert events[0].aggregate_type == AggregateType.FACILITY
    assert events[0].aggregate_id == "SYN-FAC-0002"
    assert events[0].tenant_id == synthetic_tenant
    assert events[0].payload["organization_id"] == organization.organization_id


def test_facility_under_unknown_organization_is_rejected(synthetic_registry, synthetic_tenant):
    context = ClinicalContext(identity=synthetic_registry)
    with pytest.raises(UnknownClinicalEntityError) as exc:
        context.organizations.register_facility(
            tenant_id=synthetic_tenant,
            idempotency_key="SYN-FAC-0003",
            organization_id="SYN-ORG-4040",
            label="synthetic-clinic",
            facility_type="clinic",
        )
    assert exc.value.code == "UNKNOWN_CLINICAL_ENTITY"


def test_cross_tenant_organization_lookup_is_refused(synthetic_registry, synthetic_tenant):
    context = ClinicalContext(identity=synthetic_registry)
    _register_organization(context, synthetic_tenant)
    with pytest.raises(TenantMismatchError):
        context.organizations.get_organization(
            tenant_id="SYN-LAB-9999", organization_id="SYN-ORG-0001"
        )


def test_facility_cannot_be_attached_to_another_organization(synthetic_registry, synthetic_tenant):
    context = ClinicalContext(identity=synthetic_registry)
    organization = _register_organization(context, synthetic_tenant)
    other = _register_organization(context, synthetic_tenant, "SYN-ORG-0002")
    facility = context.organizations.register_facility(
        tenant_id=synthetic_tenant,
        idempotency_key="SYN-FAC-0004",
        organization_id=organization.organization_id,
        label="synthetic-lab",
        facility_type="laboratory",
    )
    with pytest.raises(ForbiddenSyntheticOperationError):
        context.organizations.require_facility(
            tenant_id=synthetic_tenant,
            facility_id=facility.facility_id,
            organization_id=other.organization_id,
        )


def test_facility_replay_and_conflict(synthetic_registry, synthetic_tenant):
    context = ClinicalContext(identity=synthetic_registry)
    organization = _register_organization(context, synthetic_tenant)
    kwargs = {
        "tenant_id": synthetic_tenant,
        "idempotency_key": "SYN-FAC-0005",
        "organization_id": organization.organization_id,
        "label": "synthetic-lab",
        "facility_type": "laboratory",
    }
    first = context.organizations.register_facility(**kwargs)
    replay = context.organizations.register_facility(**kwargs)
    assert replay is first
    with pytest.raises(DuplicateEntityError):
        context.organizations.register_facility(**{**kwargs, "label": "other-synthetic-lab"})
    assert len(context.event_history()) == 1


def test_invalid_facility_type_is_rejected(synthetic_registry, synthetic_tenant):
    context = ClinicalContext(identity=synthetic_registry)
    organization = _register_organization(context, synthetic_tenant)
    with pytest.raises(ClinicalValidationError):
        context.organizations.register_facility(
            tenant_id=synthetic_tenant,
            idempotency_key="SYN-FAC-0006",
            organization_id=organization.organization_id,
            label="synthetic-lab",
            facility_type="spaceship",
        )
