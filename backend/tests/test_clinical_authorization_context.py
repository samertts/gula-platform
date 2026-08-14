from __future__ import annotations

from datetime import date, timedelta

import pytest
from app.identity.models.account import Account
from app.identity.models.assignment import Assignment
from app.identity.models.identity import IdentityRecord
from app.identity.models.legacy_account_link import LegacyAccountLink, LegacyAccountLinkStatus
from app.identity.services.clinical_authorization_context_service import (
    ClinicalActiveAssignmentUnavailable,
    ClinicalAuthorizationContextAmbiguous,
    ClinicalAuthorizationContextService,
    ClinicalFacilityScopeMismatch,
    ClinicalIdentityAssignmentMismatch,
)
from app.models.clinical_scope import ClinicalLabFacilityBinding
from app.models.organization import Facility, Organization
from app.models.tenant import Tenant


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
        assert legacy_lab_id == 21
        return self.binding


def _service_with(
    *,
    assignment: Assignment,
    assignment_candidates: list[Assignment] | None = None,
):
    link = LegacyAccountLink(
        id="LINK-1",
        source_kind="lab_user",
        legacy_account_id=14,
        canonical_account_id="ACCOUNT-1",
        status=LegacyAccountLinkStatus.migrated.value,
        source_fingerprint="fingerprint",
        rollback_token="rollback-token",
    )
    account = Account(id="ACCOUNT-1", identity_id="IDENTITY-1", status="active", is_active=True)
    identity = IdentityRecord(id="IDENTITY-1", person_id="PERSON-1", status="active", is_active=True)
    facility = Facility(id=31, organization_id=41, is_active=True)
    organization = Organization(id=41, tenant_id=51, is_active=True)
    tenant = Tenant(id=51, is_active=True)
    binding = ClinicalLabFacilityBinding(
        id="BINDING-1",
        legacy_lab_id=21,
        facility_resource_id=31,
        status="active",
        mapping_version=7,
        niam_organization_id="NIAM-ORG-1",
        niam_facility_id="NIAM-FAC-1",
    )
    session = _ScriptedSession(
        [
            _ScalarResult([link]),
            _RowResult([(account, identity)]),
            _RowResult([(facility, organization, tenant)]),
            _ScalarResult(assignment_candidates if assignment_candidates is not None else [assignment]),
        ]
    )
    service = ClinicalAuthorizationContextService(session)
    service.audit = _AuditRecorder()
    service.scope_bridge = _ScopeBridge(binding)
    return service


def _assignment(**overrides):
    values = {
        "id": "ASSIGNMENT-1",
        "person_id": "PERSON-1",
        "status": "active",
        "is_active": True,
        "start_date": date.today() - timedelta(days=1),
        "end_date": None,
        "clinical_organization_resource_id": 41,
        "clinical_facility_resource_id": 31,
    }
    values.update(overrides)
    return Assignment(**values)


@pytest.mark.asyncio
async def test_resolves_only_a_complete_account_person_assignment_facility_chain():
    service = _service_with(assignment=_assignment())

    context = await service.resolve_for_legacy_lab_user(legacy_lab_user_id=14, legacy_lab_id=21)

    assert context.person_id == "PERSON-1"
    assert context.assignment_id == "ASSIGNMENT-1"
    assert context.facility_resource_id == 31
    assert context.organization_resource_id == 41
    assert context.tenant_id == 51
    assert service.audit.events == [
        {
            "action": "clinical_authorization_context_resolved",
            "target_type": "legacy_lab_user",
            "target_id": "14",
            "metadata": {
                "legacy_lab_id": 21,
                "assignment_id": "ASSIGNMENT-1",
                "facility_resource_id": 31,
                "organization_resource_id": 41,
                "tenant_id": 51,
                "scope_mapping_version": 7,
            },
            "outcome": "success",
        }
    ]


@pytest.mark.asyncio
async def test_rejects_when_the_active_assignment_belongs_to_a_different_person():
    service = _service_with(
        assignment=_assignment(),
        assignment_candidates=[_assignment(person_id="PERSON-OTHER")],
    )

    with pytest.raises(ClinicalIdentityAssignmentMismatch):
        await service.resolve_for_legacy_lab_user(legacy_lab_user_id=14, legacy_lab_id=21)

    assert service.audit.events[0]["action"] == "clinical_authorization_context_denied"
    assert service.audit.events[0]["metadata"]["failure_code"] == "ClinicalIdentityAssignmentMismatch"


@pytest.mark.asyncio
async def test_rejects_when_the_person_assignment_has_a_different_operational_scope():
    service = _service_with(
        assignment=_assignment(),
        assignment_candidates=[_assignment(clinical_facility_resource_id=999)],
    )

    with pytest.raises(ClinicalFacilityScopeMismatch):
        await service.resolve_for_legacy_lab_user(legacy_lab_user_id=14, legacy_lab_id=21)

    assert service.audit.events[0]["action"] == "clinical_authorization_context_denied"
    assert service.audit.events[0]["metadata"]["failure_code"] == "ClinicalFacilityScopeMismatch"


@pytest.mark.asyncio
async def test_rejects_when_no_active_assignment_is_available_for_the_canonical_person():
    service = _service_with(assignment=_assignment(), assignment_candidates=[])

    with pytest.raises(ClinicalActiveAssignmentUnavailable):
        await service.resolve_for_legacy_lab_user(legacy_lab_user_id=14, legacy_lab_id=21)

    assert service.audit.events[0]["metadata"]["failure_code"] == "ClinicalActiveAssignmentUnavailable"


@pytest.mark.asyncio
async def test_rejects_more_than_one_active_assignment_in_the_same_scope():
    service = _service_with(
        assignment=_assignment(),
        assignment_candidates=[_assignment(), _assignment(id="ASSIGNMENT-2")],
    )

    with pytest.raises(ClinicalAuthorizationContextAmbiguous):
        await service.resolve_for_legacy_lab_user(legacy_lab_user_id=14, legacy_lab_id=21)

    assert service.audit.events[0]["metadata"]["failure_code"] == "ClinicalAuthorizationContextAmbiguous"
