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

from ..config import ALLOW_DEGRADED_REDIS, ENV, REDIS_URL

logger = logging.getLogger("gula.redis")


class CacheUnavailable(RuntimeError):
    """Raised when a sensitive operation has no shared Redis backend."""


_SHARED_CACHE_REQUIRED = ENV.lower() in {"staging", "production"} and not ALLOW_DEGRADED_REDIS


def shared_cache_required() -> bool:
    return _SHARED_CACHE_REQUIRED


# ── In-memory fallback ────────────────────────────────────────────────────────


class _MemoryStore:
    """Thread-safe in-memory key-value store with TTL support."""

    is_shared = False
    backend_name = "memory"

    def __init__(self) -> None:
        self._data: dict[str, tuple[str, float | None]] = {}  # key → (value, expire_at)
        self._lock = threading.Lock()

    def set(self, key: str, value: str | int | float | bytes, ex: int | None = None) -> None:
        expire_at = time.monotonic() + ex if ex else None
        with self._lock:
            self._data[key] = (str(value), expire_at)

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

    def ping(self) -> bool:
        """Always return True for in-memory store as it's always 'available'."""
        return True


class _UnavailableStore:
    """Explicit fail-closed backend used when shared Redis is mandatory."""

    is_shared = False
    backend_name = "unavailable"

    def _raise(self) -> None:
        raise CacheUnavailable("Shared Redis is unavailable for this runtime")

    def set(self, *args, **kwargs) -> None:
        self._raise()

    def get(self, *args, **kwargs) -> str | None:
        self._raise()

    def delete(self, *args, **kwargs) -> None:
        self._raise()

    def incr(self, *args, **kwargs) -> int:
        self._raise()

    def expire(self, *args, **kwargs) -> None:
        self._raise()

    def ping(self) -> bool:
        self._raise()


# ── Redis wrapper ─────────────────────────────────────────────────────────────


class _RedisWrapper:
    """Thin wrapper around redis-py that exposes set/get/delete/incr/ping.
    Constructed lazily so import doesn't fail if redis-py is not installed.
    """

    is_shared = True
    backend_name = "redis"

    def __init__(self, url: str) -> None:
        import redis as _redis

        self._client = _redis.from_url(url, decode_responses=True, socket_timeout=1)
        # Verify connection at startup
        self._client.ping()
        logger.info("Redis connected: %s", url.rsplit("@", maxsplit=1)[-1])

    def set(self, key: str, value: str | int | float | bytes, ex: int | None = None) -> None:
        self._client.set(key, value, ex=ex)

    def get(self, key: str) -> str | None:
        value = self._client.get(key)
        return value.decode() if isinstance(value, bytes) else value

    def delete(self, key: str) -> None:
        self._client.delete(key)

    def incr(self, key: str) -> int:
        return self._client.incr(key)

    def expire(self, key: str, seconds: int) -> None:
        self._client.expire(key, seconds)

    def ping(self) -> bool:
        """Ping Redis — raises on failure so callers can catch it."""
        self._client.ping()
        return True


# ── Public singleton ──────────────────────────────────────────────────────────


def _build_cache() -> _MemoryStore | _RedisWrapper | _UnavailableStore:
    if REDIS_URL:
        try:
            return _RedisWrapper(REDIS_URL)
        except Exception as exc:
            if _SHARED_CACHE_REQUIRED:
                logger.critical(
                    "Redis is unreachable while shared cache is mandatory: %s. "
                    "The runtime will fail closed for sensitive operations.",
                    exc,
                )
                return _UnavailableStore()
            logger.warning("Redis unavailable (%s) — using explicitly allowed in-memory store", exc)
    else:
        if _SHARED_CACHE_REQUIRED:
            logger.critical(
                "REDIS_URL is not set while shared cache is mandatory. "
                "The runtime will fail closed for sensitive operations.",
            )
            return _UnavailableStore()
        logger.info("REDIS_URL not set — using explicitly allowed in-memory store")
    return _MemoryStore()


def ensure_shared_cache() -> None:
    """Fail closed when an operation requires cross-worker Redis semantics."""
    if not _SHARED_CACHE_REQUIRED:
        return
    if not getattr(cache, "is_shared", False):
        raise CacheUnavailable("Shared Redis is required for this operation")
    cache.ping()


cache: _MemoryStore | _RedisWrapper | _UnavailableStore = _build_cache()
