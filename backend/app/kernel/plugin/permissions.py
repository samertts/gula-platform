from __future__ import annotations

import logging

from app.kernel.exceptions import PluginPermissionDenied
from app.kernel.types import PluginDescriptor

logger = logging.getLogger("gula.kernel.plugin.permissions")


class PluginPermissionManager:
    def __init__(self):
        self._available_permissions: set[str] = {
            "kernel.read",
            "kernel.write",
            "config.read",
            "config.write",
            "event.publish",
            "event.subscribe",
            "db.read",
            "db.write",
            "network.connect",
            "filesystem.read",
            "filesystem.write",
        }
        self._granted: dict[str, set[str]] = {}

    def check(self, descriptor: PluginDescriptor) -> None:
        for perm in descriptor.permissions:
            if perm not in self._available_permissions:
                raise PluginPermissionDenied(descriptor.name, perm)
        self._granted[descriptor.name] = set(descriptor.permissions)

    def has_permission(self, plugin_name: str, permission: str) -> bool:
        return permission in self._granted.get(plugin_name, set())
