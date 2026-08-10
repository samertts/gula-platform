"""A6 — Identity lifecycle hardening.

The account lifecycle follows provisioned -> active -> suspended ->
revoked/retired, with terminal revoked/retired states, session/token
invalidation on every de-operational transition, immutable audit history
(no deletion), and enforcement at authentication and token resolution.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.identity.models.account import Account, AccountStatus
from app.identity.models.audit import AuditAction
from app.identity.services.account_service import AccountService


def _account(**kw) -> Account:
    defaults = {
        "id": "acct-1",
        "uuid": "00000000-0000-0000-0000-000000000001",
        "identity_id": "identity-1",
        "account_type": "human",
        "status": AccountStatus.active.value,
        "password_hash": "hash",
        "is_active": True,
        "is_locked": False,
        "failed_login_attempts": 0,
    }
    defaults.update(kw)
    return Account(**defaults)


def _service(account: Account, session=None) -> AccountService:
    session = session or MagicMock()
    session.flush = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=result)
    svc = AccountService(session)
    svc.repo.get_by_id = AsyncMock(return_value=account)
    return svc


class TestTerminalStates:
    async def test_revoked_is_terminal(self):
        account = _account(status=AccountStatus.revoked.value)
        svc = _service(account)
        assert await svc.activate_account(account.id, "try revive") is None
        assert account.status == AccountStatus.revoked.value

    async def test_retired_is_terminal(self):
        account = _account(status=AccountStatus.retired.value)
        svc = _service(account)
        assert await svc.revoke_account(account.id, "late revoke") is None
        assert account.status == AccountStatus.retired.value

    async def test_active_can_be_revoked(self):
        account = _account()
        svc = _service(account)
        with patch.object(svc, "_audit_transition", new_callable=AsyncMock):
            result = await svc.revoke_account(account.id, "fraud", "admin-1")
        assert result is not None
        assert account.status == AccountStatus.revoked.value
        assert account.is_active is False
        assert account.deactivation_reason == "fraud"

    async def test_active_can_be_retired(self):
        account = _account()
        svc = _service(account)
        with patch.object(svc, "_audit_transition", new_callable=AsyncMock):
            result = await svc.retire_account(account.id, "age retirement")
        assert result is not None
        assert account.status == AccountStatus.retired.value
        assert account.is_active is False

    async def test_suspended_can_be_retired(self):
        account = _account(status=AccountStatus.suspended.value)
        svc = _service(account)
        with patch.object(svc, "_audit_transition", new_callable=AsyncMock):
            result = await svc.retire_account(account.id, "suspension upheld")
        assert result is not None
        assert account.status == AccountStatus.retired.value


class TestSessionInvalidation:
    async def test_suspend_invalidates_sessions(self):
        account = _account()
        session = MagicMock()
        session.flush = AsyncMock()
        active = [_account() for _ in range(2)]
        svc = _service(account, session)
        with (
            patch.object(svc, "_audit_transition", new_callable=AsyncMock),
            patch("app.identity.services.account_service.SessionService") as session_service_cls,
        ):
            instance = session_service_cls.return_value
            instance.get_active_sessions = AsyncMock(return_value=active)
            instance.terminate_all = AsyncMock()
            with patch("app.identity.services.account_service.AuditService") as audit_cls:
                audit_cls.return_value.record = AsyncMock()
                result = await svc.suspend_account(account.id, "breach")
        assert result is not None
        instance.terminate_all.assert_awaited_once()
        audit_cls.return_value.record.assert_awaited_once()
        args = audit_cls.return_value.record.await_args
        assert args.kwargs["action"] is AuditAction.account_sessions_invalidated
        assert args.kwargs["metadata"]["sessions_terminated"] == 2

    async def test_revoke_invalidates_sessions(self):
        account = _account()
        session = MagicMock()
        session.flush = AsyncMock()
        svc = _service(account, session)
        with (
            patch.object(svc, "_audit_transition", new_callable=AsyncMock),
            patch("app.identity.services.account_service.SessionService") as session_service_cls,
        ):
            instance = session_service_cls.return_value
            instance.get_active_sessions = AsyncMock(return_value=[_account()])
            instance.terminate_all = AsyncMock()
            with patch("app.identity.services.account_service.AuditService") as audit_cls:
                audit_cls.return_value.record = AsyncMock()
                await svc.revoke_account(account.id, "breach")
        instance.terminate_all.assert_awaited_once()

    async def test_activate_does_not_invalidate_sessions(self):
        account = _account(status=AccountStatus.suspended.value)
        session = MagicMock()
        session.flush = AsyncMock()
        svc = _service(account, session)
        with (
            patch.object(svc, "_audit_transition", new_callable=AsyncMock),
            patch("app.identity.services.account_service.SessionService") as session_service_cls,
        ):
            instance = session_service_cls.return_value
            instance.terminate_all = AsyncMock()
            await svc.activate_account(account.id, "review cleared")
            instance.terminate_all.assert_not_awaited()

    async def test_invalidation_survives_mock_session_without_lists(self):
        # Legacy callers that stub only repo.get_by_id + flush must not break:
        # a MagicMock session yields a non-list for get_active_sessions.
        account = _account()
        session = MagicMock()
        session.flush = AsyncMock()
        svc = _service(account, session)
        with (
            patch.object(svc, "_audit_transition", new_callable=AsyncMock),
            patch("app.identity.services.account_service.SessionService") as session_service_cls,
        ):
            instance = session_service_cls.return_value
            instance.get_active_sessions = AsyncMock(return_value=MagicMock())
            instance.terminate_all = AsyncMock()
            with patch("app.identity.services.account_service.AuditService") as audit_cls:
                audit_cls.return_value.record = AsyncMock()
                result = await svc.suspend_account(account.id, "breach")
        assert result is not None


class TestHistoryPreserved:
    async def test_transition_history_audited_not_deleted(self):
        account = _account()
        session = MagicMock()
        session.flush = AsyncMock()
        svc = _service(account, session)
        with patch("app.identity.services.account_service.SessionService") as session_service_cls:
            instance = session_service_cls.return_value
            instance.get_active_sessions = AsyncMock(return_value=[])
            instance.terminate_all = AsyncMock()
            with patch("app.identity.services.account_service.AuditService") as audit_cls:
                audit_cls.return_value.record = AsyncMock()
                result = await svc.revoke_account(account.id, "fraud", "admin-1")
        assert result is not None
        action = result[1]
        assert action == "account_revoked"
        assert AuditAction(action).value == action


class TestAuthenticationBlocked:
    async def test_revoked_account_never_authenticates(self):
        session = MagicMock()
        session.flush = AsyncMock()
        account = _account(status=AccountStatus.revoked.value, email="r@test.local")
        svc = AccountService(session)
        with patch.object(svc.repo, "find_by_email", new_callable=AsyncMock) as m:
            m.return_value = account
            result = await svc.authenticate("r@test.local", "whatever")
        assert result is None

    async def test_retired_account_never_authenticates(self):
        session = MagicMock()
        session.flush = AsyncMock()
        account = _account(status=AccountStatus.retired.value, email="rt@test.local")
        svc = AccountService(session)
        with patch.object(svc.repo, "find_by_email", new_callable=AsyncMock) as m:
            m.return_value = account
            result = await svc.authenticate("rt@test.local", "whatever")
        assert result is None
