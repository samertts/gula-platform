from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.identity.api import auth as auth_api


@pytest.mark.asyncio
async def test_niam_login_uses_request_metadata_not_query_values(monkeypatch):
    captured: dict[str, object] = {}

    class _AuthenticationService:
        def __init__(self, _db):
            pass

        async def login(self, **kwargs):
            captured.update(kwargs)
            return {"session_uuid": "session-1"}

    monkeypatch.setattr(auth_api, "AuthenticationService", _AuthenticationService)
    monkeypatch.setattr(auth_api, "rate_limit_auth", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(auth_api, "get_client_ip", lambda _request: "192.0.2.10")
    request = SimpleNamespace(headers={"user-agent": "trusted-client/1.0"})

    class _Db:
        def __init__(self):
            self.commits = 0

        def commit(self):
            self.commits += 1

    db = _Db()
    result = await auth_api.login(
        auth_api.LoginRequest(login="person@example.test", password="not-a-real-password"),
        request,
        ip_address="198.51.100.99",
        user_agent="spoofed-client/9.9",
        db=db,
    )

    assert result == {"session_uuid": "session-1"}
    assert db.commits == 1
    assert captured["ip_address"] == "192.0.2.10"
    assert captured["user_agent"] == "trusted-client/1.0"


@pytest.mark.asyncio
async def test_niam_logout_is_account_scoped(monkeypatch):
    captured: dict[str, object] = {}

    class _AuthenticationService:
        def __init__(self, _db):
            pass

        async def logout(self, session_uuid, account_id=None):
            captured.update({"session_uuid": session_uuid, "account_id": account_id})
            return account_id == "account-1" and session_uuid == "session-1"

    monkeypatch.setattr(auth_api, "AuthenticationService", _AuthenticationService)
    actor = SimpleNamespace(account=SimpleNamespace(id="account-1"))

    class _Db:
        def __init__(self):
            self.commits = 0

        def commit(self):
            self.commits += 1

    db = _Db()
    assert await auth_api.logout("session-1", actor=actor, db=db) == {"success": True}
    assert db.commits == 1
    assert captured == {"session_uuid": "session-1", "account_id": "account-1"}

    with pytest.raises(auth_api.HTTPException) as error:
        await auth_api.logout("foreign-session", actor=actor, db=db)
    assert error.value.status_code == 403
