from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from app._compat import UTC
from app.identity.models.account import AccountStatus
from app.identity.services.account_service import AccountService
from app.identity.services.authentication_service import AuthenticationService
from app.security.auth import _DUMMY_HASH


@pytest.mark.asyncio
async def test_authenticate_verifies_dummy_hash_for_unknown_login(monkeypatch):
    service = AccountService(AsyncMock())
    service.repo = AsyncMock()
    service.repo.find_by_login.return_value = None
    verify = Mock(return_value=False)
    monkeypatch.setattr("app.identity.services.account_service.verify_password", verify)

    assert await service.authenticate("unknown@example.test", "not-the-password") is None
    service.repo.find_by_login.assert_awaited_once_with("unknown@example.test")
    verify.assert_called_once_with("not-the-password", _DUMMY_HASH)


@pytest.mark.asyncio
async def test_authenticate_normalizes_phone_login_before_lookup(monkeypatch):
    service = AccountService(AsyncMock())
    service.repo = AsyncMock()
    service.repo.find_by_login.return_value = None
    verify = Mock(return_value=False)
    monkeypatch.setattr("app.identity.services.account_service.verify_password", verify)

    assert await service.authenticate(" +964 770 000 000 ", "not-the-password") is None
    service.repo.find_by_login.assert_awaited_once_with("+964770000000")
    verify.assert_called_once_with("not-the-password", _DUMMY_HASH)


@pytest.mark.asyncio
async def test_permanent_locked_account_is_not_unlocked_by_login_attempt(monkeypatch):
    service = AccountService(AsyncMock())
    session = AsyncMock()
    account = SimpleNamespace(
        status=AccountStatus.locked.value,
        is_active=True,
        is_locked=True,
        locked_until=None,
        password_hash="stored-hash",
        failed_login_attempts=0,
        last_failed_login=None,
    )
    service.repo = SimpleNamespace(
        find_by_login=AsyncMock(return_value=account),
        session=session,
    )
    monkeypatch.setattr(
        "app.identity.services.account_service.verify_password", Mock(return_value=False)
    )

    assert await service.authenticate("locked@example.test", "wrong-password") is None
    assert account.status == AccountStatus.locked.value
    assert account.is_locked is True
    assert account.failed_login_attempts == 0
    session.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_refresh_session_uses_refresh_token_identifier(monkeypatch):
    service = AuthenticationService(AsyncMock())
    service.session_repo = AsyncMock()
    service.account_repo = AsyncMock()
    service._create_session = AsyncMock(return_value={"access_token": "rotated"})
    session = SimpleNamespace(
        account_id="account-1",
        is_active=True,
        expires_at=datetime.now(UTC) + timedelta(days=1),
        ip_address="127.0.0.1",
        user_agent="test-agent",
        device_id="device-1",
        id="session-1",
    )
    account = SimpleNamespace(is_active=True)
    service.session_repo.find_by_refresh_token_jti.return_value = session
    service.account_repo.get_by_id.return_value = account
    blacklist = Mock()
    monkeypatch.setattr("app.security.auth.decode_refresh_token", lambda _token: {"jti": "refresh-jti"})
    monkeypatch.setattr("app.security.auth.blacklist_token", blacklist)

    result = await service.refresh_session("refresh-token")

    assert result == {"access_token": "rotated"}
    service.session_repo.find_by_refresh_token_jti.assert_awaited_once_with("refresh-jti")
    service.session_repo.find_by_token_jti.assert_not_called()
    service.session_repo.soft_delete.assert_awaited_once_with("session-1")
    blacklist.assert_called_once()
