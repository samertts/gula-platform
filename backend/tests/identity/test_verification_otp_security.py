from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import app.routes.verification as verification_route
import pytest
from app.security.redis_client import _MemoryStore
from fastapi import HTTPException


def test_memory_cache_set_if_absent_is_atomic_under_concurrency() -> None:
    store = _MemoryStore()

    def claim() -> bool:
        return bool(store.set_if_absent("verification:consumed:test", "1", ex=60))

    with ThreadPoolExecutor(max_workers=16) as executor:
        results = list(executor.map(lambda _index: claim(), range(64)))

    assert sum(results) == 1
    assert store.get("verification:consumed:test") == "1"


def test_production_verification_rejects_unshared_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(verification_route, "IS_PRODUCTION", True)
    monkeypatch.setattr(verification_route, "cache", _MemoryStore())

    with pytest.raises(HTTPException) as exc_info:
        verification_route._ensure_shared_cache_for_production()

    assert exc_info.value.status_code == 503


def test_production_verification_accepts_shared_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(verification_route, "IS_PRODUCTION", True)
    monkeypatch.setattr(verification_route, "cache", SimpleNamespace(is_shared=True))

    verification_route._ensure_shared_cache_for_production()
