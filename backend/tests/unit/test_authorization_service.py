"""Unit tests for authorization_service — RBAC/ABAC decision engine, policies, legacy roles."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.models.authorization import (
    AuthorizationAudit,
    BreakGlassSession,
    Permission,
    Policy,
    Role,
    RoleAssignment,
    RolePermission,
)
from app.models.user import User
from app.services.authorization_service import (
    AuthorizationCheckService,
    PolicyService,
)
from sqlalchemy.orm import Session


@pytest.fixture()
def user(db: Session) -> User:
    u = User(
        full_name="Test User",
        role="lab_manager",
        email="authz@test.local",
        password_hash="x",
    )
    db.add(u)
    db.flush()
    return u


def _make_permission(
    db: Session,
    permission_id: str = "lab.patient.read",
    domain: str = "lab",
    requires_mfa: bool = False,
    requires_justification: bool = False,
    is_sensitive: bool = False,
) -> Permission:
    perm = Permission(
        permission_id=permission_id,
        name_en=permission_id,
        name_ar=permission_id,
        domain=domain,
        resource="patient",
        action="read",
        is_sensitive=is_sensitive,
        requires_mfa=requires_mfa,
        requires_justification=requires_justification,
    )
    db.add(perm)
    db.flush()
    return perm


def _grant_role(db: Session, user: User, role_id: str = "lab_manager") -> Role:
    role = Role(role_id=role_id, name_en=role_id, name_ar=role_id)
    db.add(role)
    db.flush()
    db.add(RoleAssignment(user_id=user.id, role_id=role_id, status="active"))
    db.flush()
    return role


class TestCheckPermission:
    def test_unknown_permission_denied(self, db, user):
        result = AuthorizationCheckService(db).check_permission(user, "does.not.exist")
        assert result["decision"] == "deny"
        assert result["reason"] == "Permission not found"
        audit = db.query(AuthorizationAudit).filter_by(decision_id=result["decision_id"]).first()
        assert audit is not None and audit.decision == "deny"

    def test_no_roles_denied(self, db, user):
        _make_permission(db)
        result = AuthorizationCheckService(db).check_permission(user, "lab.patient.read")
        assert result["decision"] == "deny"
        assert result["reason"] == "No roles assigned"

    def test_role_without_permission_denied(self, db, user):
        _make_permission(db)
        _grant_role(db, user)
        result = AuthorizationCheckService(db).check_permission(user, "lab.patient.read")
        assert result["decision"] == "deny"
        assert result["reason"] == "Permission not assigned"

    def test_role_with_permission_allowed(self, db, user):
        _make_permission(db)
        role = _grant_role(db, user)
        db.add(RolePermission(role_id=role.role_id, permission_id="lab.patient.read"))
        db.flush()
        result = AuthorizationCheckService(db).check_permission(user, "lab.patient.read")
        assert result["decision"] == "allow"
        assert result["is_sensitive"] is False

    def test_legacy_role_string_grants(self, db):
        _make_permission(db, permission_id="patients:read", domain="patients")
        admin = User(
            full_name="Admin", role="admin", email="legacy@test.local", password_hash="x"
        )
        db.add(admin)
        db.flush()
        role = Role(role_id="admin_role", name_en="x", name_ar="x")
        db.add(role)
        db.add(RoleAssignment(user_id=admin.id, role_id="admin_role", status="active"))
        db.flush()
        result = AuthorizationCheckService(db).check_permission(admin, "patients:read")
        assert result["decision"] == "allow"

    def test_inactive_assignment_not_counted(self, db, user):
        _make_permission(db)
        role = Role(role_id="other_role", name_en="x", name_ar="x")
        db.add(role)
        db.flush()
        db.add(RoleAssignment(user_id=user.id, role_id="other_role", status="revoked"))
        db.flush()
        db.add(RolePermission(role_id="other_role", permission_id="lab.patient.read"))
        db.flush()
        result = AuthorizationCheckService(db).check_permission(user, "lab.patient.read")
        assert result["decision"] == "deny"

    def test_mfa_required_denied_without_mfa(self, db, user):
        _make_permission(db, requires_mfa=True)
        _grant_role(db, user)
        db.add(RolePermission(role_id="lab_manager", permission_id="lab.patient.read"))
        db.flush()
        result = AuthorizationCheckService(db).check_permission(user, "lab.patient.read")
        assert result["decision"] == "deny"
        assert result["reason"] == "MFA required for this permission"

    def test_mfa_required_allowed_with_mfa(self, db, user):
        _make_permission(db, requires_mfa=True)
        _grant_role(db, user)
        db.add(RolePermission(role_id="lab_manager", permission_id="lab.patient.read"))
        db.flush()
        user.mfa_enabled = True
        result = AuthorizationCheckService(db).check_permission(user, "lab.patient.read")
        assert result["decision"] == "allow"

    def test_justification_required(self, db, user):
        _make_permission(db, requires_justification=True)
        _grant_role(db, user)
        db.add(RolePermission(role_id="lab_manager", permission_id="lab.patient.read"))
        db.flush()
        denied = AuthorizationCheckService(db).check_permission(user, "lab.patient.read")
        assert denied["decision"] == "deny"
        assert denied["reason"] == "Justification required"
        allowed = AuthorizationCheckService(db).check_permission(
            user, "lab.patient.read", justification="clinical need"
        )
        assert allowed["decision"] == "allow"

    def test_abac_policy_denies(self, db, user):
        _make_permission(db)
        _grant_role(db, user)
        db.add(RolePermission(role_id="lab_manager", permission_id="lab.patient.read"))
        db.add(
            Policy(
                policy_id="p1",
                name_en="block governance",
                name_ar="block governance",
                status="published",
                effect="deny",
                priority=10,
                target={"resource": ["lab"], "action": ["read"], "roles": ["lab_manager"]},
            )
        )
        db.flush()
        result = AuthorizationCheckService(db).check_permission(
            user, "lab.patient.read", resource_attrs={"lab_id": 1}
        )
        assert result["decision"] == "deny"
        assert result["reason"] == "Denied by policy"
        assert result["policies_applied"][0]["policy_id"] == "p1"

    def test_abac_deny_ignores_non_matching_policy(self, db, user):
        _make_permission(db)
        _grant_role(db, user)
        db.add(RolePermission(role_id="lab_manager", permission_id="lab.patient.read"))
        db.add(
            Policy(
                policy_id="p2",
                name_en="block other",
                name_ar="block other",
                status="published",
                effect="deny",
                priority=10,
                target={"resource": ["radiology"], "action": ["write"]},
            )
        )
        db.flush()
        result = AuthorizationCheckService(db).check_permission(user, "lab.patient.read")
        assert result["decision"] == "allow"


class TestCheckMany:
    def test_all_granted(self, db, user):
        for pid in ("lab.patient.read", "lab.order.create"):
            _make_permission(db, pid)
        _grant_role(db, user)
        db.add(RolePermission(role_id="lab_manager", permission_id="lab.patient.read"))
        db.add(RolePermission(role_id="lab_manager", permission_id="lab.order.create"))
        db.flush()
        result = AuthorizationCheckService(db).check_many(
            user, ["lab.patient.read", "lab.order.create"]
        )
        assert result["granted"] is True
        assert all(r["decision"] == "allow" for r in result["results"].values())

    def test_partial_denial(self, db, user):
        _make_permission(db, "lab.patient.read")
        _make_permission(db, "lab.order.create")
        _grant_role(db, user)
        db.add(RolePermission(role_id="lab_manager", permission_id="lab.patient.read"))
        db.flush()
        result = AuthorizationCheckService(db).check_many(
            user, ["lab.patient.read", "lab.order.create"]
        )
        assert result["granted"] is False
        assert result["results"]["lab.order.create"]["decision"] == "deny"


class TestGetGrantedPermissions:
    def test_returns_assigned_and_legacy(self, db, user):
        _make_permission(db, "lab.patient.read")
        _make_permission(db, "lab.order.create")
        _make_permission(db, permission_id="patients:read", domain="patients")
        _grant_role(db, user)
        db.add(RolePermission(role_id="lab_manager", permission_id="lab.order.create"))
        db.add(RolePermission(role_id="lab_manager", permission_id="patients:read"))
        db.flush()
        granted = AuthorizationCheckService(db).get_granted_permissions(user)
        assert "lab.order.create" in granted
        assert "patients:read" in granted

    def test_domain_filter(self, db, user):
        _make_permission(db, "lab.patient.read")
        _make_permission(db, permission_id="lab.order.create")
        _make_permission(db, permission_id="patients:read", domain="patients")
        _grant_role(db, user)
        db.add(RolePermission(role_id="lab_manager", permission_id="lab.order.create"))
        db.add(RolePermission(role_id="lab_manager", permission_id="patients:read"))
        db.flush()
        granted = AuthorizationCheckService(db).get_granted_permissions(user, domain="lab")
        assert granted
        assert all(p.startswith("lab.") for p in granted)

    def test_no_roles_empty(self, db, user):
        assert AuthorizationCheckService(db).get_granted_permissions(user) == []


class TestPolicyService:
    def test_draft_policy_not_applied(self, db, user):
        _make_permission(db)
        _grant_role(db, user)
        db.add(RolePermission(role_id="lab_manager", permission_id="lab.patient.read"))
        db.add(
            Policy(
                policy_id="draft1",
                name_en="draft deny",
                name_ar="draft deny",
                status="draft",
                effect="deny",
                target={"resource": ["lab"]},
            )
        )
        db.flush()
        result = AuthorizationCheckService(db).check_permission(user, "lab.patient.read")
        assert result["decision"] == "allow"

    def test_no_policies_matches_nothing(self, db):
        subject = {"role": "lab_manager"}
        decision, applied = PolicyService(db).evaluate_policies(subject, "lab", "read")
        assert decision == "deny"
        assert applied == []

    def test_allow_policy_first(self, db):
        db.add(
            Policy(
                policy_id="allow1",
                name_en="allow",
                name_ar="allow",
                status="published",
                effect="allow",
                priority=5,
                target={"resource": ["lab"]},
            )
        )
        db.flush()
        decision, applied = PolicyService(db).evaluate_policies(
            {"role": "lab_manager"}, "lab", "read"
        )
        assert decision == "allow"
        assert applied[0]["policy_id"] == "allow1"

    def test_deny_wins_over_lower_priority_allow(self, db):
        db.add(
            Policy(
                policy_id="allow2",
                name_en="allow",
                name_ar="allow",
                status="published",
                effect="allow",
                priority=5,
                target={"resource": ["lab"]},
            )
        )
        db.add(
            Policy(
                policy_id="deny2",
                name_en="deny",
                name_ar="deny",
                status="published",
                effect="deny",
                priority=1,
                target={"resource": ["lab"]},
            )
        )
        db.flush()
        decision, applied = PolicyService(db).evaluate_policies(
            {"role": "lab_manager"}, "lab", "read"
        )
        assert decision == "deny"
        assert applied[0]["policy_id"] == "deny2"


class TestBreakGlass:
    def test_active_break_glass_marks_emergency(self, db, user):
        _make_permission(db)
        _grant_role(db, user)
        db.add(RolePermission(role_id="lab_manager", permission_id="lab.patient.read"))
        db.add(
            BreakGlassSession(
                user_id=user.id,
                emergency_category="patient_safety",
                justification="critical result",
                expires_at=datetime.now(UTC) + timedelta(hours=1),
                status="active",
            )
        )
        db.flush()
        result = AuthorizationCheckService(db).check_permission(user, "lab.patient.read")
        assert result["decision"] == "allow"
        assert result["is_emergency"] is True

    def test_expired_break_glass_not_emergency(self, db, user):
        _make_permission(db)
        _grant_role(db, user)
        db.add(RolePermission(role_id="lab_manager", permission_id="lab.patient.read"))
        db.add(
            BreakGlassSession(
                user_id=user.id,
                emergency_category="patient_safety",
                justification="critical result",
                expires_at=datetime.now(UTC) - timedelta(hours=1),
                status="active",
            )
        )
        db.flush()
        result = AuthorizationCheckService(db).check_permission(user, "lab.patient.read")
        assert result["is_emergency"] is False
