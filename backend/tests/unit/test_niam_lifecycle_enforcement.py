"""PROGRAM-05 v5.0 — National Identity Platform enforcement tests.

Covers the production enforcement wired in this program:
  1. Account lifecycle: suspended/deactivated never authenticate (Rule 10).
  2. Auditable state machine transitions (Rule 10/13, Appendix-B).
  3. Session policy: concurrent limit enforced on login, oldest session
     terminated (Rule 8/9), block when not allowed to terminate.
  4. NIAM AuthorizationService: real RBAC resolution via shared model +
     organization isolation + professional-license gating (Rule 3,
     Appendix-B automatic revocation).
  5. Audit events on login success/failure, session start/termination.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from app._compat import UTC
from app.identity.adaptive_auth.models import SessionPolicy
from app.identity.adaptive_auth.services import SessionGovernanceService
from app.identity.models.account import Account, AccountStatus
from app.identity.models.assignment import Assignment
from app.identity.models.audit import AuditAction
from app.identity.models.license import ProfessionalLicense
from app.identity.models.session import UserSession
from app.identity.services.account_service import AccountService
from app.identity.services.authentication_service import AuthenticationService
from app.identity.services.authorization_service import AuthorizationService
from app.security.auth import hash_password


def _account(**kw) -> Account:
    defaults = dict(
        id=...,
        uuid=str(uuid.uuid4()),
        identity_id="identity-1",
        account_type="human",
        status=AccountStatus.active.value,
        password_hash=hash_password("SecurePass123!@#"),
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
    )
    defaults.update(kw)
    return Account(**defaults)


def _policy(**kw) -> SessionPolicy:
    defaults = dict(
        id=...,
        uuid=str(uuid.uuid4()),
        policy_id="citizen-default",
        name="Citizen default",
        applies_to="human",
        max_sessions=1,
        allow_concurrent=False,
        require_mfa=False,
        notify_previous_device=True,
        terminate_previous_on_new_login=True,
        is_active=True,
    )
    defaults.update(kw)
    return SessionPolicy(**defaults)


class TestAccountLifecycleAuthentication:
    @pytest.mark.asyncio
    async def test_suspended_account_never_authenticates(self):
        session = MagicMock()
        session.flush = AsyncMock()
        account = _account(status=AccountStatus.suspended.value, email="s@test.local")
        svc = AccountService(session)
        with patch.object(svc.repo, "find_by_email", new_callable=AsyncMock) as m:
            m.return_value = account
            result = await svc.authenticate("s@test.local", "SecurePass123!@#")
        assert result is None

    @pytest.mark.asyncio
    async def test_deactivated_account_never_authenticates(self):
        session = MagicMock()
        session.flush = AsyncMock()
        account = _account(status=AccountStatus.deactivated.value, email="d@test.local")
        svc = AccountService(session)
        with patch.object(svc.repo, "find_by_email", new_callable=AsyncMock) as m:
            m.return_value = account
            result = await svc.authenticate("d@test.local", "SecurePass123!@#")
        assert result is None

    @pytest.mark.asyncio
    async def test_pending_verification_can_login_limited(self):
        session = MagicMock()
        session.flush = AsyncMock()
        account = _account(status=AccountStatus.pending_verification.value, email="p@test.local")
        svc = AccountService(session)
        with patch.object(svc.repo, "find_by_email", new_callable=AsyncMock) as m:
            m.return_value = account
            result = await svc.authenticate("p@test.local", "SecurePass123!@#")
        assert result is not None
        assert result.status == AccountStatus.pending_verification.value

    @pytest.mark.asyncio
    async def test_locked_account_denied_until_expiry(self):
        session = MagicMock()
        session.flush = AsyncMock()
        account = _account(
            status=AccountStatus.active.value,
            email="l@test.local",
            is_locked=True,
            locked_until=datetime.now(UTC) + timedelta(minutes=10),
        )
        svc = AccountService(session)
        with patch.object(svc.repo, "find_by_email", new_callable=AsyncMock) as m:
            m.return_value = account
            result = await svc.authenticate("l@test.local", "SecurePass123!@#")
        assert result is None


class TestAccountLifecycleTransitions:
    @pytest.mark.asyncio
    async def test_suspend_transition_allowed_and_audited(self):
        session = MagicMock()
        session.flush = AsyncMock()
        account = _account()
        svc = AccountService(session)
        with patch.object(svc.repo, "get_by_id", new_callable=AsyncMock) as m, patch.object(
            svc, "_audit_transition", new_callable=AsyncMock
        ) as audit:
            m.return_value = account
            result = await svc.suspend_account(account.id, "policy violation", "admin-1")
        assert result is not None
        assert account.status == AccountStatus.suspended.value
        audit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invalid_transition_rejected(self):
        session = MagicMock()
        session.flush = AsyncMock()
        account = _account(status=AccountStatus.deactivated.value)
        svc = AccountService(session)
        with patch.object(svc.repo, "get_by_id", new_callable=AsyncMock) as m:
            m.return_value = account
            result = await svc.deactivate_account(account.id, "already deactivated")
        assert result is None
        assert account.status == AccountStatus.deactivated.value

    @pytest.mark.asyncio
    async def test_activate_restores_operational_state(self):
        session = MagicMock()
        session.flush = AsyncMock()
        account = _account(status=AccountStatus.suspended.value)
        svc = AccountService(session)
        with patch.object(svc.repo, "get_by_id", new_callable=AsyncMock) as m, patch.object(
            svc, "_audit_transition", new_callable=AsyncMock
        ):
            m.return_value = account
            result = await svc.activate_account(account.id, "restored after review")
        assert result is not None
        assert account.status == AccountStatus.active.value
        assert account.activated_at is not None


class TestSessionPolicyEnforcement:
    @pytest.mark.asyncio
    async def test_oldest_session_terminated_when_limit_exceeded(self):
        session = MagicMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        policy = _policy(max_sessions=1)
        old = UserSession(
            id="old-1",
            uuid=str(uuid.uuid4()),
            account_id="a1",
            token_jti="jti-old",
            session_type="web",
            is_active=True,
            started_at=datetime.now(UTC) - timedelta(hours=2),
            last_activity_at=datetime.now(UTC) - timedelta(hours=1),
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        svc = SessionGovernanceService(session)

        def fake_execute(stmt):
            result = MagicMock()
            if isinstance(stmt, select):
                pass
            result.scalars.return_value.all.return_value = [old]
            return result

        session.execute.side_effect = fake_execute
        with patch.object(
            svc, "get_session_policy", new_callable=AsyncMock, return_value=policy
        ), patch.object(
            svc, "get_active_session_count", new_callable=AsyncMock, return_value=1
        ), patch.object(
            svc, "terminate_previous_sessions", new_callable=AsyncMock, return_value=1
        ):
            result = await svc.enforce_session_policy("a1", "human")
        assert result["action"] == "terminated_previous"
        assert result["policy_id"] == "citizen-default"

    @pytest.mark.asyncio
    async def test_login_blocks_when_policy_forbids_termination(self):
        session = MagicMock()
        policy = _policy(terminate_previous_on_new_login=False, max_sessions=1)
        svc = SessionGovernanceService(session)
        with patch.object(
            svc, "get_session_policy", new_callable=AsyncMock, return_value=policy
        ), patch.object(
            svc, "get_active_session_count", new_callable=AsyncMock, return_value=1
        ):
            result = await svc.enforce_session_policy("a1", "human")
        assert result["action"] == "block_new_session"

    @pytest.mark.asyncio
    async def test_multisession_limit_keeps_newest(self):
        session = MagicMock()
        session.execute = AsyncMock()
        session.flush = AsyncMock()
        policy = _policy(max_sessions=2, allow_concurrent=True)
        svc = SessionGovernanceService(session)
        with patch.object(
            svc, "get_session_policy", new_callable=AsyncMock, return_value=policy
        ), patch.object(
            svc, "get_active_session_count", new_callable=AsyncMock, return_value=2
        ), patch.object(
            svc, "terminate_previous_sessions", new_callable=AsyncMock, return_value=1
        ):
            result = await svc.enforce_session_policy("a1", "human")
        assert result["action"] == "terminated_previous"


class TestLoginAuditWiring:
    @pytest.mark.asyncio
    async def test_login_success_audited_and_mfa_flagged(self):
        session = MagicMock()
        session.flush = AsyncMock()
        account = _account(mfa_enabled=True, email="a@test.local")
        svc = AuthenticationService(session)
        with patch.object(
            svc.account_service, "authenticate", new_callable=AsyncMock, return_value=account
        ), patch.object(
            svc.session_governance,
            "enforce_session_policy",
            new_callable=AsyncMock,
            return_value={"enforced": True, "action": "allowed", "policy_id": "p-1"},
        ), patch.object(svc, "_audit", new_callable=AsyncMock) as audit, patch.object(
            svc.session_repo, "create", new_callable=AsyncMock
        ) as create:
            result = await svc.login("a@test.local", "SecurePass123!@#")
        assert result is not None
        audit.assert_awaited()
        actions = [c.kwargs["action"] for c in audit.await_args_list]
        assert "login_succeeded" in actions
        assert "session_started" in actions
        created = create.await_args.args[0]
        assert created.mfa_used is True
        assert created.policy_id == "p-1"

    @pytest.mark.asyncio
    async def test_login_failure_audited(self):
        session = MagicMock()
        svc = AuthenticationService(session)
        with patch.object(
            svc.account_service, "authenticate", new_callable=AsyncMock, return_value=None
        ), patch.object(
            svc.account_service, "find_by_email", new_callable=AsyncMock, return_value=None
        ), patch.object(
            svc.account_service, "find_by_username", new_callable=AsyncMock, return_value=None
        ), patch.object(svc, "_audit", new_callable=AsyncMock) as audit:
            result = await svc.login("bad@test.local", "wrong")
        assert result is None
        assert audit.await_args.kwargs["action"] == "login_failed"

    @pytest.mark.asyncio
    async def test_login_failure_unknown_account_audits_no_target(self):
        session = MagicMock()
        svc = AuthenticationService(session)
        with patch.object(
            svc.account_service, "authenticate", new_callable=AsyncMock, return_value=None
        ), patch.object(
            svc.account_service, "find_by_email", new_callable=AsyncMock, return_value=None
        ), patch.object(
            svc.account_service, "find_by_username", new_callable=AsyncMock, return_value=None
        ), patch.object(svc, "_audit", new_callable=AsyncMock) as audit:
            await svc.login("nobody@test.local", "wrong")
        assert audit.await_args.kwargs["target_id"] is None

    @pytest.mark.asyncio
    async def test_login_failure_blocked_account_audits_target(self):
        session = MagicMock()
        account = _account(email="blocked@test.local")
        svc = AuthenticationService(session)
        with patch.object(
            svc.account_service, "authenticate", new_callable=AsyncMock, return_value=None
        ), patch.object(
            svc.account_service, "find_by_email", new_callable=AsyncMock, return_value=account
        ), patch.object(
            svc.account_service, "find_by_username", new_callable=AsyncMock, return_value=None
        ), patch.object(svc, "_audit", new_callable=AsyncMock) as audit:
            await svc.login("blocked@test.local", "wrong")
        assert audit.await_args.kwargs["target_id"] == account.id

    @pytest.mark.asyncio
    async def test_session_policy_block_denies_login(self):
        session = MagicMock()
        account = _account(email="b@test.local")
        svc = AuthenticationService(session)
        with patch.object(
            svc.account_service, "authenticate", new_callable=AsyncMock, return_value=account
        ), patch.object(
            svc.session_governance,
            "enforce_session_policy",
            new_callable=AsyncMock,
            return_value={"action": "block_new_session"},
        ), patch.object(svc, "_audit", new_callable=AsyncMock):
            result = await svc.login("b@test.local", "SecurePass123!@#")
        assert result is None


class TestNiamAuthorizationRbac:
    @pytest.mark.asyncio
    async def test_permission_resolved_from_shared_model(self):
        session = MagicMock()
        assignment = Assignment(
            id="a-1",
            uuid=str(uuid.uuid4()),
            employment_id="e-1",
            person_id="p-1",
            role_id="lab_manager",
            assignment_type="primary",
            status="active",
            start_date=date.today(),
            is_active=True,
        )
        svc = AuthorizationService(session)
        with patch.object(
            svc.assignment_repo, "find_by_person_id", new_callable=AsyncMock
        ) as m, patch.object(svc, "_is_license_ok", new_callable=AsyncMock, return_value=True):
            m.return_value = [assignment]
            assert await svc.has_permission("p-1", "results:read") is True
            assert await svc.has_permission("p-1", "system:admin") is False

    @pytest.mark.asyncio
    async def test_organization_isolation_enforced(self):
        session = MagicMock()
        assignment = Assignment(
            id="a-1",
            uuid=str(uuid.uuid4()),
            employment_id="e-1",
            person_id="p-1",
            organization_id="org-1",
            role_id="lab_manager",
            assignment_type="primary",
            status="active",
            start_date=date.today(),
            is_active=True,
        )
        svc = AuthorizationService(session)
        with patch.object(
            svc.assignment_repo, "find_by_person_id", new_callable=AsyncMock
        ) as m, patch.object(svc, "_is_license_ok", new_callable=AsyncMock, return_value=True):
            m.return_value = [assignment]
            assert await svc.has_permission("p-1", "results:read", "org-1") is True
            assert await svc.has_permission("p-1", "results:read", "org-other") is False

    @pytest.mark.asyncio
    async def test_expired_license_revokes_professional_permissions(self):
        session = MagicMock()
        session.execute = AsyncMock()
        assignment = Assignment(
            id="a-1",
            uuid=str(uuid.uuid4()),
            employment_id="e-1",
            person_id="p-1",
            role_id="doctor",
            assignment_type="primary",
            status="active",
            start_date=date.today(),
            is_active=True,
        )
        expired = ProfessionalLicense(
            id="lic-1",
            uuid=str(uuid.uuid4()),
            person_id="p-1",
            license_type="medical",
            license_number="LIC-1",
            license_name="Medical License",
            issuing_authority="Syndicate",
            issue_date=date(2020, 1, 1),
            expiry_date=date(2025, 1, 1),
            status="active",
            verified=True,
            is_active=True,
        )
        result = MagicMock()
        result.scalars.return_value.all.return_value = [expired]
        session.execute.return_value = result
        svc = AuthorizationService(session)
        with patch.object(
            svc.assignment_repo, "find_by_person_id", new_callable=AsyncMock
        ) as m:
            m.return_value = [assignment]
            assert await svc.has_permission("p-1", "results:read") is False

    @pytest.mark.asyncio
    async def test_valid_verified_license_grants_professional_permissions(self):
        session = MagicMock()
        session.execute = AsyncMock()
        assignment = Assignment(
            id="a-1",
            uuid=str(uuid.uuid4()),
            employment_id="e-1",
            person_id="p-1",
            role_id="doctor",
            assignment_type="primary",
            status="active",
            start_date=date.today(),
            is_active=True,
        )
        valid = ProfessionalLicense(
            id="lic-1",
            uuid=str(uuid.uuid4()),
            person_id="p-1",
            license_type="medical",
            license_number="LIC-2",
            license_name="Medical License",
            issuing_authority="Syndicate",
            issue_date=date(2020, 1, 1),
            expiry_date=date(2035, 1, 1),
            status="active",
            verified=True,
            is_active=True,
        )
        result = MagicMock()
        result.scalars.return_value.all.return_value = [valid]
        session.execute.return_value = result
        svc = AuthorizationService(session)
        with patch.object(
            svc.assignment_repo, "find_by_person_id", new_callable=AsyncMock
        ) as m:
            m.return_value = [assignment]
            assert await svc.has_permission("p-1", "results:read") is True


class TestAuditActionCoverage:
    def test_login_and_status_actions_exist(self):
        for name in (
            "login_succeeded",
            "login_failed",
            "logout_succeeded",
            "account_status_changed",
            "account_suspended",
            "account_restored",
            "account_deactivated",
        ):
            assert AuditAction(name).value == name
