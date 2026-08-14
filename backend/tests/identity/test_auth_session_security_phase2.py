"""Authentication and session hardening tests for IAM Phase 2."""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from app._compat import UTC
from app.identity.services import authentication_service as authentication_module
from app.security import auth as security_auth
from app.security.rate_limit import RateLimiter, _raise_429
from fastapi import HTTPException


class _AccountRepository:
    account = None

    def __init__(self, session):
        self.session = session

    async def get_by_id(self, account_id: str):
        if self.account and self.account.id == account_id:
            return self.account
        return None


class _AccountService:
    account = None

    def __init__(self, session):
        self.session = session

    async def authenticate(self, login: str, password: str):
        return self.account


class _SessionRepository:
    session_record = None

    def __init__(self, session):
        self.session = session
        self.created = []
        self.deleted = []

    async def create(self, session):
        self.created.append(session)
        self.session_record = session
        return session

    async def find_by_refresh_token_jti(self, refresh_jti: str):
        session = self.session_record
        if session and session.is_active and session.refresh_token_jti == refresh_jti:
            return session
        return None

    async def soft_delete(self, session_id: str):
        session = self.session_record
        if session and session.id == session_id:
            session.is_active = False
            self.deleted.append(session_id)

    async def get_by_uuid(self, session_uuid: str):
        return self.session_record if self.session_record and self.session_record.uuid == session_uuid else None

    async def terminate_session(self, session_id: str, reason: str, terminated_by: str):
        if self.session_record and self.session_record.id == session_id:
            self.session_record.is_active = False

    async def terminate_all_for_account(self, account_id: str, reason: str):
        if self.session_record and self.session_record.account_id == account_id:
            self.session_record.is_active = False


def _build_service(monkeypatch, *, active_account: bool = True):
    account = SimpleNamespace(
        id="account-1",
        uuid="account-uuid-1",
        identity_id="identity-1",
        is_active=active_account,
    )
    old_session = SimpleNamespace(
        id="session-1",
        uuid="session-uuid-1",
        account_id=account.id,
        refresh_token_jti="old-refresh-jti",
        is_active=True,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        ip_address="127.0.0.1",
        user_agent="test-agent",
        device_id="device-1",
    )
    _AccountRepository.account = account
    _AccountService.account = account
    _SessionRepository.session_record = old_session
    monkeypatch.setattr(authentication_module, "AccountRepository", _AccountRepository)
    monkeypatch.setattr(authentication_module, "AccountService", _AccountService)
    monkeypatch.setattr(authentication_module, "SessionRepository", _SessionRepository)

    blacklisted: list[tuple[str, int]] = []
    monkeypatch.setattr(
        security_auth,
        "decode_refresh_token",
        lambda token: {"jti": "old-refresh-jti"} if token == "old-token" else None,
    )
    monkeypatch.setattr(
        security_auth,
        "create_token",
        lambda payload: f"access:{payload['jti']}",
    )
    monkeypatch.setattr(
        security_auth,
        "create_refresh_token",
        lambda payload: f"refresh:{payload['jti']}",
    )
    monkeypatch.setattr(
        security_auth,
        "blacklist_token",
        lambda jti, seconds: blacklisted.append((jti, seconds)),
    )

    async def no_op_workspace_provisioning(self, account):
        return None

    monkeypatch.setattr(
        "app.identity.services.workspace_service.WorkspaceService.ensure_citizen_workspace",
        no_op_workspace_provisioning,
    )
    service = authentication_module.AuthenticationService(SimpleNamespace())
    return service, old_session, blacklisted


@pytest.mark.asyncio
async def test_refresh_rotates_jti_blacklists_old_token_and_deactivates_old_session(monkeypatch):
    service, old_session, blacklisted = _build_service(monkeypatch)

    result = await service.refresh_session("old-token")

    assert result is not None
    assert result["access_token"].startswith("access:")
    assert result["refresh_token"].startswith("refresh:")
    assert blacklisted and blacklisted[0][0] == "old-refresh-jti"
    assert old_session.is_active is False
    assert service.session_repo.deleted == ["session-1"]
    assert len(service.session_repo.created) == 1
    assert service.session_repo.created[0].refresh_token_jti != "old-refresh-jti"


@pytest.mark.asyncio
async def test_refresh_replay_is_rejected_after_rotation(monkeypatch):
    service, _, _ = _build_service(monkeypatch)

    assert await service.refresh_session("old-token") is not None
    assert await service.refresh_session("old-token") is None


@pytest.mark.asyncio
async def test_refresh_is_rejected_for_inactive_account_without_blacklisting(monkeypatch):
    service, old_session, blacklisted = _build_service(monkeypatch, active_account=False)

    assert await service.refresh_session("old-token") is None
    assert old_session.is_active is True
    assert blacklisted == []


def test_rate_limiter_rejects_after_window_budget_is_exhausted():
    key = f"phase2-rate-test-{uuid4()}"
    limiter = RateLimiter()

    assert limiter.check(key, max_requests=1, window_seconds=60) is True
    assert limiter.check(key, max_requests=1, window_seconds=60) is False


def test_rate_limit_429_contains_retry_and_budget_headers():
    with pytest.raises(HTTPException) as error:
        _raise_429("blocked", limit=3, reset_ts=int(datetime.now(UTC).timestamp()) + 30)

    assert error.value.status_code == 429
    assert error.value.headers["X-RateLimit-Limit"] == "3"
    assert error.value.headers["X-RateLimit-Remaining"] == "0"
    assert int(error.value.headers["Retry-After"]) >= 1
