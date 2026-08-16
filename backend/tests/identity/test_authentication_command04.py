"""Command 04 authentication/session hardening tests."""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app._compat import UTC
from app.identity.api.auth import router as niam_auth_router
from app.identity.repositories.session_repository import SessionRepository
from app.identity.services.authentication_service import AuthenticationService
from app.security import auth as security_auth


@pytest.mark.asyncio
async def test_active_refresh_lookup_requests_row_lock():
    class _Result:
        def scalar_one_or_none(self):
            return None

    class _Session:
        def __init__(self):
            self.statements = []

        async def execute(self, statement):
            self.statements.append(statement)
            return _Result()

    db = _Session()
    await SessionRepository(db).find_by_refresh_token_jti("refresh-jti")
    assert db.statements[0]._for_update_arg is not None


def test_niam_auth_contract_exposes_server_authoritative_session_routes():
    paths = {route.path for route in niam_auth_router.routes}
    assert "/auth/login" in paths
    assert "/auth/refresh" in paths
    assert "/auth/logout" in paths
    assert "/auth/logout-all" in paths


class _ReplayRepository:
    def __init__(self, session):
        self.session = session
        self.rotated = SimpleNamespace(
            id="old-session",
            uuid="old-session-uuid",
            account_id="account-1",
            token_jti="old-access",
            refresh_token_jti="replayed-refresh",
            refresh_family_id="family-1",
            termination_reason="refresh_rotation",
            is_active=False,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        self.invalidated_family: tuple[str, str] | None = None

    async def find_by_refresh_token_jti(self, jti: str, *, active_only: bool = True):
        if not active_only and jti == self.rotated.refresh_token_jti:
            return self.rotated
        return None

    async def terminate_all_for_refresh_family(self, family_id: str, reason: str):
        self.invalidated_family = (family_id, reason)


@pytest.mark.asyncio
async def test_replayed_rotated_refresh_invalidates_the_whole_family(monkeypatch):
    service = AuthenticationService(AsyncMock())
    repo = _ReplayRepository(service.session)
    service.session_repo = repo
    blacklisted: list[tuple[str, int]] = []
    monkeypatch.setattr(
        security_auth,
        "decode_refresh_token",
        lambda token: {"jti": "replayed-refresh"} if token == "replayed-token" else None,
    )
    monkeypatch.setattr(
        security_auth,
        "blacklist_token",
        lambda jti, seconds: blacklisted.append((jti, seconds)),
    )

    assert await service.refresh_session("replayed-token") is None
    assert repo.invalidated_family == ("family-1", "refresh_reuse_detected")
    assert blacklisted and blacklisted[0][0] == "replayed-refresh"


def test_access_and_refresh_jti_are_preserved_for_canonical_session_binding(monkeypatch):
    captured: list[dict] = []

    def capture_access(data, **_kwargs):
        captured.append(data)
        return "access-token"

    def capture_refresh(data, **_kwargs):
        captured.append(data)
        return "refresh-token"

    monkeypatch.setattr(security_auth, "_shared_create_access_token", capture_access)
    monkeypatch.setattr(security_auth, "_shared_create_refresh_token", capture_refresh)

    security_auth.create_token({"jti": "access-jti", "account_uuid": "account-1"})
    security_auth.create_refresh_token({"jti": "refresh-jti", "account_uuid": "account-1"})

    assert captured[0]["jti"] == "access-jti"
    assert captured[0]["type"] == "access"
    assert captured[1]["jti"] == "refresh-jti"
    assert captured[1]["type"] == "refresh"


@pytest.mark.asyncio
async def test_logout_blacklists_both_token_classes_and_terminates_owned_session(monkeypatch):
    service = AuthenticationService(AsyncMock())
    session = SimpleNamespace(
        id="session-1",
        uuid="session-uuid",
        account_id="account-1",
        token_jti="access-jti",
        refresh_token_jti="refresh-jti",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        is_active=True,
    )
    service.session_repo = AsyncMock()
    service.session_repo.get_by_uuid.return_value = session
    blacklisted: list[str] = []
    monkeypatch.setattr(
        security_auth,
        "blacklist_token",
        lambda jti, _seconds: blacklisted.append(jti),
    )

    assert await service.logout("session-uuid", account_id="account-1") is True
    assert blacklisted == ["access-jti", "refresh-jti"]
    service.session_repo.terminate_session.assert_awaited_once_with(
        session_id="session-1",
        reason="user_logout",
        terminated_by="account-1",
    )


@pytest.mark.asyncio
async def test_logout_rejects_cross_account_session_without_revocation(monkeypatch):
    service = AuthenticationService(AsyncMock())
    session = SimpleNamespace(
        id="session-1",
        uuid="session-uuid",
        account_id="other-account",
        token_jti="access-jti",
        refresh_token_jti="refresh-jti",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        is_active=True,
    )
    service.session_repo = AsyncMock()
    service.session_repo.get_by_uuid.return_value = session
    blacklist = AsyncMock()
    monkeypatch.setattr(security_auth, "blacklist_token", blacklist)

    assert await service.logout("session-uuid", account_id="account-1") is False
    service.session_repo.terminate_session.assert_not_awaited()
    blacklist.assert_not_awaited()
