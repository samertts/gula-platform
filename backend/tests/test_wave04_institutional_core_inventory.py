"""Wave 04 — institutional hierarchy conformance and declared gaps.

Synthetic schema-level assertions only. These tests do not seed a registry,
claim government adoption, modify production data, or change authorization.
"""

from __future__ import annotations

import pytest
from app.identity.models.administrative_structure import (
    NIAMAdminBranch,
    NIAMAdminDepartment,
    NIAMAdminFacility,
    NIAMAdminUnit,
    OrganizationOwnership,
    OrganizationRepresentative,
    OrganizationStatus,
)
from app.identity.models.niam_organization import NIAMOrganization
from app.identity.services.organization_service import (
    InvalidOrganizationTransition,
    OrganizationStateService,
    OrganizationVerificationProvider,
    OrganizationVerificationStatus,
)
from app.national.domain.clinic import Clinic
from app.national.domain.department import Department
from app.national.domain.directorate import Directorate
from app.national.domain.facility import Facility
from app.national.domain.hospital import Hospital
from app.national.domain.laboratory import Laboratory
from app.national.domain.organization import Organization
from app.national.domain.ward import Ward
from app.national.enums import FacilityType, OrganizationType
from app.national.fhir.organization import FHIROrganizationMapper


def _columns(model) -> set[str]:
    return {column.name for column in model.__table__.columns}


def test_national_institutional_models_expose_stable_ids_audit_and_fhir_columns() -> None:
    for model in (Organization, Directorate, Facility, Hospital, Department, Ward, Clinic, Laboratory):
        columns = _columns(model)
        assert "id" in columns
        assert "created_at" in columns
        assert "updated_at" in columns
        assert "is_deleted" in columns
        assert "version" in columns
        assert "fhir_id" in columns

    assert "org_type" in _columns(Organization)
    assert "parent_organization_id" in _columns(Organization)
    assert "nhop_code" in _columns(Organization)

    assert {"organization_id", "parent_directorate_id", "governorate"} <= _columns(Directorate)
    assert {"organization_id", "directorate_id", "parent_facility_id"} <= _columns(Facility)
    assert {"facility_id", "parent_department_id"} <= _columns(Department)
    assert {"hospital_id", "facility_id"} <= _columns(Ward)
    assert {"license_number", "nhop_lab_code"} <= _columns(Laboratory)


def test_national_facility_types_and_hierarchy_indexes_match_declared_enums() -> None:
    assert {member.value for member in OrganizationType} >= {
        "ministry", "directorate", "hospital", "clinic", "laboratory", "pharmacy"
    }
    assert {member.value for member in FacilityType} >= {
        "hospital", "clinic", "laboratory", "pharmacy", "ward", "emergency", "operating_room"
    }

    facility_indexes = {index.name for index in Facility.__table__.indexes}
    assert {
        "ix_national_facilities_type",
        "ix_national_facilities_org",
        "ix_national_facilities_directorate",
    } <= facility_indexes
    assert Facility.__table__.c.organization_id.foreign_keys
    assert Facility.__table__.c.directorate_id.foreign_keys
    assert Directorate.__table__.c.organization_id.foreign_keys


def test_fhir_organization_mapper_preserves_parent_and_active_status() -> None:
    organization = Organization(
        id="ORG-SYN-0001",
        org_type=OrganizationType.MINISTRY,
        name="Synthetic Ministry",
        is_active=True,
        parent_organization_id=None,
    )
    mapped = FHIROrganizationMapper.from_model(organization)

    assert mapped["resourceType"] == "Organization"
    assert mapped["id"] == "ORG-SYN-0001"
    assert mapped["active"] is True
    assert "partOf" not in mapped


def test_niam_admin_hierarchy_and_ownership_columns_are_present() -> None:
    assert {"org_id", "org_type", "status", "governorate", "district"} <= _columns(NIAMOrganization)
    assert {"branch_id", "organization_id", "status"} <= _columns(NIAMAdminBranch)
    assert {"facility_id", "branch_id", "organization_id", "facility_type"} <= _columns(NIAMAdminFacility)
    assert {"dept_id", "facility_id", "head_person_id"} <= _columns(NIAMAdminDepartment)
    assert {"unit_id", "department_id"} <= _columns(NIAMAdminUnit)
    assert {"valid_from", "expires_at", "status"} <= _columns(OrganizationRepresentative)
    assert {"valid_from", "expires_at", "status", "authority_reference"} <= _columns(OrganizationOwnership)


def test_organization_state_machine_rejects_draft_activation() -> None:
    organization = Organization(id="ORG-SYN-0002", org_type=OrganizationType.MINISTRY, name="Synthetic")
    organization.status = OrganizationStatus.draft.value
    with pytest.raises(InvalidOrganizationTransition):
        OrganizationStateService.activate_after_approval(organization)
    assert organization.status == OrganizationStatus.draft.value


@pytest.mark.asyncio
async def test_verification_provider_is_explicitly_not_connected() -> None:
    result = await OrganizationVerificationProvider().verify("ORG-SYN-0003", OrganizationType.HOSPITAL)

    assert result.status is OrganizationVerificationStatus.not_connected
    assert result.provider == "organization:not-connected"


@pytest.mark.xfail(strict=True, reason="Effective-dating/history columns are a documented Wave 04 gap")
def test_effective_dating_history_is_present_for_core_institutions() -> None:
    for model in (Organization, Directorate, Facility, Hospital):
        columns = _columns(model)
        assert {"effective_from", "effective_to"} <= columns


@pytest.mark.asyncio
@pytest.mark.xfail(strict=True, reason="Fuzzy/registry duplicate detection is not connected in this wave")
async def test_registry_backed_duplicate_detection_is_connected() -> None:
    result = await OrganizationVerificationProvider().verify("ORG-SYN-0004", OrganizationType.HOSPITAL)
    assert result.status is not OrganizationVerificationStatus.not_connected
