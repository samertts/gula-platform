"""HTTP-boundary hardening tests for IAM Phase 5 workspace routes."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from app.identity.api import workspaces as workspace_api
from app.identity.services.workspace_service import WorkspaceAccessDenied
from fastapi import HTTPException


class _Result:
    def __init__(self, row: Any = None) -> None:
        self.row = row

    def first(self) -> Any:
        return self.row


class _Db:
    def __init__(self, row: Any = None, workspace: Any = None) -> None:
        self.row = row
        self.workspace = workspace
        self.statement = None

    async def execute(self, statement: Any) -> _Result:
        self.statement = statement
        return _Result(self.row)

    async def get(self, model: Any, workspace_id: Any) -> Any:
        return self.workspace


class _Credentials:
    def __init__(self, token: str) -> None:
        self.credentials = token


class _Audit:
    records: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    denied: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def __init__(self, db: Any) -> None:
        self.db = db

    async def record(self, *args: Any, **kwargs: Any) -> None:
        self.records.append((args, kwargs))

    async def record_event(self, *args: Any, **kwargs: Any) -> None:
        self.denied.append((args, kwargs))


class _WorkspaceService:
    context: Any = None
    error: Exception | None = None

    def __init__(self, db: Any) -> None:
        self.db = db

    async def switch(self, account: Any, session_id: str, workspace_id: str) -> Any:
        if self.error:
            raise self.error
        return self.context


def request() -> SimpleNamespace:
    return SimpleNamespace(cookies={})


def actor() -> workspace_api.NiamActor:
    account = SimpleNamespace(id="account-1", uuid="account-uuid-1", identity_id="identity-1")
    session = SimpleNamespace(id="session-1", uuid="session-uuid-1")
    return workspace_api.NiamActor(account=account, session=session)


def workspace() -> SimpleNamespace:
    return SimpleNamespace(
        id="workspace-1",
        uuid="workspace-uuid-1",
        workspace_type="citizen",
        name="Citizen Workspace",
        name_ar="مساحة المواطن",
        status="active",
        organization_id=None,
        facility_id=None,
        department_id=None,
        professional_type=None,
        is_personal=True,
    )


def test_missing_niam_credentials_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    credentials = None
    with pytest.raises(HTTPException) as error:
        import asyncio

        asyncio.run(workspace_api.get_current_niam_actor(request(), credentials, _Db()))

    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_invalid_or_inactive_niam_token_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(workspace_api, "decode_token", lambda token: {"jti": "jti-1"})

    with pytest.raises(HTTPException) as error:
        await workspace_api.get_current_niam_actor(
            request(),
            _Credentials("invalid-token"),
            _Db(row=None),
        )

    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_valid_token_requires_matching_active_account_and_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        workspace_api,
        "decode_token",
        lambda token: {"jti": "jti-1", "account_uuid": "account-uuid-1"},
    )
    account = SimpleNamespace(id="account-1")
    session = SimpleNamespace(id="session-1")

    db = _Db(row=(account, session))
    result = await workspace_api.get_current_niam_actor(
        request(),
        _Credentials("valid-token"),
        db,
    )

    assert result.account is account
    assert "is_locked" in str(db.statement)
    assert result.session is session


@pytest.mark.asyncio
async def test_switch_route_returns_server_context_and_audits_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _Audit.records = []
    _WorkspaceService.context = SimpleNamespace(
        account_id="account-1",
        identity_id="identity-1",
        workspace_id="workspace-1",
        version=2,
    )
    _WorkspaceService.error = None
    monkeypatch.setattr(workspace_api, "WorkspaceService", _WorkspaceService)
    monkeypatch.setattr(workspace_api, "AuditService", _Audit)

    result = await workspace_api.switch_workspace(
        "workspace-1",
        actor=actor(),
        db=_Db(workspace=workspace()),
    )

    assert result["context"]["workspace_id"] == "workspace-1"
    assert result["context"]["version"] == 2
    assert result["workspace"]["status"] == "active"
    assert len(_Audit.records) == 1


@pytest.mark.asyncio
async def test_switch_route_returns_403_and_audits_denial(monkeypatch: pytest.MonkeyPatch) -> None:
    _Audit.denied = []
    _WorkspaceService.error = WorkspaceAccessDenied("not eligible")
    monkeypatch.setattr(workspace_api, "WorkspaceService", _WorkspaceService)
    monkeypatch.setattr(workspace_api, "AuditService", _Audit)

    with pytest.raises(HTTPException) as error:
        await workspace_api.switch_workspace("foreign-workspace", actor=actor(), db=_Db())

    assert error.value.status_code == 403
    assert len(_Audit.denied) == 1
    assert _Audit.denied[0][1]["outcome"] == "denied"


def test_niam_session_idle_timeout_is_server_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    from datetime import datetime, timedelta

    from app._compat import UTC

    session = SimpleNamespace(last_activity_at=datetime.now(UTC) - timedelta(hours=2))
    assert workspace_api._session_is_idle(session, datetime.now(UTC)) is True


def test_niam_session_touch_skips_recent_activity(monkeypatch: pytest.MonkeyPatch) -> None:
    from datetime import datetime

    from app._compat import UTC

    class _SyncDb:
        def __init__(self) -> None:
            self.commits = 0

        def commit(self) -> None:
            self.commits += 1

    now = datetime.now(UTC)
    session = SimpleNamespace(last_activity_at=now)
    db = _SyncDb()
    workspace_api._touch_session_sync(db, session, now)
    assert db.commits == 0
