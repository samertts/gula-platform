from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from app._compat import StrEnum
from app.kernel import Kernel

logger = logging.getLogger("gula.kernel.runtime_performance")


class EvictionPolicy(StrEnum):
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"
    ADAPTIVE = "adaptive"


@dataclass
class CacheEntry:
    key: str
    value: Any
    size: int = 1
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    ttl: float = 300.0
    access_count: int = 0
    hit_count: int = 0

    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl

    def record_access(self) -> None:
        self.accessed_at = time.time()
        self.access_count += 1
        self.hit_count += 1


class AdaptiveCache:
    def __init__(
        self,
        name: str,
        max_size: int = 1000,
        default_ttl: float = 300.0,
        eviction_policy: EvictionPolicy = EvictionPolicy.ADAPTIVE,
        min_ttl: float = 10.0,
        max_ttl: float = 3600.0,
    ):
        self.name = name
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.eviction_policy = eviction_policy
        self.min_ttl = min_ttl
        self.max_ttl = max_ttl
        self._entries: dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._hits: int = 0
        self._misses: int = 0
        self._evictions: int = 0
        self._access_patterns: deque[float] = deque(maxlen=1000)

    @property
    def size(self) -> int:
        return len(self._entries)

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return round(self._hits / max(1, total) * 100, 1)

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._entries.get(key)
            if not entry or entry.is_expired():
                self._misses += 1
                self._entries.pop(key, None)
                return None
            entry.record_access()
            self._hits += 1
            self._access_patterns.append(time.time())
            self._adapt_ttl(entry)
            return entry.value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        with self._lock:
            if len(self._entries) >= self.max_size:
                self._evict()
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl or self.default_ttl,
            )
            self._entries[key] = entry

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._entries.pop(key, None) is not None

    def clear(self) -> int:
        with self._lock:
            count = len(self._entries)
            self._entries.clear()
            return count

    def _evict(self) -> None:
        if not self._entries:
            return
        policy = self.eviction_policy
        if policy == EvictionPolicy.ADAPTIVE:
            policy = self._select_policy()

        if policy == EvictionPolicy.LRU:
            key = min(self._entries, key=lambda k: self._entries[k].accessed_at)
        elif policy == EvictionPolicy.LFU:
            key = min(self._entries, key=lambda k: self._entries[k].access_count)
        elif policy == EvictionPolicy.FIFO:
            key = min(self._entries, key=lambda k: self._entries[k].created_at)
        else:
            key = min(self._entries, key=lambda k: self._entries[k].created_at)
        self._entries.pop(key, None)
        self._evictions += 1

    def _select_policy(self) -> EvictionPolicy:
        if self.hit_rate > 80:
            return EvictionPolicy.LRU
        if self.hit_rate > 50:
            return EvictionPolicy.TTL
        return EvictionPolicy.LFU

    def _adapt_ttl(self, entry: CacheEntry) -> None:
        if self.eviction_policy != EvictionPolicy.ADAPTIVE:
            return
        if entry.access_count > 10:
            entry.ttl = min(entry.ttl * 1.5, self.max_ttl)
        elif entry.access_count < 3 and time.time() - entry.created_at > 60:
            entry.ttl = max(entry.ttl * 0.8, self.min_ttl)

    def get_stats(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "size": self.size,
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate,
            "evictions": self._evictions,
            "policy": self.eviction_policy.value,
            "default_ttl": self.default_ttl,
        }


class DynamicScaler:
    def __init__(self, name: str, min_workers: int = 1, max_workers: int = 10):
        self.name = name
        self.min_workers = min_workers
        self.max_workers = max_workers
        self._current_workers: int = min_workers
        self._target_workers: int = min_workers
        self._load_history: deque[float] = deque(maxlen=60)
        self._lock = Lock()
        self._scale_up_count: int = 0
        self._scale_down_count: int = 0

    @property
    def current_workers(self) -> int:
        return self._current_workers

    def record_load(self, load_percent: float) -> None:
        self._load_history.append(load_percent)

    def analyze(self) -> dict[str, Any]:
        with self._lock:
            if not self._load_history:
                return {"recommended": self._current_workers, "stable": True}
            avg_load = sum(self._load_history) / len(self._load_history)
            if avg_load > 80 and self._current_workers < self.max_workers:
                self._target_workers = min(self._current_workers + 1, self.max_workers)
                self._scale_up_count += 1
            elif avg_load < 30 and self._current_workers > self.min_workers:
                self._target_workers = max(self._current_workers - 1, self.min_workers)
                self._scale_down_count += 1
            stable = self._target_workers == self._current_workers
            return {
                "current": self._current_workers,
                "target": self._target_workers,
                "avg_load_pct": round(avg_load, 1),
                "stable": stable,
            }

    def apply(self) -> int:
        self._current_workers = self._target_workers
        return self._current_workers

    def get_stats(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "current": self._current_workers,
            "min": self.min_workers,
            "max": self.max_workers,
            "scale_ups": self._scale_up_count,
            "scale_downs": self._scale_down_count,
        }


class ConnectionOptimizer:
    def __init__(self, name: str, min_pool: int = 2, max_pool: int = 20):
        self.name = name
        self.min_pool = min_pool
        self.max_pool = max_pool
        self._current_pool: int = min_pool
        self._active_connections: int = 0
        self._peak_connections: int = 0
        self._reuse_count: int = 0
        self._lock = Lock()

    def record_connection(self) -> None:
        with self._lock:
            self._active_connections += 1
            self._peak_connections = max(self._peak_connections, self._active_connections)

    def record_release(self) -> None:
        with self._lock:
            self._active_connections = max(0, self._active_connections - 1)
            self._reuse_count += 1

    def optimize_pool_size(self, utilization_pct: float) -> int:
        if utilization_pct > 80 and self._current_pool < self.max_pool:
            self._current_pool = min(self._current_pool + 2, self.max_pool)
        elif utilization_pct < 20 and self._current_pool > self.min_pool:
            self._current_pool = max(self._current_pool - 2, self.min_pool)
        return self._current_pool

    def get_stats(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "pool_size": self._current_pool,
            "active": self._active_connections,
            "peak": self._peak_connections,
            "reuse_count": self._reuse_count,
            "pool_range": [self.min_pool, self.max_pool],
        }


class PerformanceOptimizer:
    def __init__(self, kernel: Kernel | None = None):
        self._kernel = kernel
        self._caches: dict[str, AdaptiveCache] = {}
        self._scalers: dict[str, DynamicScaler] = {}
        self._connection_optimizers: dict[str, ConnectionOptimizer] = {}
        self._optimization_count: int = 0
        self._last_optimization: float = 0.0
        self._optimization_interval: float = 60.0

    def create_cache(self, name: str, **kwargs: Any) -> AdaptiveCache:
        cache = AdaptiveCache(name=name, **kwargs)
        self._caches[name] = cache
        return cache

    def get_cache(self, name: str) -> AdaptiveCache | None:
        return self._caches.get(name)

    def create_scaler(
        self, name: str, min_workers: int = 1, max_workers: int = 10,
    ) -> DynamicScaler:
        scaler = DynamicScaler(name=name, min_workers=min_workers, max_workers=max_workers)
        self._scalers[name] = scaler
        return scaler

    def get_scaler(self, name: str) -> DynamicScaler | None:
        return self._scalers.get(name)

    def create_connection_optimizer(
        self, name: str, min_pool: int = 2, max_pool: int = 20,
    ) -> ConnectionOptimizer:
        opt = ConnectionOptimizer(name=name, min_pool=min_pool, max_pool=max_pool)
        self._connection_optimizers[name] = opt
        return opt

    def get_connection_optimizer(self, name: str) -> ConnectionOptimizer | None:
        return self._connection_optimizers.get(name)

    def optimize_all(self) -> dict[str, Any]:
        self._optimization_count += 1
        self._last_optimization = time.time()
        results: dict[str, Any] = {
            "caches": {},
            "scalers": {},
            "connections": {},
            "timestamp": time.time(),
        }
        for name, cache in self._caches.items():
            results["caches"][name] = cache.get_stats()
        for name, scaler in self._scalers.items():
            analysis = scaler.analyze()
            if not analysis["stable"]:
                scaler.apply()
            results["scalers"][name] = scaler.get_stats()
        for name, opt in self._connection_optimizers.items():
            results["connections"][name] = opt.get_stats()
        return results

    def get_stats(self) -> dict[str, Any]:
        return {
            "caches": {n: c.get_stats() for n, c in self._caches.items()},
            "scalers": {n: s.get_stats() for n, s in self._scalers.items()},
            "connections": {n: c.get_stats() for n, c in self._connection_optimizers.items()},
            "optimization_count": self._optimization_count,
            "last_optimization": self._last_optimization,
        }
