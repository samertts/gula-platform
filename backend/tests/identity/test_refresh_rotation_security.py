from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

from app.security import auth as security_auth
from app.security.redis_client import _MemoryStore


def test_refresh_jti_consume_is_atomic_under_concurrency(monkeypatch):
    store = _MemoryStore()
    monkeypatch.setattr("app.security.redis_client.cache", store)

    def consume() -> bool:
        return security_auth.consume_refresh_jti("same-refresh-jti", 60)

    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(lambda _: consume(), range(64)))

    assert sum(results) == 1


def test_refresh_jti_marker_expires_for_new_rotation_window(monkeypatch):
    store = _MemoryStore()
    monkeypatch.setattr("app.security.redis_client.cache", store)

    assert security_auth.consume_refresh_jti("expiring-jti", 1) is True
    assert security_auth.consume_refresh_jti("expiring-jti", 1) is False


def test_refresh_replay_revokes_token_family_and_audits_without_secret(monkeypatch):
    from app.routes import mobile

    calls = {}

    def fake_bump(user, db, **kwargs):
        calls["bump"] = (user, db, kwargs)

    def fake_audit(db, **kwargs):
        calls["audit"] = kwargs

    class _DB:
        def commit(self):
            calls["commit"] = True

    user = SimpleNamespace(id=17, role="staff")
    request = SimpleNamespace(
        client=SimpleNamespace(host="127.0.0.1"),
        headers={},
    )
    monkeypatch.setattr(mobile, "bump_perm_version", fake_bump)
    monkeypatch.setattr(mobile, "log_action", fake_audit)
    monkeypatch.setattr(mobile, "get_client_ip", lambda req: "127.0.0.1")

    mobile._revoke_after_refresh_replay(_DB(), user, request)

    assert calls["bump"][2]["reason"] == "refresh_replay"
    assert calls["audit"]["action"] == "refresh_replay_detected"
    assert "same-refresh-jti" not in calls["audit"]["details"]
    assert "access_token" not in calls["audit"]["details"]
    assert "refresh_token" not in calls["audit"]["details"]
    assert calls["commit"] is True


def test_refresh_requires_shared_backend_in_production(monkeypatch):
    from app.routes import mobile
    from fastapi import HTTPException

    class _UnsharedCache:
        is_shared = False

    monkeypatch.setattr(mobile, "IS_PRODUCTION", True)
    monkeypatch.setattr(mobile, "cache", _UnsharedCache())

    try:
        mobile._require_shared_refresh_backend()
    except HTTPException as exc:
        assert exc.status_code == 503
    else:
        raise AssertionError("production refresh must fail closed without shared cache")
