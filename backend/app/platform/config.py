"""Standardized configuration module — registry pattern for module configurations."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any

from . import PlatformRegistry

logger = logging.getLogger("gula.platform.config")


class ConfigService:
    _watchers: dict[str, list[Callable]] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return os.getenv(key, default)

    def set(self, key: str, value: str) -> None:
        os.environ[key] = value
        watchers = self._watchers.get(key, [])
        for cb in watchers:
            try:
                cb(key, value)
            except Exception:
                logger.warning("[CONFIG] Watcher failed for key=%s", key, exc_info=True)

    def get_all(self) -> dict[str, str]:
        return dict(os.environ)

    def watch(self, key: str, callback: Callable) -> None:
        self._watchers.setdefault(key, []).append(callback)


PlatformRegistry.register(
    "config",
    ConfigService(),
    capabilities=[
        {"name": "get", "description": "Get a configuration value by key"},
        {"name": "set", "description": "Set a configuration value"},
        {"name": "get_all", "description": "Get all configuration values"},
        {"name": "watch", "description": "Register a callback for config changes"},
    ],
)
