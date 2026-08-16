from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.identity.api import sessions as sessions_api


class _Repo:
    def __init__(self, session_record):
        self.session_record = session_record

    async def get_by_uuid(self, session_uuid):
        if self.session_record.uuid == session_uuid:
            return self.session_record
        return None


class _Service:
    def __init__(self, db):
        self.repo = _Repo(
            SimpleNamespace(uuid="foreign-session", id="session-2", account_id="account-2")
        )
        self.terminated = []

    async def get_active_sessions(self, account_id):
        return []

    async def terminate(self, session_id, reason):
        self.terminated.append((session_id, reason))

    async def terminate_all(self, account_id, reason):
        self.terminated.append((account_id, reason))


@pytest.mark.asyncio
async def test_list_sessions_rejects_client_account_scope_mismatch():
    actor = SimpleNamespace(account=SimpleNamespace(id="account-1"))

    with pytest.raises(HTTPException) as error:
        await sessions_api.list_sessions("account-2", actor=actor, db=None)

    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_terminate_session_rejects_foreign_session_before_mutation(monkeypatch):
    service = _Service(None)
    monkeypatch.setattr(sessions_api, "SessionService", lambda db: service)
    actor = SimpleNamespace(account=SimpleNamespace(id="account-1"))

    with pytest.raises(HTTPException) as error:
        await sessions_api.terminate_session(
            "foreign-session", actor=actor, reason="security_recovery", db=None
        )

    assert error.value.status_code == 403
    assert service.terminated == []


@pytest.mark.asyncio
async def test_terminate_all_rejects_foreign_account_before_mutation():
    actor = SimpleNamespace(account=SimpleNamespace(id="account-1"))

    with pytest.raises(HTTPException) as error:
        await sessions_api.terminate_all_sessions("account-2", actor=actor, db=None)

    assert error.value.status_code == 403
