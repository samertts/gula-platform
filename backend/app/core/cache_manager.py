"""
Multi-Level Cache Manager — GULA Platform
===========================================
Implements L1 (in-memory) + L2 (Redis) + L3 (PostgreSQL/loader) cache-aside strategy.

Architecture:
  L1 — Thread-safe in-memory dict with TTL (30–60s default, max 10 000 entries)
  L2 — Redis via ``redis_client.cache`` singleton
  L3 — Caller-provided async loader function (e.g. database query)

Degradation awareness (integrated with ``self_healing.health``):
  L1_CACHE_HEAVY   → skip L2 reads/writes; use only L1 + L3
  L2_READ_ONLY     → skip L2 writes; L2 reads still permitted
  L3_CRITICAL_ONLY → skip all caching; fall through to loader only

Usage:
  from app.core.cache_manager import cache_manager, cached

  # Direct API
  value = await cache_manager.get("gula:patient:123:profile", loader=load_patient)
  await cache_manager.set("gula:patient:123:profile", value, ttl=300)
  await cache_manager.invalidate("gula:patient:123:*")

  # Decorator
  @cached(ttl=300, prefix="patient", key_from_args=0)
  async def get_patient(patient_id: int): ...
"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
import os
import threading
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("gula.cache")

# ─── Environment Configuration ───────────────────────────────────────────────

_DEFAULT_L1_TTL = int(os.getenv("CACHE_L1_TTL", "60"))
_DEFAULT_L2_TTL = int(os.getenv("CACHE_L2_TTL", "300"))
_L1_MAX_SIZE = int(os.getenv("CACHE_L1_MAX_SIZE", "10000"))
_CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() != "false"
_CACHE_METRICS_ENABLED = os.getenv("CACHE_METRICS_ENABLED", "true").lower() != "false"

# ─── CacheStats ──────────────────────────────────────────────────────────────


@dataclass
class CacheStats:
    """Snapshot of cache performance counters and current size."""

    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0
    l1_size: int = 0
    l2_size: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hit_count + self.miss_count
        if total == 0:
            return 0.0
        return round(self.hit_count / total, 4)

    @property
    def size(self) -> int:
        return self.l1_size

    def to_dict(self) -> dict[str, Any]:
        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "eviction_count": self.eviction_count,
            "hit_rate": self.hit_rate,
            "size": self.size,
            "l1_size": self.l1_size,
            "l2_size": self.l2_size,
        }


# ─── L1: Thread-safe In-Memory Cache ─────────────────────────────────────────


class _L1Cache:
    """Thread-safe in-memory cache with TTL and LRU-ish eviction."""

    def __init__(self, max_size: int = _L1_MAX_SIZE, default_ttl: int = _DEFAULT_L1_TTL):
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._data: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        ts = time.monotonic()
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            value, expire_at = entry
            if ts > expire_at:
                del self._data[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        expire_at = time.monotonic() + (ttl if ttl is not None else self._default_ttl)
        with self._lock:
            if key not in self._data and len(self._data) >= self._max_size:
                self._evict_one()
            self._data[key] = (value, expire_at)

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def delete_pattern(self, prefix: str) -> int:
        count = 0
        with self._lock:
            keys = [k for k in self._data if k.startswith(prefix)]
            for k in keys:
                del self._data[k]
                count += 1
        return count

    def _evict_one(self) -> None:
        if not self._data:
            return
        oldest_key = next(iter(self._data))
        del self._data[oldest_key]

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._data)

    def keys(self) -> list[str]:
        with self._lock:
            return list(self._data.keys())


# ─── CacheManager Singleton ──────────────────────────────────────────────────


class CacheManager:
    """Multi-level cache manager with L1→L2→L3 cascading fallback.

    Implements the cache-aside pattern: load on miss, store for next time.
    Integrates with the system's degradation model via ``self_healing.health``.
    """

    def __init__(self) -> None:
        self._l1 = _L1Cache()
        self._hit_count = 0
        self._miss_count = 0
        self._eviction_count = 0
        self._stats_lock = threading.Lock()
        self._ttl_overrides: dict[str, int] = {}
        self._lock = threading.Lock()

    # ── Public Configuration ─────────────────────────────────────────────────

    def configure_ttl(self, domain: str, ttl: int) -> None:
        """Override default TTL for a domain.

        Domain is the first segment of the cache key (e.g. ``patient``
        for ``gula:patient:...``).
        """
        with self._lock:
            self._ttl_overrides[domain] = ttl

    def _resolve_ttl(self, key: str, fallback_l2: int | None = None) -> tuple[int, int]:
        domain = key.split(":")[0] if ":" in key else ""
        if domain == "gula" and key.count(":") >= 2:
            domain = key.split(":")[1]
        override = self._ttl_overrides.get(domain)
        if override is not None:
            return override, override
        return _DEFAULT_L1_TTL, fallback_l2 or _DEFAULT_L2_TTL

    # ── Core Get ─────────────────────────────────────────────────────────────

    async def get(
        self,
        key: str,
        loader: Callable[[], Awaitable[Any]] | None = None,
        ttl: int | None = None,
        l2_ttl: int | None = None,
    ) -> Any | None:
        """Retrieve a value from the cache hierarchy.

        Steps:
          1. Check L1 (in-memory).
          2. If miss and not L1_CACHE_HEAVY: check L2 (Redis).
          3. If miss and loader provided: call loader → store in L1 (+ L2 if allowed).
        """
        if not _CACHE_ENABLED and loader is not None:
            return await loader()

        l1_ttl, resolved_l2_ttl = self._resolve_ttl(key, l2_ttl)
        actual_l1_ttl = ttl or l1_ttl
        actual_l2_ttl = l2_ttl or resolved_l2_ttl

        level = self._get_degradation_level()

        from app.core.self_healing import DegradationLevel

        if level == DegradationLevel.L3_CRITICAL_ONLY and loader is not None:
            return await loader()

        value = self._l1.get(key)
        if value is not None:
            self._record_hit()
            return value

        if level != DegradationLevel.L1_CACHE_HEAVY:
            value = await self._l2_get(key)
            if value is not None:
                self._record_hit()
                self._l1.set(key, value, ttl=_DEFAULT_L1_TTL)
                return value

        if loader is not None:
            value = await loader()
            if value is not None:
                self._l1.set(key, value, ttl=actual_l1_ttl)
                if level not in (
                    DegradationLevel.L1_CACHE_HEAVY,
                    DegradationLevel.L2_READ_ONLY,
                ):
                    await self._l2_set(key, value, ex=actual_l2_ttl)
            self._record_miss()
            return value

        self._record_miss()
        return None

    # ── Core Set ─────────────────────────────────────────────────────────────

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        l2_ttl: int | None = None,
    ) -> None:
        """Write a value to L1 and, if degradation permits, L2."""
        if not _CACHE_ENABLED:
            return

        l1_ttl, resolved_l2_ttl = self._resolve_ttl(key, l2_ttl)
        actual_l1_ttl = ttl or l1_ttl
        actual_l2_ttl = l2_ttl or resolved_l2_ttl

        level = self._get_degradation_level()

        from app.core.self_healing import DegradationLevel

        if level == DegradationLevel.L3_CRITICAL_ONLY:
            return

        self._l1.set(key, value, ttl=actual_l1_ttl)

        if level not in (DegradationLevel.L1_CACHE_HEAVY, DegradationLevel.L2_READ_ONLY):
            await self._l2_set(key, value, ex=actual_l2_ttl)

    # ── Delete & Invalidation ────────────────────────────────────────────────

    async def delete(self, key: str) -> None:
        """Evict a single key from both L1 and L2."""
        self._l1.delete(key)
        try:
            from app.security.redis_client import cache as redis_cache

            redis_cache.delete(key)
        except Exception:
            pass

    async def invalidate(self, pattern: str) -> int:
        """Evict all keys matching a prefix pattern from L1 and L2.

        Returns the total number of keys invalidated across both layers.
        """
        count = self._l1.delete_pattern(pattern)
        count += await self._l2_delete_pattern(pattern)
        return count

    # ── Bulk Operations ──────────────────────────────────────────────────────

    async def get_many(
        self,
        keys: list[str],
        loader: Callable[[list[str]], Awaitable[dict[str, Any]]] | None = None,
        ttl: int | None = None,
        l2_ttl: int | None = None,
    ) -> dict[str, Any]:
        """Retrieve multiple keys in batch.

        Missing keys are loaded via the bulk *loader* which receives the
        list of missing keys and must return ``{key: value, ...}``.
        """
        result: dict[str, Any] = {}
        missing: list[str] = []

        for key in keys:
            val = await self.get(key, loader=None, ttl=ttl, l2_ttl=l2_ttl)
            if val is not None:
                result[key] = val
            else:
                missing.append(key)

        if missing and loader is not None:
            loaded = await loader(missing)
            for key, value in loaded.items():
                if value is not None:
                    await self.set(key, value, ttl=ttl, l2_ttl=l2_ttl)
                    result[key] = value

        return result

    async def set_many(
        self,
        mapping: dict[str, Any],
        ttl: int | None = None,
        l2_ttl: int | None = None,
    ) -> None:
        """Write multiple key-value pairs."""
        for key, value in mapping.items():
            await self.set(key, value, ttl=ttl, l2_ttl=l2_ttl)

    # ── Cache Warming ────────────────────────────────────────────────────────

    async def warm(
        self,
        keys: list[str],
        loader: Callable[[str], Awaitable[Any]],
        ttl: int | None = None,
        l2_ttl: int | None = None,
    ) -> int:
        """Pre-populate the cache with eagerly loaded keys.

        Iterates *keys*, calls *loader(key)* for each, and stores the
        result.  Returns the number of successfully cached entries.
        """
        count = 0
        for key in keys:
            try:
                value = await loader(key)
                if value is not None:
                    await self.set(key, value, ttl=ttl, l2_ttl=l2_ttl)
                    count += 1
            except Exception:
                logger.warning("[CACHE] Warm failed for key=%s", key, exc_info=True)
        logger.info("[CACHE] Warmed %d/%d keys", count, len(keys))
        return count

    # ── Stats ────────────────────────────────────────────────────────────────

    def stats(self) -> CacheStats:
        """Return a snapshot of current cache statistics."""
        with self._stats_lock:
            return CacheStats(
                hit_count=self._hit_count,
                miss_count=self._miss_count,
                eviction_count=self._eviction_count,
                l1_size=self._l1.size,
                l2_size=0,
            )

    def reset_stats(self) -> None:
        """Zero out hit/miss/eviction counters."""
        with self._stats_lock:
            self._hit_count = 0
            self._miss_count = 0
            self._eviction_count = 0

    def clear(self) -> None:
        """Flush all L1 entries (L2 is untouched)."""
        self._l1.clear()

    # ── Internal Helpers ─────────────────────────────────────────────────────

    def _get_degradation_level(self):
        try:
            from app.core.self_healing import DegradationLevel, health

            return health.degradation_level
        except Exception:
            from app.core.self_healing import DegradationLevel

            return DegradationLevel.NONE

    async def _l2_get(self, key: str) -> Any | None:
        try:
            from app.security.redis_client import cache as redis_cache

            raw = redis_cache.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            return None

    async def _l2_set(self, key: str, value: Any, ex: int = _DEFAULT_L2_TTL) -> None:
        try:
            from app.security.redis_client import cache as redis_cache

            redis_cache.set(key, json.dumps(value, ensure_ascii=False, default=str), ex=ex)
        except Exception:
            pass

    async def _l2_delete_pattern(self, pattern: str) -> int:
        try:
            from app.security.redis_client import cache as redis_cache

            client = getattr(redis_cache, "_client", None)
            if client is None:
                return 0
            import redis as _redis_module

            if not isinstance(client, _redis_module.Redis):
                return 0
            count = 0
            cursor = 0
            while True:
                cursor, keys = client.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    client.delete(*keys)
                    count += len(keys)
                if cursor == 0:
                    break
            return count
        except Exception:
            return 0

    def _record_hit(self) -> None:
        if _CACHE_METRICS_ENABLED:
            with self._stats_lock:
                self._hit_count += 1

    def _record_miss(self) -> None:
        if _CACHE_METRICS_ENABLED:
            with self._stats_lock:
                self._miss_count += 1


# ─── Module-level singleton ──────────────────────────────────────────────────

cache_manager = CacheManager()


# ─── Utilities ───────────────────────────────────────────────────────────────


def build_cache_key(prefix: str, *args, **kwargs) -> str:
    """Build a cache key following the ``gula:{prefix}:{arg}:...`` convention.

    If the raw key exceeds 250 characters it is hashed to a fixed-length key.
    """
    parts = [prefix]
    for arg in args:
        parts.append(str(arg))
    for k, v in kwargs.items():
        parts.append(f"{k}={v}")
    raw = ":".join(parts)
    full_key = raw if raw.startswith("gula:") else f"gula:{raw}"
    if len(full_key) > 250:
        digest = hashlib.sha256(full_key.encode()).hexdigest()[:16]
        full_key = f"gula:{prefix}:{digest}"
    return full_key


# ─── @cached Decorator ───────────────────────────────────────────────────────


def cached(
    ttl: int | None = None,
    l2_ttl: int | None = None,
    prefix: str = "",
    key_from_args: int | None = None,
    key_fn: Callable[..., str] | None = None,
):
    """Decorator that caches the return value of an async function.

    Parameters
    ----------
    ttl : int, optional
        L1 TTL in seconds for the cached value.  Falls back to
        ``CACHE_L1_TTL`` / domain override when not set.
    l2_ttl : int, optional
        L2 (Redis) TTL in seconds.
    prefix : str
        Cache key prefix (e.g. ``"patient"``).  Defaults to the function name.
    key_from_args : int, optional
        Positional index of the argument to use as the unique cache key
        suffix.  E.g. ``key_from_args=0`` uses the first argument.
    key_fn : callable, optional
        Custom callable ``(*args, **kwargs) -> str`` that returns the
        full cache key.  Takes precedence over *key_from_args*.

    Examples
    --------
    @cached(ttl=300, prefix="patient", key_from_args=0)
    async def get_patient(patient_id: int) -> dict: ...

    @cached(ttl=600, key_fn=lambda lab_id, status: f"gula:lab:{lab_id}:orders:{status}")
    async def get_orders(lab_id: int, status: str) -> list: ...
    """

    def decorator(func):
        name = prefix or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not _CACHE_ENABLED:
                return await func(*args, **kwargs)

            if key_fn is not None:
                cache_key = key_fn(*args, **kwargs)
            elif key_from_args is not None:
                key_arg = args[key_from_args] if key_from_args < len(args) else None
                cache_key = build_cache_key(name, key_arg)
            else:
                cache_key = build_cache_key(name, *args, **kwargs)

            async def loader():
                return await func(*args, **kwargs)

            return await cache_manager.get(cache_key, loader=loader, ttl=ttl, l2_ttl=l2_ttl)

        return wrapper

    return decorator
