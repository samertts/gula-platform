from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from app._compat import UTC
from app.identity.models.account import Account, AccountStatus
from app.identity.models.membership import Membership, MembershipStatus
from app.identity.models.policy import IdentityPolicy
from app.identity.models.session import UserSession
from app.identity.policy_engine import PolicyContext, PolicyEngine
from app.identity.services.authorization_decision import (
    AuthorizationActor,
    AuthorizationDecisionService,
    AuthorizationReason,
    AuthorizationRequest,
)


class _Result:
    def __init__(self, values: list[object]) -> None:
        self.values = values

    def scalars(self) -> _Result:
        return self

    def all(self) -> list[object]:
        return self.values


class _AuthorizationSession:
    def __init__(
        self,
        *,
        membership: Membership | None = None,
        permission_exists: bool = True,
        effective_permissions: list[str] | None = None,
        policies: list[IdentityPolicy] | None = None,
        fail: bool = False,
    ) -> None:
        self.membership = membership
        self.permission_exists = permission_exists
        self.effective_permissions = effective_permissions or []
        self.policies = policies or []
        self.fail = fail

    def execute(self, statement):
        if self.fail:
            raise RuntimeError("simulated policy store failure")
        sql = str(statement)
        if "niam_memberships" in sql:
            return _Result([self.membership] if self.membership else [])
        if "niam_role_assignments" in sql:
            return _Result(self.effective_permissions)
        if "niam_policies" in sql:
            return _Result(self.policies)
        return _Result([])

    def scalar(self, statement):
        if self.fail:
            raise RuntimeError("simulated catalog failure")
        return "permission-id" if self.permission_exists else None

    def add(self, entry) -> None:
        del entry

    def flush(self) -> None:
        return None


def _actor(*, active: bool = True, mfa: bool = False) -> AuthorizationActor:
    account = Account(
        id="account-1",
        identity_id="identity-1",
        status=AccountStatus.active.value if active else AccountStatus.suspended.value,
        is_active=active,
        is_locked=False,
    )
    session = UserSession(
        id="session-1",
        account_id="account-1",
        is_active=active,
        mfa_used=mfa,
        started_at=datetime.now(UTC) - timedelta(minutes=5),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    return AuthorizationActor(account=account, session=session)


def _membership() -> Membership:
    return Membership(
        id="membership-1",
        account_id="account-1",
        organization_id="org-1",
        facility_id=None,
        department_id=None,
        unit_id=None,
        workspace_id=None,
        status=MembershipStatus.active.value,
        is_active=True,
        expires_at=None,
    )


def _request(**overrides) -> AuthorizationRequest:
    values = {
        "subject_account_id": "account-1",
        "action": "read",
        "resource_type": "lab_result",
        "resource_id": "result-1",
        "permission_key": "lab_result.read",
        "organization_id": "org-1",
        "resource_context": {"exists": True, "organization_id": "org-1"},
    }
    values.update(overrides)
    return AuthorizationRequest(**values)


def test_missing_trusted_actor_denies_compatibility_engine() -> None:
    result = PolicyEngine().evaluate(
        PolicyContext(subject_id="account-1", subject_type="account", action="read", resource_type="lab_result"),
    )
    assert result is False


def test_actor_mismatch_denies_before_database_access() -> None:
    service = AuthorizationDecisionService(_AuthorizationSession())
    decision = service._evaluate(_actor(), _request(subject_account_id="other-account"))
    assert decision.reason_code is AuthorizationReason.actor_mismatch


def test_inactive_account_denies() -> None:
    service = AuthorizationDecisionService(_AuthorizationSession())
    decision = service._evaluate(_actor(active=False), _request())
    assert decision.reason_code is AuthorizationReason.account_inactive


def test_resource_id_requires_server_resolution() -> None:
    service = AuthorizationDecisionService(_AuthorizationSession(membership=_membership(), effective_permissions=["lab_result.read"]))
    decision = service._evaluate(_actor(), _request(resource_context={"organization_id": "org-1"}))
    assert decision.reason_code is AuthorizationReason.resource_unresolved


def test_scope_mismatch_denies_cross_tenant_request() -> None:
    service = AuthorizationDecisionService(_AuthorizationSession())
    decision = service._evaluate(
        _actor(),
        _request(organization_id="org-2", resource_context={"exists": True, "organization_id": "org-2"}),
    )
    assert decision.reason_code is AuthorizationReason.membership_unresolved


def test_unknown_permission_denies() -> None:
    service = AuthorizationDecisionService(
        _AuthorizationSession(membership=_membership(), permission_exists=False),
    )
    decision = service._evaluate(_actor(), _request())
    assert decision.reason_code is AuthorizationReason.permission_unknown


def test_missing_effective_permission_denies() -> None:
    service = AuthorizationDecisionService(
        _AuthorizationSession(membership=_membership(), permission_exists=True, effective_permissions=[]),
    )
    decision = service._evaluate(_actor(), _request())
    assert decision.reason_code is AuthorizationReason.permission_missing


def test_active_rbac_and_context_allow() -> None:
    service = AuthorizationDecisionService(
        _AuthorizationSession(membership=_membership(), effective_permissions=["lab_result.read"]),
    )
    decision = service._evaluate(_actor(), _request())
    assert decision.allowed is True
    assert decision.reason_code is AuthorizationReason.allowed


def test_explicit_deny_policy_overrides_rbac_allow() -> None:
    deny = IdentityPolicy(
        policy_id="clinical-deny-v2",
        effect="deny",
        actions=["read"],
        resources=["lab_result"],
        priority=10,
        version="2.0",
        is_active=True,
        is_enabled=True,
    )
    allow = IdentityPolicy(
        policy_id="clinical-allow-v1",
        effect="allow",
        actions=["read"],
        resources=["lab_result"],
        priority=100,
        version="1.0",
        is_active=True,
        is_enabled=True,
    )
    service = AuthorizationDecisionService(
        _AuthorizationSession(
            membership=_membership(),
            effective_permissions=["lab_result.read"],
            policies=[allow, deny],
        ),
    )
    decision = service._evaluate(_actor(), _request())
    assert decision.reason_code is AuthorizationReason.policy_denied
    assert decision.policy_id == "clinical-deny-v2"
    assert decision.policy_version == "2.0"


def test_invalid_purpose_denies_without_fallback() -> None:
    service = AuthorizationDecisionService(_AuthorizationSession())
    decision = service._evaluate(
        _actor(),
        _request(purpose="UNTRUSTED_PURPOSE", purpose_validated=False),
    )
    assert decision.reason_code is AuthorizationReason.purpose_invalid


def test_sensitive_action_requires_mfa_step_up() -> None:
    service = AuthorizationDecisionService(
        _AuthorizationSession(membership=_membership(), effective_permissions=["lab_result.export"]),
    )
    decision = service._evaluate(
        _actor(mfa=False),
        _request(action="export", permission_key="lab_result.export", sensitivity="high"),
    )
    assert decision.reason_code is AuthorizationReason.step_up_required
    assert decision.required_assurance == "MFA"


def test_break_glass_is_not_an_admin_bypass() -> None:
    service = AuthorizationDecisionService(_AuthorizationSession())
    decision = service._evaluate(
        _actor(mfa=True),
        _request(
            break_glass=True,
            break_glass_authorized=False,
            environment={"break_glass_reason": "emergency"},
        ),
    )
    assert decision.reason_code is AuthorizationReason.break_glass_workflow_required


def test_database_failure_fails_closed() -> None:
    service = AuthorizationDecisionService(_AuthorizationSession(fail=True))
    decision = service.authorize(_actor(), _request())
    assert decision.allowed is False
    assert decision.reason_code is AuthorizationReason.internal_failure


def test_scope_helper_rejects_workspace_crossing() -> None:
    request = _request(workspace_id="workspace-2")
    membership = SimpleNamespace(
        organization_id="org-1",
        facility_id=None,
        department_id=None,
        unit_id=None,
        workspace_id="workspace-1",
    )
    reason = AuthorizationDecisionService._check_scope(request, membership)
    assert reason is AuthorizationReason.workspace_boundary_denied


def test_role_assignment_rejects_client_selected_account_mismatch() -> None:
    from app.identity.api.roles import RoleAssignmentRequest, assign_role
    from fastapi import HTTPException

    class _Db:
        def get(self, model, object_id):
            del model, object_id
            return _membership()

    with pytest.raises(HTTPException) as error:
        assign_role(
            RoleAssignmentRequest(
                account_id="attacker-account",
                membership_id="membership-1",
                role_id="role-1",
            ),
            _actor(),
            _Db(),
        )
    assert error.value.status_code == 403


def test_role_router_does_not_expose_internal_decision_helper() -> None:
    from app.identity.api.roles import router

    paths = {route.path for route in router.routes}
    assert "/roles/effective" in paths
    assert all("require_phase8_decision" not in path for path in paths)


def test_organization_scope_is_broader_than_explicit_workspace_scope() -> None:
    request = _request(workspace_id="workspace-2")
    organization_membership = SimpleNamespace(
        organization_id="org-1",
        facility_id=None,
        department_id=None,
        unit_id=None,
        workspace_id=None,
    )
    assert AuthorizationDecisionService._check_scope(request, organization_membership) is None


class _RelationshipSession(_AuthorizationSession):
    def __init__(self, relationship, **kwargs) -> None:
        super().__init__(**kwargs)
        self.relationship = relationship

    def execute(self, statement):
        if "niam_citizen_relationships" in str(statement):
            return _Result([self.relationship])
        return super().execute(statement)


def test_relationship_access_requires_explicit_scope_and_purpose() -> None:
    relationship = SimpleNamespace(
        patient_id="patient-1",
        citizen_id=None,
        purpose="citizen_workspace",
        is_active_at=lambda: True,
        allows=lambda resource, write=False: resource == "patient_record" and not write,
    )
    service = AuthorizationDecisionService(
        _RelationshipSession(
            relationship,
            membership=_membership(),
            effective_permissions=["patient_record.read"],
        ),
    )
    decision = service._evaluate(
        _actor(),
        _request(
            resource_type="patient_record",
            permission_key="patient_record.read",
            relationship_type="self",
            purpose="citizen_workspace",
            purpose_validated=True,
            resource_context={
                "exists": True,
                "organization_id": "org-1",
                "patient_id": "patient-1",
            },
        ),
    )
    assert decision.allowed is True


def test_relationship_purpose_mismatch_denies() -> None:
    relationship = SimpleNamespace(
        patient_id="patient-1",
        citizen_id=None,
        purpose="citizen_workspace",
        is_active_at=lambda: True,
        allows=lambda resource, write=False: True,
    )
    service = AuthorizationDecisionService(
        _RelationshipSession(
            relationship,
            membership=_membership(),
            effective_permissions=["patient_record.read"],
        ),
    )
    decision = service._evaluate(
        _actor(),
        _request(
            resource_type="patient_record",
            permission_key="patient_record.read",
            relationship_type="self",
            purpose="TREATMENT",
            purpose_validated=True,
            resource_context={
                "exists": True,
                "organization_id": "org-1",
                "patient_id": "patient-1",
            },
        ),
    )
    assert decision.reason_code is AuthorizationReason.relationship_denied
