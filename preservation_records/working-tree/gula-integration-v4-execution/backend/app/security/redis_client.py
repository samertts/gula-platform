"""Redis client for GULA Platform.

Provides a thin wrapper with automatic fallback to an in-memory store in local
development and tests. In production/staging the fallback is **fail-closed**:
the process refuses to run with process-local security state unless the operator
explicitly sets ``ALLOW_DEGRADED_REDIS=true`` (see S-06).

Usage:
    from .redis_client import cache
    cache.set("key", "value", ex=3600)
    value = cache.get("key")          # returns str | None
    cache.delete("key")
"""

import logging
import os
import threading
import time

from ..config import IS_PRODUCTION, REDIS_URL

logger = logging.getLogger("gula.redis")

# ── In-memory fallback ────────────────────────────────────────────────────────


class SecurityStoreUnavailable(RuntimeError):
    """Shared security state (Redis) is required but unavailable.

    Raised instead of silently downgrading token revocation, rate limiting and
    idempotency to a per-process dictionary.
    """


class _MemoryStore:
    """Thread-safe in-memory key-value store with TTL support.

    Process-local: revocation, rate limits and ``set_if_absent`` claims are NOT
    shared across workers. Only acceptable in development/test or when the
    deployment has explicitly acknowledged degraded mode.
    """

    is_shared = False
    is_degraded = True


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

    is_shared = True
    is_degraded = False

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


def _degraded_mode_allowed() -> bool:
    """Whether process-local security state is explicitly acceptable.

    Development and test may run without Redis for convenience. A production or
    staging deployment must opt in explicitly via ``ALLOW_DEGRADED_REDIS=true``
    (documented operational decision) — otherwise we fail closed.
    """
    if not IS_PRODUCTION:
        return True
    return os.getenv("ALLOW_DEGRADED_REDIS", "false").lower() == "true"


def _build_cache() -> _MemoryStore | _RedisWrapper:
    if REDIS_URL:
        try:
            return _RedisWrapper(REDIS_URL)
        except Exception as exc:
            # The process may still start so liveness/readiness probes can
            # report the outage; security-critical callers use
            # ``security_store()`` and fail closed in production.
            if _degraded_mode_allowed():
                logger.critical(
                    "[GULA CRITICAL] Redis is unreachable: %s. Running in "
                    "explicitly acknowledged degraded mode (process-local "
                    "security state; NOT shared across workers).",
                    exc,
                )
            else:
                logger.critical(
                    "[GULA CRITICAL] Redis is unreachable: %s. Security-critical "
                    "operations will fail closed until it recovers.",
                    exc,
                )
            return _MemoryStore()
    if _degraded_mode_allowed():
        logger.warning(
            "REDIS_URL not set — using an explicitly acknowledged in-memory store "
            "(not shared across workers)",
        )
    else:
        logger.critical(
            "[GULA CRITICAL] REDIS_URL is not set. Security-critical operations "
            "will fail closed until shared state is configured.",
        )
    return _MemoryStore()


cache: _MemoryStore | _RedisWrapper = _build_cache()


def security_store(operation: str) -> _MemoryStore | _RedisWrapper:
    """Return the cache for a security-critical operation, failing closed.

    Token revocation, rate limiting and idempotency claims are only valid when
    the backing store is shared across workers. In production/staging a
    process-local fallback is refused unless the deployment explicitly set
    ``ALLOW_DEGRADED_REDIS=true`` (documented operational decision).
    """
    if not getattr(cache, "is_shared", False) and not _degraded_mode_allowed():
        raise SecurityStoreUnavailable(
            f"{operation} requires shared Redis state; process-local fallback "
            "is not permitted in production/staging.",
        )
    return cache


def is_shared_security_state() -> bool:
    """True when revocation/rate-limit/idempotency state is shared across workers."""
    return bool(getattr(cache, "is_shared", False))
