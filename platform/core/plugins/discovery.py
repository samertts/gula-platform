import importlib
import importlib.util
import logging
import os
from typing import Any

from platform.core.plugins.registry import PluginRegistry
from platform.core.plugins.sandbox import PluginSandbox


def discover_plugins(search_paths: list[str]) -> dict[str, Any]:
    plugins = {}
    for search_path in search_paths:
        if not os.path.isdir(search_path):
            continue
        for entry in sorted(os.listdir(search_path)):
            plugin_dir = os.path.join(search_path, entry)
            if not os.path.isdir(plugin_dir):
                continue
            manifest_path = os.path.join(plugin_dir, "plugin.json")
            if not os.path.exists(manifest_path):
                continue
            plugins[entry] = {"path": plugin_dir, "manifest_path": manifest_path}
        for entry in sorted(os.listdir(search_path)):
            if entry.endswith(".py") and not entry.startswith("_"):
                plugin_path = os.path.join(search_path, entry)
                module_name = entry[:-3]
                plugins[module_name] = {"path": plugin_path, "manifest_path": None}
    return plugins


class PluginDiscovery:
    def __init__(self):
        self._logger = logging.getLogger("gula.plugins.discovery")

    def discover(self, search_paths: list[str]) -> dict[str, Any]:
        return discover_plugins(search_paths)

    def load_plugin(self, plugin_path: str, module_name: str) -> Any:
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load plugin from {plugin_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self._logger.info("Plugin loaded: %s (%s)", module_name, plugin_path)
        return module

    def validate_manifest(self, manifest_path: str) -> bool:
        import json
        try:
            with open(manifest_path) as f:
                data = json.load(f)
            return "name" in data and "version" in data
        except Exception:
            return False
