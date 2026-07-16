"""Standardized caching service — wraps core/cache_manager.py."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from ..core.cache_manager import cache_manager
from . import PlatformRegistry

logger = logging.getLogger("gula.platform.caching")


class PlatformCacheService:
    async def get(self, key: str, loader: Callable[[], Awaitable[Any]] | None = None, ttl: int | None = None) -> Any | None:
        return await cache_manager.get(key, loader=loader, ttl=ttl)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        await cache_manager.set(key, value, ttl=ttl)

    async def delete(self, key: str) -> None:
        await cache_manager.delete(key)

    async def invalidate_pattern(self, pattern: str) -> int:
        return await cache_manager.invalidate(pattern)

    async def warmup(self, keys: list[str], loader) -> int:
        return await cache_manager.warm(keys, loader)


PlatformRegistry.register("caching", PlatformCacheService(), capabilities=[
    {"name": "get", "description": "Retrieve a value from the multi-level cache"},
    {"name": "set", "description": "Store a value in the cache"},
    {"name": "delete", "description": "Evict a single key from the cache"},
    {"name": "invalidate_pattern", "description": "Evict all keys matching a prefix pattern"},
    {"name": "warmup", "description": "Pre-populate the cache with eagerly loaded keys"},
])
