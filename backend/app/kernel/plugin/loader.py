from __future__ import annotations

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from backend.app.kernel.exceptions import PluginLoadError
from backend.app.kernel.types import PluginDescriptor

if TYPE_CHECKING:
    from backend.app.kernel import Kernel

logger = logging.getLogger("gula.kernel.plugin.loader")


class PluginLoader:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel

    async def load(self, path: str) -> PluginDescriptor:
        plugin_path = Path(path)
        if not plugin_path.exists():
            raise PluginLoadError(path, "Plugin path does not exist")

        spec = importlib.util.spec_from_file_location(plugin_path.stem, plugin_path / "__init__.py")
        if not spec or not spec.loader:
            raise PluginLoadError(path, "Cannot load plugin module")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "Plugin"):
            raise PluginLoadError(path, "Plugin class not found")

        plugin_class = module.Plugin
        instance = plugin_class()
        return PluginDescriptor(
            name=getattr(instance, "name", plugin_path.stem),
            version=getattr(instance, "version", "1.0.0"),
            path=str(plugin_path),
            entry_point="Plugin",
            dependencies=getattr(instance, "dependencies", []),
            permissions=getattr(instance, "permissions", []),
            enabled=True,
        )
