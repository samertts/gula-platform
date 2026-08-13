from __future__ import annotations

import pytest
from app.identity.models.assignment import Assignment
from app.identity.models.policy import IdentityPolicy
from app.identity.services.authorization_service import AuthorizationService


class _AssignmentRepository:
    def __init__(self, assignments):
        self.assignments = assignments

    async def find_by_person_id(self, person_id):
        assert person_id == "PERSON-1"
        return self.assignments


class _PolicyRepository:
    def __init__(self, policies):
        self.policies = policies

    async def find_enabled_for_action(self, permission):
        return [policy for policy in self.policies if permission in policy.actions]


def _assignment(**overrides):
    values = {
        "id": "ASSIGNMENT-1",
        "person_id": "PERSON-1",
        "role_id": "doctor",
        "status": "active",
        "is_active": True,
        "clinical_organization_resource_id": 41,
        "clinical_facility_resource_id": 31,
    }
    values.update(overrides)
    return Assignment(**values)


def _policy(*, effect="allow", facility_ids=None, action="clinical.ehr.record.read"):
    return IdentityPolicy(
        id="POLICY-1",
        policy_id="clinical-ehr-read",
        uuid="00000000-0000-0000-0000-000000000001",
        name="Clinical EHR read",
        policy_type="authorization",
        effect=effect,
        actions=[action],
        resources=[action.rsplit(".", 1)[0]],
        subjects={"role_ids": ["doctor"]},
        conditions={
            "clinical_organization_resource_ids": [41],
            "clinical_facility_resource_ids": facility_ids or [31],
        },
        created_by="SYSTEM",
        is_enabled=True,
        is_active=True,
    )


def _service(*, assignments=None, policies=None):
    service = AuthorizationService(session=None)
    service.assignment_repo = _AssignmentRepository(assignments or [_assignment()])
    service.policy_repo = _PolicyRepository(policies or [])
    return service


@pytest.mark.asyncio
async def test_exact_scoped_policy_allows_the_matching_assignment_only():
    service = _service(policies=[_policy()])

    allowed = await service.has_permission(
        person_id="PERSON-1",
        permission="clinical.ehr.record.read",
        organization_id="41",
        facility_resource_id=31,
    )

    assert allowed is True


@pytest.mark.asyncio
async def test_missing_exact_policy_denies_by_default():
    service = _service()

    allowed = await service.has_permission(
        person_id="PERSON-1",
        permission="clinical.ehr.record.read",
        organization_id="41",
        facility_resource_id=31,
    )

    assert allowed is False


@pytest.mark.asyncio
async def test_scope_mismatch_denies_even_when_role_policy_exists():
    service = _service(policies=[_policy(facility_ids=[99])])

    allowed = await service.has_permission(
        person_id="PERSON-1",
        permission="clinical.ehr.record.read",
        organization_id="41",
        facility_resource_id=31,
    )

    assert allowed is False


@pytest.mark.asyncio
async def test_matching_deny_policy_overrides_matching_allow_policy():
    service = _service(policies=[_policy(effect="allow"), _policy(effect="deny")])

    allowed = await service.has_permission(
        person_id="PERSON-1",
        permission="clinical.ehr.record.read",
        organization_id="41",
        facility_resource_id=31,
    )

    assert allowed is False
