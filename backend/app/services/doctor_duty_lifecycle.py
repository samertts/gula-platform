"""Fail-closed lifecycle hooks for Duty expiry.

Clinical payloads are never stored here. The registry only tracks opaque cache keys
and callback handles so context expiry can revoke UI capabilities immediately.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from threading import RLock

from app.services.cache_service import delete as delete_cache


class DutyLifecycleRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._cache_keys: dict[str, set[str]] = defaultdict(set)
        self._stop_callbacks: dict[str, list[Callable[[], None]]] = defaultdict(list)

    def register_cache_key(self, duty_context_id: str, key: str) -> None:
        if not duty_context_id or not key:
            raise ValueError("duty_context_id and key are required")
        with self._lock:
            self._cache_keys[duty_context_id].add(key)

    def register_stop_callback(self, duty_context_id: str, callback: Callable[[], None]) -> None:
        with self._lock:
            self._stop_callbacks[duty_context_id].append(callback)

    def revoke(self, duty_context_id: str) -> dict[str, int]:
        with self._lock:
            keys = tuple(self._cache_keys.pop(duty_context_id, set()))
            callbacks = tuple(self._stop_callbacks.pop(duty_context_id, []))
        deleted = sum(1 for key in keys if delete_cache(key))
        stopped = 0
        for callback in callbacks:
            try:
                callback()
                stopped += 1
            except Exception:
                # Revocation remains fail-closed even if a UI integration is down.
                continue
        return {"cache_keys_invalidated": deleted, "stop_callbacks_called": stopped}

    def clear(self) -> None:
        with self._lock:
            self._cache_keys.clear()
            self._stop_callbacks.clear()


duty_lifecycle = DutyLifecycleRegistry()
