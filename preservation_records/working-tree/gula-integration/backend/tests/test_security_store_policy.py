"""S-06 / S-07 security-hardening policy tests.

S-06 — shared security state (Redis) must never silently downgrade to
       process-local memory in production/staging. Degraded mode is only
       acceptable in non-production, or when the operator explicitly sets
       ``ALLOW_DEGRADED_REDIS=true``.

S-07 — auth cookies must carry ``Secure`` whenever the *effective* deployment
       is internet-facing: production, staging, demo mode, or any HTTPS base
       URL (e.g. a pilot environment that is not named ``production``).
"""
from __future__ import annotations

import importlib
import sys

import app.security.redis_client as rc
import pytest

# ── S-06: shared security state is fail-closed in production ────────────────


class _UnreachableRedis:
    """Stands in for ``redis.from_url`` when the server cannot be reached."""

    def __init__(self, _url: str) -> None:
        raise RuntimeError("connection refused")


class _SharedStore:
    is_shared = True


def test_store_shared_flags_are_explicit():
    assert rc._MemoryStore.is_shared is False
    assert rc._MemoryStore.is_degraded is True
    assert rc._RedisWrapper.is_shared is True
    assert rc._RedisWrapper.is_degraded is False


@pytest.mark.parametrize("redis_url", ["redis://unreachable:6379/0", ""])
def test_production_does_not_raise_at_import_without_redis(monkeypatch, redis_url):
    """The app must still boot so readiness probes can report the outage."""
    monkeypatch.setattr(rc, "IS_PRODUCTION", True)
    monkeypatch.setattr(rc, "REDIS_URL", redis_url)
    monkeypatch.delenv("ALLOW_DEGRADED_REDIS", raising=False)
    monkeypatch.setattr(rc, "_RedisWrapper", _UnreachableRedis)

    store = rc._build_cache()
    assert isinstance(store, rc._MemoryStore)


@pytest.mark.parametrize("operation", ["Token revocation", "Rate limiting", "Order idempotency"])
def test_production_security_operations_fail_closed_without_redis(monkeypatch, operation):
    monkeypatch.setattr(rc, "IS_PRODUCTION", True)
    monkeypatch.delenv("ALLOW_DEGRADED_REDIS", raising=False)
    monkeypatch.setattr(rc, "cache", rc._MemoryStore())

    with pytest.raises(rc.SecurityStoreUnavailable, match=operation):
        rc.security_store(operation)


def test_production_allows_explicitly_acknowledged_degraded_mode(monkeypatch):
    monkeypatch.setattr(rc, "IS_PRODUCTION", True)
    monkeypatch.setenv("ALLOW_DEGRADED_REDIS", "true")
    monkeypatch.setattr(rc, "cache", rc._MemoryStore())

    assert rc.security_store("Token revocation") is rc.cache


def test_development_allows_memory_fallback(monkeypatch):
    monkeypatch.setattr(rc, "IS_PRODUCTION", False)
    monkeypatch.delenv("ALLOW_DEGRADED_REDIS", raising=False)
    monkeypatch.setattr(rc, "cache", rc._MemoryStore())

    assert rc.security_store("Token revocation") is rc.cache


def test_shared_store_is_always_accepted(monkeypatch):
    shared = _SharedStore()
    monkeypatch.setattr(rc, "IS_PRODUCTION", True)
    monkeypatch.delenv("ALLOW_DEGRADED_REDIS", raising=False)
    monkeypatch.setattr(rc, "cache", shared)

    assert rc.security_store("Token revocation") is shared


def test_shared_state_probe_reports_degraded_store(monkeypatch):
    monkeypatch.setattr(rc, "cache", rc._MemoryStore())
    assert rc.is_shared_security_state() is False


def test_token_revocation_check_fails_closed_in_production(monkeypatch):
    from app.security import auth

    monkeypatch.setattr(rc, "IS_PRODUCTION", True)
    monkeypatch.delenv("ALLOW_DEGRADED_REDIS", raising=False)
    monkeypatch.setattr(rc, "cache", rc._MemoryStore())

    with pytest.raises(rc.SecurityStoreUnavailable):
        auth.is_token_blacklisted("jti-1")


def test_rate_limiter_fails_closed_with_503_in_production(monkeypatch):
    from app.security import rate_limit
    from fastapi import HTTPException

    monkeypatch.setattr(rc, "IS_PRODUCTION", True)
    monkeypatch.delenv("ALLOW_DEGRADED_REDIS", raising=False)
    monkeypatch.setattr(rc, "cache", rc._MemoryStore())

    with pytest.raises(HTTPException) as excinfo:
        rate_limit._check("user:1", 10, 60)
    assert excinfo.value.status_code == 503


# ── S-07: cookie security follows the effective deployment configuration ────

_BASE_ENV = {
    "RUNTIME_MODE": "api",
    "FEATURE_BACKGROUND_TASKS": "false",
    "REDIS_URL": "redis://cache.example:6379/0",
    # Deterministic low-entropy placeholders: config validates length/policy,
    # and no reusable credential material is committed to the repository.
    "SECRET_KEY": "x" * 64,
    "REFRESH_TOKEN_SECRET": "y" * 64,
    "ENCRYPTION_KEY": "z" * 64,
    "NID_HMAC_KEY": "w" * 64,
    "AUDIT_ANCHOR_KEY": "v" * 64,
}


def _load_config(monkeypatch: pytest.MonkeyPatch, **overrides: str):
    """Import config under a temporary, fully isolated environment."""
    environment = {**_BASE_ENV, **overrides}
    with monkeypatch.context() as scoped_env:
        for name, value in environment.items():
            scoped_env.setenv(name, value)
        for name in ("DEMO_MODE", "DEMO_DATA_ISOLATION_ACK", "CORS_ORIGINS", "TRUSTED_HOSTS"):
            if name not in overrides:
                scoped_env.delenv(name, raising=False)
        scoped_env.delenv("ALLOW_DEGRADED_REDIS", raising=False)
        sys.modules.pop("app.config", None)
        try:
            return importlib.import_module("app.config")
        finally:
            sys.modules.pop("app.config", None)


def test_https_pilot_environment_gets_secure_cookies(monkeypatch: pytest.MonkeyPatch):
    config = _load_config(monkeypatch, ENV="pilot", BASE_URL="https://pilot.gula.example")

    # A pilot is not named "production"/"staging", yet it is internet-facing.
    assert config.IS_PRODUCTION is False
    assert config.USE_SECURE_COOKIES is True
    assert config.cookie_security_options()["secure"] is True


def test_development_over_plain_http_keeps_local_cookies(monkeypatch: pytest.MonkeyPatch):
    config = _load_config(monkeypatch, ENV="development", BASE_URL="http://localhost:8000")

    assert config.USE_SECURE_COOKIES is False
    assert config.cookie_security_options() == {
        "httponly": True,
        "samesite": "strict",
        "secure": False,
    }


def test_demo_mode_gets_secure_cookies(monkeypatch: pytest.MonkeyPatch):
    config = _load_config(
        monkeypatch,
        ENV="demo",
        BASE_URL="http://demo.local:8000",
        DEMO_MODE="true",
        DEMO_DATA_ISOLATION_ACK="true",
    )

    assert config.USE_SECURE_COOKIES is True
    assert config.cookie_security_options()["httponly"] is True
