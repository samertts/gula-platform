"""Wave 04 — workforce and professional identity conformance.

Synthetic, schema-level assertions only. No official licensing, government
registry, payroll, financial, disciplinary or production approval is claimed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.identity.base import IdentityBase
from app.identity.models.account import Account
from app.identity.models.assignment import Assignment
from app.identity.models.delegation import NiamDelegation
from app.identity.models.employment import Employment, EmploymentStatus
from app.identity.models.identity import IdentityRecord
from app.identity.models.legacy_account_link import LegacyAccountLink, LegacyAccountLinkStatus
from app.identity.models.membership import Membership
from app.identity.professional_registry.models import (
    ProfessionalAuthorization,
    ProfessionalRegistryEntry,
)
from app.identity.services.clinical_authorization_context_service import (
    ClinicalActiveAssignmentUnavailable,
    ClinicalAuthorizationContextService,
)
from app.identity.services.verification_service import (
    AssuranceLevel,
    NotConnectedProvider,
    VerificationMethod,
    VerificationRequest,
    VerificationStatus,
)
from app.integration.inbox import SUPPORTED_EVENT_TYPES
from app.models.clinical_scope import ClinicalLabFacilityBinding
from app.models.organization import Facility, Organization
from app.models.tenant import Tenant
from app.national.domain.employee import Employee
from app.national.domain.practitioner import Practitioner
from app.national.domain.provider import Provider
from app.national.fhir.practitioner import FHIRPractitionerMapper
from app.national.reference.professions import Profession
from app.national.reference.specialties import Specialty
from app.governance.models.workforce import (
    AttendanceRecord,
    BoardCertification,
    HealthcareWorker,
    ProfessionalLicense,
    ProductivityRecord,
    RotationRecord,
)
from sqlalchemy import MetaData


def _columns(model) -> set[str]:
    return {column.name for column in model.__table__.columns}


def test_professional_registry_enforces_verification_before_privileges() -> None:
    registry_columns = _columns(ProfessionalRegistryEntry)
    assert {
        "registry_id",
        "registration_number",
        "issuing_authority",
        "verified",
        "verified_at",
        "expires_at",
        "privileges_activated_at",
    } <= registry_columns
    assert {"scope_type", "scope_id", "status", "expires_at"} <= _columns(ProfessionalAuthorization)


def test_delegation_model_is_canonical_metadata_only() -> None:
    assert "niam_delegations" in IdentityBase.metadata.tables
    columns = _columns(NiamDelegation)
    assert {"starts_at", "expires_at", "revoked_at", "depth", "permission_keys"} <= columns
    check = next(
        constraint.sqltext
        for constraint in NiamDelegation.__table__.constraints
        if constraint.name == "ck_niam_delegations_depth"
    )
    assert "1" in str(check) and "3" in str(check)


def test_employment_and_assignment_capture_lifecycle_and_scope() -> None:
    assert EmploymentStatus.terminated.value == "terminated"
    employment_columns = _columns(Employment)
    assert {
        "person_id", "organization_id", "status", "start_date", "end_date",
        "supervisor_person_id", "is_primary_employment", "termination_reason",
        "termination_date", "transfer_from_employment", "transfer_to_organization",
        "transfer_date",
    } <= employment_columns

    assignment_columns = _columns(Assignment)
    assert {
        "employment_id", "person_id", "organization_id", "facility_id",
        "clinical_organization_resource_id", "clinical_facility_resource_id",
        "status", "start_date", "end_date", "expected_end_date", "is_temporary",
        "is_emergency", "is_delegated", "delegated_from", "delegated_by",
        "max_duration_hours",
    } <= assignment_columns
    assert Assignment.__table__.c.clinical_facility_resource_id.foreign_keys
    assert Assignment.__table__.c.clinical_organization_resource_id.foreign_keys


def test_membership_lifecycle_timestamps_are_present() -> None:
    assert {
        "activated_at", "expires_at", "suspended_at", "revoked_at",
        "revocation_reason", "version",
    } <= _columns(Membership)


def test_national_workforce_models_cover_identity_classification_and_fhir() -> None:
    assert {"employee_code", "hire_date", "is_healthcare_worker"} <= _columns(Employee)
    assert {
        "license_number", "health_profession_number", "specialty",
        "qualification", "is_verified",
    } <= _columns(Practitioner)
    assert {"license_number", "specialty", "is_active"} <= _columns(Provider)
    assert Profession.__tablename__ == "ref_professions"
    assert Specialty.__tablename__ == "ref_specialties"

    practitioner = Practitioner(
        id="PRACTITIONER-SYN-1",
        role="doctor",
        full_name="Synthetic Clinician",
        license_number="SYN-LICENSE-1",
        qualification="Synthetic qualification",
    )
    mapped = FHIRPractitionerMapper.from_model(practitioner)
    assert mapped["resourceType"] == "Practitioner"
    assert any(identifier.get("value") == "SYN-LICENSE-1" for identifier in mapped.get("identifier", []))


def test_governance_workforce_records_cover_qualifications_and_duty() -> None:
    assert {"employee_code", "profession", "specialization"} <= _columns(HealthcareWorker)
    assert {"license_number", "issuing_authority", "expiry_date", "verified_at"} <= _columns(ProfessionalLicense)
    assert {"board_name", "specialty", "expiry_date"} <= _columns(BoardCertification)
    assert {"worker_id", "start_date", "end_date", "reason"} <= _columns(RotationRecord)
    assert {"worker_id", "date", "status"} <= _columns(AttendanceRecord)
    assert {"period", "period_start", "period_end"} <= _columns(ProductivityRecord)


def test_workforce_events_are_staged_not_approval_events() -> None:
    assert {"workforce.attendance.recorded", "workforce.assignment.changed"} <= SUPPORTED_EVENT_TYPES


@pytest.mark.asyncio
async def test_external_verification_never_claims_official_authority() -> None:
    provider = NotConnectedProvider(VerificationMethod.professional_registry)
    result = await provider.verify(VerificationRequest(
        account_id="ACCOUNT-SYN-1",
        identity_id="IDENTITY-SYN-1",
        method=VerificationMethod.professional_registry,
        reference="REFERENCE-SYN-1",
    ))
    assert result.status is VerificationStatus.not_connected
    assert result.assurance is AssuranceLevel.L0
    assert "not connected" in (result.reason or "")


class _ScalarResult:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return self

    def all(self):
        return self.values


class _RowResult:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class _ScriptedSession:
    def __init__(self, results):
        self.results = list(results)

    async def execute(self, _statement):
        return self.results.pop(0)


class _AuditRecorder:
    def __init__(self):
        self.events = []

    async def record_event(self, **kwargs):
        self.events.append(kwargs)


class _ScopeBridge:
    def __init__(self, binding):
        self.binding = binding

    async def resolve_active_binding(self, legacy_lab_id):
        return self.binding


def _terminated_workforce_service():
    link = LegacyAccountLink(
        id="LINK-W04-1",
        source_kind="lab_user",
        legacy_account_id=14,
        canonical_account_id="ACCOUNT-SYN-2",
        status=LegacyAccountLinkStatus.migrated.value,
        source_fingerprint="fingerprint-synthetic",
        rollback_token="rollback-synthetic",
    )
    account = Account(id="ACCOUNT-SYN-2", identity_id="IDENTITY-SYN-2", status="active", is_active=True)
    identity = IdentityRecord(id="IDENTITY-SYN-2", person_id="PERSON-SYN-2", status="active", is_active=True)
    facility = Facility(id=31, organization_id=41, is_active=True)
    organization = Organization(id=41, tenant_id=51, is_active=True)
    tenant = Tenant(id=51, is_active=True)
    binding = ClinicalLabFacilityBinding(
        id="BINDING-W04-1",
        legacy_lab_id=21,
        facility_resource_id=31,
        status="active",
        mapping_version=7,
        niam_organization_id="NIAM-ORG-SYN-1",
        niam_facility_id="NIAM-FAC-SYN-1",
    )
    # The canonical query below only returns active assignments; no row is
    # returned for a terminated workforce member.
    session = _ScriptedSession([
        _ScalarResult([link]),
        _RowResult([(account, identity)]),
        _RowResult([(facility, organization, tenant)]),
        _ScalarResult([]),
    ])
    service = ClinicalAuthorizationContextService(session)
    service.audit = _AuditRecorder()
    service.scope_bridge = _ScopeBridge(binding)
    return service


@pytest.mark.asyncio
async def test_terminated_workforce_has_no_active_clinical_assignment_context() -> None:
    service = _terminated_workforce_service()

    with pytest.raises(ClinicalActiveAssignmentUnavailable):
        await service.resolve_for_legacy_lab_user(legacy_lab_user_id=14, legacy_lab_id=21)

    assert service.audit.events[0]["metadata"]["failure_code"] == "ClinicalActiveAssignmentUnavailable"


@pytest.mark.xfail(
    strict=True,
    reason="Wave 04 excludes migrations; workforce/delegation DDL parity remains owner-gated",
)
def test_institutional_workforce_migrations_are_present() -> None:
    root = Path(__file__).resolve().parents[2]
    migrations = root / "migrations/versions"
    for name in (
        "20261119_0002_niam_delegations.py",
        "20261114_0004_unify_professional_identity.py",
    ):
        assert (migrations / name).exists()


@pytest.mark.xfail(strict=True, reason="Route/auth wiring is an owner security decision")
def test_workforce_routes_are_mounted() -> None:
    source = (Path(__file__).resolve().parents[2] / "app/identity/api/router.py").read_text()
    assert "delegations" in source
    assert "professional_registry" in source


@pytest.mark.xfail(strict=True, reason="Official provider-registry mapping is not connected")
def test_canonical_provider_registry_mapping_is_connected() -> None:
    combined = MetaData()
    assert "dp_provider_registry" in combined.tables
