from __future__ import annotations

import logging
from typing import Dict, List, Optional

from backend.app.kernel.types import PluginDescriptor

logger = logging.getLogger("gula.kernel.plugin.registry")


class PluginRegistry:
    def __init__(self):
        self._plugins: dict[str, PluginDescriptor] = {}

    def register(self, descriptor: PluginDescriptor) -> None:
        self._plugins[descriptor.name] = descriptor
        logger.info(
            "Plugin registered",
            extra={"plugin": descriptor.name, "version": descriptor.version},
        )

    def unregister(self, name: str) -> None:
        self._plugins.pop(name, None)

    def get(self, name: str) -> PluginDescriptor | None:
        return self._plugins.get(name)

    def has(self, name: str) -> bool:
        return name in self._plugins

    def list_plugins(self) -> list[PluginDescriptor]:
        return list(self._plugins.values())

    def list_enabled(self) -> list[PluginDescriptor]:
        return [p for p in self._plugins.values() if p.enabled]
