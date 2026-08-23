from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.identity.api import auth, devices, ownership, persons, sessions, workspaces
from app.identity.services import device_service
from fastapi import HTTPException
from fastapi.routing import APIRoute


class _Result:
    def __init__(self, row=None, scalar=None):
        self.row = row
        self.scalar = scalar

    def first(self):
        return self.row

    def scalar_one_or_none(self):
        return self.scalar


class _Db:
    def __init__(self, row=None, scalar=None):
        self.row = row
        self.scalar = scalar
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return _Result(row=self.row, scalar=self.scalar)

    async def scalar(self, statement):
        self.statements.append(statement)
        return self.scalar


def _actor(account_id: str = "account-1"):
    account = SimpleNamespace(
        id=account_id,
        uuid=f"{account_id}-uuid",
        identity_id="identity-1",
    )
    session = SimpleNamespace(id="session-1", uuid="session-uuid-1")
    return workspaces.NiamActor(account=account, session=session)


class _Audit:
    records: list[tuple[tuple, dict]] = []

    def __init__(self, db):
        self.db = db

    async def record_event(self, *args, **kwargs):
        self.records.append((args, kwargs))

    async def record(self, *args, **kwargs):
        self.records.append((args, kwargs))


@pytest.mark.asyncio
async def test_async_niam_actor_query_rejects_locked_account(monkeypatch):
    monkeypatch.setattr(
        workspaces,
        "decode_token",
        lambda token: {"jti": "jti-1", "account_uuid": "account-uuid-1"},
    )
    db = _Db(row=None)

    with pytest.raises(HTTPException) as error:
        await workspaces.get_current_niam_actor(
            SimpleNamespace(cookies={}),
            SimpleNamespace(credentials="token"),
            db,
        )

    assert error.value.status_code == 401
    assert "is_locked" in str(db.statements[0])


@pytest.mark.asyncio
async def test_foreign_account_scope_is_denied_and_audited(monkeypatch):
    _Audit.records = []
    monkeypatch.setattr(ownership, "AuditService", _Audit)

    with pytest.raises(HTTPException) as error:
        await ownership.require_account_scope(_Db(), _actor(), "foreign-account")

    assert error.value.status_code == 403
    assert _Audit.records[-1][1]["target_type"] == "account"
    assert _Audit.records[-1][1]["outcome"] == "denied"


@pytest.mark.asyncio
async def test_session_termination_rejects_foreign_session(monkeypatch):
    actor = _actor()
    foreign_session = SimpleNamespace(
        id="session-2",
        uuid="foreign-session",
        account_id="account-2",
    )

    class _Service:
        def __init__(self, db):
            self.repo = SimpleNamespace(get_by_uuid=AsyncMock(return_value=foreign_session))

    denial = AsyncMock()
    monkeypatch.setattr(sessions, "SessionService", _Service)
    monkeypatch.setattr(sessions, "record_authorization_denial", denial)

    with pytest.raises(HTTPException) as error:
        await sessions.terminate_session(
            "foreign-session",
            reason="manual",
            actor=actor,
            db=_Db(),
        )

    assert error.value.status_code == 403
    denial.assert_awaited_once()


@pytest.mark.asyncio
async def test_session_termination_uses_actor_identity(monkeypatch):
    owned_session = SimpleNamespace(
        id="session-1",
        uuid="owned-session",
        account_id="account-1",
    )
    service = None

    class _Service:
        def __init__(self, db):
            nonlocal service
            service = self
            self.repo = SimpleNamespace(get_by_uuid=AsyncMock(return_value=owned_session))
            self.terminate = AsyncMock()

    _Audit.records = []
    monkeypatch.setattr(sessions, "SessionService", _Service)
    monkeypatch.setattr(sessions, "AuditService", _Audit)

    result = await sessions.terminate_session(
        "owned-session",
        reason="manual",
        actor=_actor(),
        db=_Db(),
    )

    assert result == {"success": True}
    service.terminate.assert_awaited_once_with(
        "session-1",
        "manual",
        terminated_by="account-1",
    )
    assert _Audit.records[-1][1]["actor_id"] == "account-1"


@pytest.mark.asyncio
async def test_logout_rejects_foreign_session_and_audits(monkeypatch):
    foreign_session = SimpleNamespace(
        id="session-2",
        uuid="foreign-session",
        account_id="account-2",
    )

    class _Service:
        def __init__(self, db):
            self.session_repo = SimpleNamespace(
                get_by_uuid=AsyncMock(return_value=foreign_session)
            )
            self.logout = AsyncMock()

    denial = AsyncMock()
    monkeypatch.setattr(auth, "AuthenticationService", _Service)
    monkeypatch.setattr(auth, "record_authorization_denial", denial)

    with pytest.raises(HTTPException) as error:
        await auth.logout("foreign-session", actor=_actor(), db=_Db())

    assert error.value.status_code == 403
    denial.assert_awaited_once()
    assert denial.await_args.kwargs["target_type"] == "session"
    assert denial.await_args.kwargs["reason"] == "logout_session_scope_mismatch"


@pytest.mark.asyncio
async def test_logout_uses_actor_and_records_owned_session_audit(monkeypatch):
    owned_session = SimpleNamespace(
        id="session-1",
        uuid="owned-session",
        account_id="account-1",
    )
    service = None

    class _Service:
        def __init__(self, db):
            nonlocal service
            service = self
            self.session_repo = SimpleNamespace(
                get_by_uuid=AsyncMock(return_value=owned_session)
            )
            self.logout = AsyncMock(return_value=True)

    _Audit.records = []
    monkeypatch.setattr(auth, "AuthenticationService", _Service)
    monkeypatch.setattr(auth, "AuditService", _Audit)

    result = await auth.logout("owned-session", actor=_actor(), db=_Db())

    assert result == {"success": True}
    service.logout.assert_awaited_once_with(
        "owned-session",
        actor_account_id="account-1",
    )
    assert _Audit.records[-1][1]["actor_id"] == "account-1"
    assert _Audit.records[-1][1]["target_id"] == "owned-session"


@pytest.mark.asyncio
async def test_device_fingerprint_cannot_be_rebound(monkeypatch):
    existing = SimpleNamespace(person_id="other-person", account_id="other-account")

    class _Repo:
        def __init__(self, session):
            self.session = session

        async def find_by_fingerprint(self, fingerprint):
            return existing

    monkeypatch.setattr(device_service, "DeviceRepository", _Repo)
    service = device_service.DeviceService(_Db())

    with pytest.raises(device_service.DeviceRegistrationConflict):
        await service.register_device(
            person_id="person-1",
            account_id="account-1",
            device_fingerprint="fingerprint-1",
        )


def _routes(router):
    return [route for route in router.routes if isinstance(route, APIRoute)]


@pytest.mark.parametrize(
    ("router", "path"),
    [
        (sessions.router, "/account/{account_id}"),
        (sessions.router, "/{session_uuid}/terminate"),
        (sessions.router, "/account/{account_id}/terminate-all"),
        (devices.router, "/register"),
        (devices.router, "/{device_uuid}/trust"),
        (devices.router, "/{device_uuid}/revoke"),
        (persons.router, "/"),
        (persons.router, "/{person_uuid}"),
        (auth.router, "/logout"),
    ],
)
def test_sensitive_niam_routes_require_current_actor(router, path):
    route = next(route for route in _routes(router) if route.path.endswith(path))
    dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
    assert workspaces.get_current_niam_actor in dependency_calls
