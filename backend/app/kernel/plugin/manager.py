from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.app.kernel.plugin.dependencies import PluginDependencyResolver
from backend.app.kernel.plugin.hot_reload import HotPluginReloader
from backend.app.kernel.plugin.loader import PluginLoader
from backend.app.kernel.plugin.marketplace import PluginMarketplaceInterface
from backend.app.kernel.plugin.permissions import PluginPermissionManager
from backend.app.kernel.plugin.registry import PluginRegistry
from backend.app.kernel.plugin.sandbox import PluginSandbox
from backend.app.kernel.plugin.version_manager import PluginVersionManager
from backend.app.kernel.types import PluginDescriptor

if TYPE_CHECKING:
    from backend.app.kernel import Kernel

logger = logging.getLogger("gula.kernel.plugin.manager")


class PluginManager:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.registry = PluginRegistry()
        self.loader = PluginLoader(kernel)
        self.sandbox = PluginSandbox()
        self.permissions = PluginPermissionManager()
        self.dependency_resolver = PluginDependencyResolver()
        self.version_manager = PluginVersionManager()
        self.hot_reloader = HotPluginReloader(kernel, self)
        self.marketplace = PluginMarketplaceInterface()

    async def load_plugin(self, path: str) -> PluginDescriptor:
        descriptor = await self.loader.load(path)
        self.dependency_resolver.validate(descriptor, self.registry.list_plugins())
        self.permissions.check(descriptor)
        self.version_manager.validate(descriptor)
        self.registry.register(descriptor)
        return descriptor

    async def unload_plugin(self, name: str) -> None:
        self.registry.unregister(name)

    async def enable_plugin(self, name: str) -> None:
        plugin = self.registry.get(name)
        if plugin:
            plugin.enabled = True

    async def disable_plugin(self, name: str) -> None:
        plugin = self.registry.get(name)
        if plugin:
            plugin.enabled = False

    def list_plugins(self) -> list[PluginDescriptor]:
        return self.registry.list_plugins()

    def get_plugin(self, name: str) -> PluginDescriptor | None:
        return self.registry.get(name)
