"""Redis client for GULA Platform.
Provides a thin wrapper with automatic fallback to an in-memory store
when Redis is not configured or unreachable — so the app works in dev
without Redis and in production with it.

Usage:
    from .redis_client import cache
    cache.set("key", "value", ex=3600)
    value = cache.get("key")          # returns str | None
    cache.delete("key")
"""

import logging
import threading
import time

from ..config import IS_PRODUCTION, REDIS_URL

logger = logging.getLogger("gula.redis")

# ── In-memory fallback ────────────────────────────────────────────────────────


class _MemoryStore:
    """Thread-safe in-memory key-value store with TTL support."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[str, float | None]] = {}  # key → (value, expire_at)
        self._lock = threading.Lock()

    def set(self, key: str, value: str | int | float | bytes, ex: int | None = None) -> None:
        expire_at = time.monotonic() + ex if ex else None
        with self._lock:
            self._data[key] = (str(value), expire_at)

    def set_if_absent(self, key: str, value: str | int | float | bytes, ex: int | None = None) -> bool:
        expire_at = time.monotonic() + ex if ex else None
        with self._lock:
            entry = self._data.get(key)
            if entry is not None:
                if entry[1] is None or time.monotonic() <= entry[1]:
                    return False
                del self._data[key]
            self._data[key] = (str(value), expire_at)
            return True

    def get(self, key: str) -> str | None:
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            value, expire_at = entry
            if expire_at is not None and time.monotonic() > expire_at:
                del self._data[key]
                return None
            return value

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def incr(self, key: str) -> int:
        with self._lock:
            entry = self._data.get(key)
            current = int(entry[0]) if entry else 0
            new_val = current + 1
            expire_at = entry[1] if entry else None
            self._data[key] = (str(new_val), expire_at)
            return new_val

    def expire(self, key: str, seconds: int) -> None:
        with self._lock:
            entry = self._data.get(key)
            if entry is not None:
                self._data[key] = (entry[0], time.monotonic() + seconds)

    @property
    def is_shared(self) -> bool:
        return False

    def ping(self) -> bool:
        """Always return True for in-memory store as it's always 'available'."""
        return True


# ── Redis wrapper ─────────────────────────────────────────────────────────────


class _RedisWrapper:
    """Thin wrapper around redis-py that exposes set/get/delete/incr/ping.
    Constructed lazily so import doesn't fail if redis-py is not installed.
    """

    def __init__(self, url: str) -> None:
        import redis as _redis

        self._client = _redis.from_url(url, decode_responses=True, socket_timeout=1)
        # Verify connection at startup
        self._client.ping()
        logger.info("Redis connected: %s", url.rsplit("@", maxsplit=1)[-1])

    def set(self, key: str, value: str | int | float | bytes, ex: int | None = None) -> None:
        self._client.set(key, value, ex=ex)

    def set_if_absent(self, key: str, value: str | int | float | bytes, ex: int | None = None) -> bool:
        return bool(self._client.set(key, value, ex=ex, nx=True))

    def get(self, key: str) -> str | None:
        value = self._client.get(key)
        return value.decode() if isinstance(value, bytes) else value

    def delete(self, key: str) -> None:
        self._client.delete(key)

    def incr(self, key: str) -> int:
        return self._client.incr(key)

    def expire(self, key: str, seconds: int) -> None:
        self._client.expire(key, seconds)

    @property
    def is_shared(self) -> bool:
        return True

    def ping(self) -> bool:
        """Ping Redis — raises on failure so callers can catch it."""
        self._client.ping()
        return True


# ── Public singleton ──────────────────────────────────────────────────────────


def _build_cache() -> _MemoryStore | _RedisWrapper:
    if REDIS_URL:
        try:
            return _RedisWrapper(REDIS_URL)
        except Exception as exc:
            if IS_PRODUCTION:
                # In production Redis is mandatory for full functionality, but we allow
                # the system to start in degraded mode if it's unreachable.
                # The self-healing system will attempt to recover it.
                logger.critical(
                    "[GULA CRITICAL] Redis is unreachable in production: %s. "
                    "Falling back to in-memory store (degraded mode).",
                    exc,
                )
            logger.warning("Redis unavailable (%s) — falling back to in-memory store", exc)
    else:
        if IS_PRODUCTION:
            logger.critical(
                "[GULA CRITICAL] REDIS_URL is not set in production. "
                "Falling back to in-memory store (degraded mode).",
            )
        logger.info("REDIS_URL not set — using in-memory store (not shared across workers)")
    return _MemoryStore()


cache: _MemoryStore | _RedisWrapper = _build_cache()
