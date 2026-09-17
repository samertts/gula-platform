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

    def set_if_absent(self, key: str, value: str | int | float | bytes, ex: int | None = None) -> bool:
        expire_at = time.monotonic() + ex if ex else None
        with self._lock:
            entry = self._data.get(key)
            if entry is not None:
                if entry[1] is not None and time.monotonic() > entry[1]:
                    del self._data[key]
                else:
                    return False
            self._data[key] = (str(value), expire_at)
            return True

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

    def get(self, key: str) -> str | None:
        value = self._client.get(key)
        return value.decode() if isinstance(value, bytes) else value

    def set_if_absent(self, key: str, value: str | int | float | bytes, ex: int | None = None) -> bool:
        return bool(self._client.set(key, value, ex=ex, nx=True))

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


def is_shared() -> bool:
    """True when the cache is Redis-backed and therefore shared across workers.

    False means this process fell back to `_MemoryStore`, which is per-process.
    Everything built on the cache degrades with it, and not uniformly visibly:
    token revocation (security/auth.py blacklist_token), sessions, rate
    limiting, MFA challenges, the API firewall and HTTP idempotency all become
    worker-local while continuing to behave normally within one worker.

    `_MemoryStore.ping()` returns True unconditionally, so a liveness ping
    cannot answer this question. Ask this instead.
    """
    return not isinstance(cache, _MemoryStore)


def degraded_reason() -> str:
    """Why the cache is not shared, phrased for an operator. Empty when shared."""
    if is_shared():
        return ""
    if not REDIS_URL:
        return (
            "REDIS_URL is not set, so this process is using a per-worker in-memory "
            "store. Token revocation, sessions, rate limiting and idempotency are "
            "not shared across workers."
        )
    return (
        "REDIS_URL is set but Redis was unreachable when this process started, so "
        "it fell back to a per-worker in-memory store. The fallback is decided once "
        "at import and is NOT re-attempted, so this process will not recover even "
        "after Redis returns; it needs a restart. Token revocation, sessions, rate "
        "limiting and idempotency are not shared across workers until then."
    )
