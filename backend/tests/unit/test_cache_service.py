from __future__ import annotations

import threading
import time

import pytest

from app.services import cache_service


def test_cache_key_is_tenant_scoped_and_does_not_embed_dimensions() -> None:
    first = cache_service.cache_key("immunization_report", 10, year=2026, month=8)
    second = cache_service.cache_key("immunization_report", 11, year=2026, month=8)
    assert first != second
    assert "2026" not in first
    assert "patient" not in first.lower()


def test_cache_key_rejects_personal_or_clinical_dimensions() -> None:
    with pytest.raises(ValueError):
        cache_service.cache_key("immunization_report", 10, patient_id="synthetic-only")


def test_get_or_set_single_flight_calls_loader_once(monkeypatch: pytest.MonkeyPatch) -> None:
    cache_service._single_flight.clear()
    store: dict[str, str] = {}

    monkeypatch.setattr(cache_service.cache, "get", lambda key: store.get(key))
    monkeypatch.setattr(cache_service.cache, "set", lambda key, value, ex=None: store.__setitem__(key, value))
    calls = 0
    calls_lock = threading.Lock()

    def loader() -> dict[str, int]:
        nonlocal calls
        with calls_lock:
            calls += 1
        time.sleep(0.02)
        return {"scheduled": 3}

    results: list[dict[str, int]] = []
    threads = [threading.Thread(target=lambda: results.append(cache_service.get_or_set("k", loader, ttl_seconds=10))) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert calls == 1
    assert results == [{"scheduled": 3}] * 5


def test_cache_outage_falls_back_to_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cache_service.cache, "get", lambda key: (_ for _ in ()).throw(RuntimeError("redis down")))
    monkeypatch.setattr(cache_service.cache, "set", lambda key, value, ex=None: (_ for _ in ()).throw(RuntimeError("redis down")))
    assert cache_service.get_or_set("outbox-key", lambda: {"pending": 2}, ttl_seconds=10) == {"pending": 2}
