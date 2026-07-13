from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.kernel import Kernel
    from backend.app.kernel.plugin.manager import PluginManager

logger = logging.getLogger("gula.kernel.plugin.hot_reload")


class HotPluginReloader:
    def __init__(self, kernel: Kernel, manager: PluginManager):
        self.kernel = kernel
        self.manager = manager
        self._watchers: dict[str, float] = {}
        self._running = False

    async def watch(self, plugin_name: str, path: str) -> None:
        self._watchers[plugin_name] = 0.0

    async def unwatch(self, plugin_name: str) -> None:
        self._watchers.pop(plugin_name, None)

    async def reload(self, plugin_name: str) -> None:
        plugin = self.manager.get_plugin(plugin_name)
        if not plugin:
            return
        await self.manager.unload_plugin(plugin_name)
        await self.manager.load_plugin(plugin.path)
