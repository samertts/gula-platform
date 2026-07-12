from __future__ import annotations

import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger("gula.cache")


class CacheBackend(ABC):
    @abstractmethod
    def get(self, key: str) -> Any:
        ...

    @abstractmethod
    def set(self, key: str, value: Any, ex: int | None = None) -> None:
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        ...

    @abstractmethod
    def ping(self) -> bool:
        ...

    @abstractmethod
    def close(self) -> None:
        ...


class MemoryBackend(CacheBackend):
    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float | None]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any:
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            value, expiry = item
            if expiry is not None and time.time() > expiry:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ex: int | None = None) -> None:
        expiry = time.time() + ex if ex else None
        with self._lock:
            self._store[key] = (value, expiry)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def ping(self) -> bool:
        return True

    def close(self) -> None:
        with self._lock:
            self._store.clear()


class RedisBackend(CacheBackend):
    def __init__(self, redis_url: str) -> None:
        import redis.asyncio as aioredis
        self._client = aioredis.from_url(redis_url, decode_responses=True)
        self._sync_client = None

    def _sync(self):
        if self._sync_client is None:
            import redis
            self._sync_client = redis.from_url(self._client.connection_pool.connection_kwargs.get("url", ""))
        return self._sync_client

    def get(self, key: str) -> Any:
        try:
            val = self._sync().get(key)
            return val
        except Exception as exc:
            logger.warning("Redis get failed: %s", exc)
            return None

    def set(self, key: str, value: Any, ex: int | None = None) -> None:
        try:
            self._sync().set(key, value, ex=ex)
        except Exception as exc:
            logger.warning("Redis set failed: %s", exc)

    def delete(self, key: str) -> None:
        try:
            self._sync().delete(key)
        except Exception as exc:
            logger.warning("Redis delete failed: %s", exc)

    def ping(self) -> bool:
        try:
            return self._sync().ping()
        except Exception:
            return False

    def close(self) -> None:
        try:
            self._sync().close()
        except Exception:
            pass


_cache_instance: CacheBackend | None = None
_cache_lock = threading.Lock()


def get_cache(redis_url: str | None = None) -> CacheBackend:
    global _cache_instance
    if _cache_instance is not None:
        return _cache_instance
    with _cache_lock:
        if _cache_instance is not None:
            return _cache_instance
        if redis_url:
            _cache_instance = RedisBackend(redis_url)
        else:
            _cache_instance = MemoryBackend()
    return _cache_instance
