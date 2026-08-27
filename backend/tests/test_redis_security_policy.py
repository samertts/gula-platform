from __future__ import annotations

import pytest
from app.security import redis_client


def _raise_connection_error(_url: str):
    raise ConnectionError("synthetic redis outage")


def test_production_redis_outage_fails_closed(monkeypatch):
    monkeypatch.setattr(redis_client, "REDIS_URL", "redis://synthetic.invalid/0")
    monkeypatch.setattr(redis_client, "IS_PRODUCTION", True)
    monkeypatch.setattr(redis_client, "ALLOW_DEGRADED_REDIS", False)
    monkeypatch.setattr(redis_client, "_RedisWrapper", _raise_connection_error)

    with pytest.raises(RuntimeError, match="Redis is required in production"):
        redis_client._build_cache()


def test_production_missing_redis_url_fails_closed(monkeypatch):
    monkeypatch.setattr(redis_client, "REDIS_URL", "")
    monkeypatch.setattr(redis_client, "IS_PRODUCTION", True)
    monkeypatch.setattr(redis_client, "ALLOW_DEGRADED_REDIS", False)

    with pytest.raises(RuntimeError, match="REDIS_URL must be set in production"):
        redis_client._build_cache()


def test_production_degraded_redis_requires_explicit_ack(monkeypatch):
    monkeypatch.setattr(redis_client, "REDIS_URL", "redis://synthetic.invalid/0")
    monkeypatch.setattr(redis_client, "IS_PRODUCTION", True)
    monkeypatch.setattr(redis_client, "ALLOW_DEGRADED_REDIS", True)
    monkeypatch.setattr(redis_client, "_RedisWrapper", _raise_connection_error)

    cache = redis_client._build_cache()

    assert isinstance(cache, redis_client._MemoryStore)
    assert cache.ping() is True
