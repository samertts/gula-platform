from __future__ import annotations

import asyncio
import functools
import hashlib
import json
import logging
import time
import weakref
from collections import OrderedDict
from typing import Any, Callable

logger = logging.getLogger(__name__)


class LRUCache:
    def __init__(self, maxsize: int = 1000, ttl_seconds: float = 300.0):
        self._maxsize = maxsize
        self._ttl = ttl_seconds
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()

    def get(self, key: str) -> Any | None:
        if key not in self._cache:
            return None
        value, expiry = self._cache[key]
        if time.time() > expiry:
            self._cache.pop(key)
            return None
        self._cache.move_to_end(key)
        return value

    def set(self, key: str, value: Any, ttl: float | None = None):
        expiry = time.time() + (ttl or self._ttl)
        self._cache[key] = (value, expiry)
        self._cache.move_to_end(key)
        while len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

    def delete(self, key: str):
        self._cache.pop(key, None)

    def clear(self):
        self._cache.clear()

    def contains(self, key: str) -> bool:
        return self.get(key) is not None

    def size(self) -> int:
        self._evict_expired()
        return len(self._cache)

    def _evict_expired(self):
        now = time.time()
        expired = [k for k, (_, t) in self._cache.items() if now > t]
        for k in expired:
            self._cache.pop(k, None)

    def keys(self) -> list[str]:
        self._evict_expired()
        return list(self._cache.keys())


class AsyncMemoizer:
    def __init__(self, maxsize: int = 500, ttl: float = 60.0):
        self._cache = LRUCache(maxsize=maxsize, ttl_seconds=ttl)

    def memoize(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            key_parts = [func.__name__]
            key_parts.extend(str(a) for a in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            key = hashlib.md5("".join(key_parts).encode()).hexdigest()
            cached = self._cache.get(key)
            if cached is not None:
                return cached
            result = await func(*args, **kwargs)
            self._cache.set(key, result)
            return result
        return wrapper

    def invalidate(self, func: Callable | None = None):
        if func:
            prefix = func.__name__
            for key in self._cache.keys():
                if key.startswith(hashlib.md5(prefix.encode()).hexdigest()):
                    self._cache.delete(key)
        else:
            self._cache.clear()


class ConnectionPool:
    def __init__(self, min_size: int = 2, max_size: int = 20, factory: Callable | None = None):
        self._min = min_size
        self._max = max_size
        self._factory = factory
        self._available: list[Any] = []
        self._in_use_ids: set[int] = set()
        self._lock = asyncio.Lock()

    async def acquire(self) -> Any:
        async with self._lock:
            while self._available:
                conn = self._available.pop()
                if self._is_valid(conn):
                    self._in_use_ids.add(id(conn))
                    return conn
            if self.size < self._max:
                conn = await self._create_connection()
                self._in_use_ids.add(id(conn))
                return conn
            raise RuntimeError("Connection pool exhausted")

    async def release(self, conn: Any):
        async with self._lock:
            self._in_use_ids.discard(id(conn))
            if self._is_valid(conn):
                self._available.append(conn)

    async def _create_connection(self) -> Any:
        if self._factory:
            result = self._factory()
            if asyncio.iscoroutine(result):
                return await result
            return result
        return {"id": id(self), "created_at": time.time()}

    def _is_valid(self, conn: Any) -> bool:
        return conn is not None

    @property
    def size(self) -> int:
        return len(self._available) + len(self._in_use_ids)

    @property
    def available_count(self) -> int:
        return len(self._available)

    @property
    def in_use_count(self) -> int:
        return len(self._in_use_ids)


class BatchAggregator:
    def __init__(self, max_batch_size: int = 100, flush_interval: float = 0.5):
        self._max_batch = max_batch_size
        self._interval = flush_interval
        self._queue: asyncio.Queue = asyncio.Queue()
        self._handlers: dict[str, Callable] = {}
        self._running = False
        self._task: asyncio.Task | None = None

    def register_handler(self, event_type: str, handler: Callable):
        self._handlers[event_type] = handler

    async def add(self, event_type: str, item: Any):
        await self._queue.put((event_type, item))

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._flush_loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._flush()

    async def _flush_loop(self):
        while self._running:
            await asyncio.sleep(self._interval)
            await self._flush()

    async def _flush(self):
        batches: dict[str, list[Any]] = {}
        while not self._queue.empty() and sum(len(b) for b in batches.values()) < self._max_batch:
            try:
                event_type, item = self._queue.get_nowait()
                if event_type not in batches:
                    batches[event_type] = []
                batches[event_type].append(item)
            except asyncio.QueueEmpty:
                break
        for event_type, items in batches.items():
            handler = self._handlers.get(event_type)
            if handler:
                try:
                    await handler(items)
                except Exception as e:
                    logger.exception("Batch handler failed for %s: %s", event_type, e)


class ProcessingTimeTracker:
    def __init__(self):
        self._timings: dict[str, list[float]] = {}

    def __enter__(self):
        self._start = time.time()
        return self

    def __exit__(self, *args: Any):
        elapsed = (time.time() - self._start) * 1000
        if self._operation not in self._timings:
            self._timings[self._operation] = []
        self._timings[self._operation].append(elapsed)

    async def track(self, operation: str, func: Callable, *args: Any, **kwargs: Any) -> Any:
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            elapsed = (time.time() - start) * 1000
            if operation not in self._timings:
                self._timings[operation] = []
            self._timings[operation].append(elapsed)

    def set_operation(self, operation: str):
        self._operation = operation

    def get_stats(self, operation: str | None = None) -> dict[str, Any]:
        target = {operation: self._timings.get(operation, [])} if operation else self._timings
        stats = {}
        for op, timings in target.items():
            if timings:
                sorted_t = sorted(timings)
                n = len(sorted_t)
                stats[op] = {
                    "count": n,
                    "min_ms": sorted_t[0],
                    "max_ms": sorted_t[-1],
                    "avg_ms": sum(sorted_t) / n,
                    "p50_ms": sorted_t[n // 2],
                    "p95_ms": sorted_t[int(n * 0.95)],
                    "p99_ms": sorted_t[int(n * 0.99)],
                    "total_ms": sum(sorted_t),
                }
        return stats

    def reset(self, operation: str | None = None):
        if operation:
            self._timings.pop(operation, None)
        else:
            self._timings.clear()
