from __future__ import annotations

import pytest
from app.security.mfa_service import MFAService


class _ChallengeStore:
    def __init__(self, value: str | None):
        self.value = value
        self.deleted_keys: list[str] = []

    def get_and_delete(self, key: str) -> str | None:
        self.deleted_keys.append(key)
        value, self.value = self.value, None
        return value


class _Query:
    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return None


class _DB:
    def query(self, *args, **kwargs):
        return _Query()


def test_webauthn_challenge_is_consumed_before_unknown_credential(monkeypatch):
    store = _ChallengeStore("single-use-challenge")
    service = MFAService(_DB())
    monkeypatch.setattr(service, "_challenge_cache", lambda: store)

    assert service.complete_webauthn_authentication(42, {"id": "unknown"}) is False
    assert store.deleted_keys == ["webauthn:challenge:42"]
    assert store.value is None


def test_mfa_challenge_cache_fails_closed_without_shared_backend(monkeypatch):
    from app.security import mfa_service, redis_client

    class _UnsharedCache:
        is_shared = False

    monkeypatch.setattr(mfa_service, "IS_PRODUCTION", True)
    monkeypatch.setattr(redis_client, "cache", _UnsharedCache())

    with pytest.raises(RuntimeError, match="challenge store unavailable"):
        MFAService(_DB())._challenge_cache()
