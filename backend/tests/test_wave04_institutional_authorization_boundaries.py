"""Wave 04 — negative institutional authorization conformance.

Synthetic fixtures only. These tests assert fail-closed behavior of the
already-integrated canonical decision service; they add no new role,
permission, membership, route, policy or production behavior.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace

from app._compat import UTC
from app.identity.services.authorization_decision import (
    AuthorizationDecisionService,
    AuthorizationReason,
    AuthorizationRequest,
)
from app.identity.services.membership_service import MembershipService


class _ScalarResult:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return self

    def all(self):
        return self.values


class _ExecuteSession:
    def __init__(self, values):
        self.values = values

    async def execute(self, _statement):
        return _ScalarResult(self.values)


class _ScalarSession:
    def __init__(self, values):
        self.results = list(values)

    async def scalar(self, _statement):
        return self.results.pop(0)


def _request(**overrides):
    values = dict(
        subject_account_id="ACCOUNT-A",
        action="read",
        resource_type="patient_record",
        resource_id="PATIENT-SYN-1",
        permission_key="patient_record.read",
        organization_id="ORG-DIRECTORATE-A",
        facility_id="FACILITY-A",
        department_id="DEPT-A",
        unit_id=None,
        workspace_id=None,
        resource_context={
            "exists": True,
            "organization_id": "ORG-DIRECTORATE-A",
            "facility_id": "FACILITY-A",
            "department_id": "DEPT-A",
        },
    )
    values.update(overrides)
    return AuthorizationRequest(**values)


def _membership(**overrides):
    values = dict(
        id="MEMBERSHIP-A",
        organization_id="ORG-DIRECTORATE-A",
        facility_id="FACILITY-A",
        department_id="DEPT-A",
        unit_id=None,
        workspace_id=None,
        status="active",
        is_active=True,
        expires_at=None,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def _actor():
    return SimpleNamespace(account=SimpleNamespace(id="ACCOUNT-A"))


def test_directorate_a_cannot_access_directorate_b() -> None:
    result = AuthorizationDecisionService._check_scope(
        _request(
            organization_id="ORG-DIRECTORATE-B",
            facility_id="FACILITY-B",
            resource_context={
                "exists": True,
                "organization_id": "ORG-DIRECTORATE-B",
                "facility_id": "FACILITY-B",
            },
        ),
        _membership(),
    )
    assert result is AuthorizationReason.cross_tenant_denied


def test_facility_a_cannot_access_facility_b_in_same_ministry() -> None:
    result = AuthorizationDecisionService._check_scope(
        _request(
            facility_id="FACILITY-B",
            resource_context={
                "exists": True,
                "organization_id": "ORG-DIRECTORATE-A",
                "facility_id": "FACILITY-B",
            },
        ),
        _membership(),
    )
    assert result is AuthorizationReason.scope_mismatch


def test_same_ministry_hierarchy_does_not_override_facility_context() -> None:
    request = _request(resource_context={
        "exists": True,
        "organization_id": "ORG-DIRECTORATE-A",
        "facility_id": "FACILITY-B",
        "same_ministry": True,
    })
    assert AuthorizationDecisionService._check_resource_context(request) is AuthorizationReason.scope_mismatch
    assert AuthorizationDecisionService._check_scope(request, _membership()) is AuthorizationReason.scope_mismatch


def test_expired_membership_is_not_resolved_for_authorization() -> None:
    expired = _membership(expires_at=datetime.now(UTC) - timedelta(minutes=1))
    service = AuthorizationDecisionService(_ExecuteSession([expired]))

    resolved = asyncio.run(service._resolve_membership(_actor(), _request()))

    assert resolved is None


def test_active_membership_is_resolved_for_authorization() -> None:
    active = _membership(expires_at=datetime.now(UTC) + timedelta(hours=1))
    service = AuthorizationDecisionService(_ExecuteSession([active]))

    resolved = asyncio.run(service._resolve_membership(_actor(), _request()))

    assert resolved is active


def test_management_actions_require_organization_authority() -> None:
    assert AuthorizationDecisionService._requires_management_authority(
        _request(resource_type="membership", action="approve")
    ) is True
    assert AuthorizationDecisionService._requires_management_authority(
        _request(resource_type="patient_record", action="read")
    ) is False


def test_facility_admin_cannot_manage_national_organization() -> None:
    # The synthetic session has no active ownership or representative record
    # for ORG-NATIONAL; facility-level membership is irrelevant to this check.
    assert asyncio.run(
        MembershipService(_ScalarSession([None, None]))._can_manage_organization(
            "ACCOUNT-FACILITY-ADMIN", "ORG-NATIONAL"
        )
    ) is False


def test_exact_organization_authority_is_required() -> None:
    assert asyncio.run(
        MembershipService(_ScalarSession(["OWNERSHIP-SYN-1"]))._can_manage_organization(
            "ACCOUNT-A", "ORG-DIRECTORATE-A"
        )
    ) is True
