from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest
from app._compat import UTC
from app.identity.services.account_service import AccountService
from app.identity.services.authentication_service import AuthenticationService
from app.security.auth import _DUMMY_HASH


def test_authenticate_verifies_dummy_hash_for_unknown_login(monkeypatch):
    service = AccountService(MagicMock())
    service.repo = MagicMock()
    service.repo.find_by_login.return_value = None
    verify = Mock(return_value=False)
    monkeypatch.setattr("app.identity.services.account_service.verify_password", verify)

    assert service.authenticate("unknown@example.test", "not-the-password") is None
    service.repo.find_by_login.assert_called_once_with("unknown@example.test")
    verify.assert_called_once_with("not-the-password", _DUMMY_HASH)


def test_refresh_session_uses_refresh_token_identifier(monkeypatch):
    service = AuthenticationService(MagicMock())
    service.session_repo = MagicMock()
    service.account_repo = MagicMock()
    service._create_session = MagicMock(return_value={"access_token": "rotated"})
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

    result = service.refresh_session("refresh-token")

    assert result == {"access_token": "rotated"}
    service.session_repo.find_by_refresh_token_jti.assert_called_once_with("refresh-jti")
    service.session_repo.find_by_token_jti.assert_not_called()
    service.session_repo.soft_delete.assert_called_once_with("session-1")
    blacklist.assert_called_once()
