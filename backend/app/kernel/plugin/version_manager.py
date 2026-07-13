from __future__ import annotations

import logging

from backend.app.kernel.types import PluginDescriptor

logger = logging.getLogger("gula.kernel.plugin.version")


class PluginVersionManager:
    def __init__(self):
        self._version_map: dict[str, str] = {}

    def validate(self, descriptor: PluginDescriptor) -> None:
        existing = self._version_map.get(descriptor.name)
        if existing and existing != descriptor.version:
            logger.warning(
                "Plugin version mismatch",
                extra={
                    "plugin": descriptor.name,
                    "existing": existing,
                    "new": descriptor.version,
                },
            )

    def register(self, descriptor: PluginDescriptor) -> None:
        self._version_map[descriptor.name] = descriptor.version

    def get_version(self, name: str) -> str | None:
        return self._version_map.get(name)
