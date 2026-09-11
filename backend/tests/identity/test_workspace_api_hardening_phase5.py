"""HTTP-boundary hardening tests for IAM Phase 5 workspace routes."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.identity.api import workspaces as workspace_api
from app.identity.services.workspace_service import WorkspaceAccessDenied
from fastapi import HTTPException


class _Result:
    def __init__(self, row=None):
        self.row = row

    def first(self):
        return self.row


class _Query:
    """The tail of the synchronous chain the actor dependency builds.

    It records nothing about the predicates: a fake cannot prove that
    `Account.is_locked` is filtered, which is exactly how the async
    dependency kept a missing lock check out of sight. The predicates are
    proved against real PostgreSQL in tests/test_identity_link_and_assurance.py
    (`test_a_locked_account_is_refused`). What this file proves is the HTTP
    boundary: which status code comes back for which shape of input.
    """

    def __init__(self, row):
        self.row = row

    def join(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.row


class _Db:
    def __init__(self, row=None, workspace=None):
        self.row = row
        self.workspace = workspace

    def query(self, *entities):
        return _Query(self.row)

    async def execute(self, statement):
        return _Result(self.row)

    async def get(self, model, workspace_id):
        return self.workspace


class _Credentials:
    def __init__(self, token):
        self.credentials = token


class _Audit:
    records = []
    denied = []

    def __init__(self, db):
        self.db = db

    async def record(self, *args, **kwargs):
        self.records.append((args, kwargs))

    async def record_event(self, *args, **kwargs):
        self.denied.append((args, kwargs))


class _WorkspaceService:
    context = None
    error = None

    def __init__(self, db):
        self.db = db

    async def switch(self, account, session_id, workspace_id):
        if self.error:
            raise self.error
        return self.context


def request():
    return SimpleNamespace(cookies={})


def actor():
    account = SimpleNamespace(id="account-1", uuid="account-uuid-1", identity_id="identity-1")
    session = SimpleNamespace(id="session-1", uuid="session-uuid-1")
    return workspace_api.NiamActor(account=account, session=session)


def workspace():
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


def test_missing_niam_credentials_are_rejected(monkeypatch):
    credentials = None
    with pytest.raises(HTTPException) as error:
        workspace_api.get_current_niam_actor(request(), credentials, _Db())

    assert error.value.status_code == 401


def test_invalid_or_inactive_niam_token_is_rejected(monkeypatch):
    monkeypatch.setattr(workspace_api, "decode_token", lambda token: {"jti": "jti-1"})

    with pytest.raises(HTTPException) as error:
        workspace_api.get_current_niam_actor(
            request(),
            _Credentials("invalid-token"),
            _Db(row=None),
        )

    assert error.value.status_code == 401


def test_valid_token_requires_matching_active_account_and_session(monkeypatch):
    monkeypatch.setattr(
        workspace_api,
        "decode_token",
        lambda token: {"jti": "jti-1", "account_uuid": "account-uuid-1"},
    )
    account = SimpleNamespace(id="account-1")
    session = SimpleNamespace(id="session-1")

    result = workspace_api.get_current_niam_actor(
        request(),
        _Credentials("valid-token"),
        _Db(row=(account, session)),
    )

    assert result.account is account
    assert result.session is session


@pytest.mark.asyncio
async def test_switch_route_returns_server_context_and_audits_success(monkeypatch):
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
async def test_switch_route_returns_403_and_audits_denial(monkeypatch):
    _Audit.denied = []
    _WorkspaceService.error = WorkspaceAccessDenied("not eligible")
    monkeypatch.setattr(workspace_api, "WorkspaceService", _WorkspaceService)
    monkeypatch.setattr(workspace_api, "AuditService", _Audit)

    with pytest.raises(HTTPException) as error:
        await workspace_api.switch_workspace("foreign-workspace", actor=actor(), db=_Db())

    assert error.value.status_code == 403
    assert len(_Audit.denied) == 1
    assert _Audit.denied[0][1]["outcome"] == "denied"
