"""Command 05 shared Redis and fail-closed tests."""

from __future__ import annotations

import os

import pytest
from app.security import redis_client
from app.security.auth import blacklist_token
from app.security.rate_limit import RateLimiter
from fastapi import HTTPException


def test_shared_cache_requirement_rejects_unavailable_backend(monkeypatch):
    monkeypatch.setattr(redis_client, "_SHARED_CACHE_REQUIRED", True)
    monkeypatch.setattr(redis_client, "cache", redis_client._UnavailableStore())

    with pytest.raises(redis_client.CacheUnavailable):
        redis_client.ensure_shared_cache()
    with pytest.raises(redis_client.CacheUnavailable):
        blacklist_token("jti-1", 60)


def test_development_memory_store_remains_explicitly_allowed(monkeypatch):
    store = redis_client._MemoryStore()
    monkeypatch.setattr(redis_client, "_SHARED_CACHE_REQUIRED", False)
    monkeypatch.setattr(redis_client, "cache", store)

    redis_client.ensure_shared_cache()
    store.set("key", "value", ex=60)
    assert store.get("key") == "value"


def test_rate_limiter_returns_503_when_shared_cache_is_required(monkeypatch):
    monkeypatch.setattr(redis_client, "_SHARED_CACHE_REQUIRED", True)
    monkeypatch.setattr(redis_client, "cache", redis_client._UnavailableStore())

    with pytest.raises(HTTPException) as exc_info:
        RateLimiter().check("auth:ip", max_requests=5, window_seconds=60)
    assert exc_info.value.status_code == 503
    assert exc_info.value.headers["Retry-After"] == "5"


@pytest.mark.integration
def test_two_redis_wrappers_share_revocation_key():
    url = os.getenv("COMMAND05_REDIS_URL", "redis://127.0.0.1:6380/0")
    first = redis_client._RedisWrapper(url)
    second = redis_client._RedisWrapper(url)
    key = "gula:command05:test:shared-jti"
    try:
        first.set(key, "1", ex=30)
        assert second.get(key) == "1"
        second.delete(key)
        assert first.get(key) is None
    finally:
        first.delete(key)


def test_startup_readiness_is_red_when_strict_redis_is_unavailable(monkeypatch):
    from app.core import startup_guard

    monkeypatch.setattr(startup_guard, "system_ready", True)
    monkeypatch.setattr(redis_client, "_SHARED_CACHE_REQUIRED", True)
    monkeypatch.setattr(redis_client, "cache", redis_client._UnavailableStore())
    monkeypatch.setattr("app.database.check_db_connection", lambda: True)

    ready, reason = startup_guard.is_system_ready()
    assert ready is False
    assert reason == "redis_unavailable"
