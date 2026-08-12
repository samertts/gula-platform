from __future__ import annotations

import logging

from app.kernel.types import PluginDescriptor

logger = logging.getLogger("gula.kernel.plugin.dependencies")


class PluginDependencyResolver:
    def __init__(self):
        self._resolved: set[str] = set()

    def validate(self, descriptor: PluginDescriptor, existing: list[PluginDescriptor]) -> None:
        existing_names = {p.name for p in existing}
        for dep in descriptor.dependencies:
            if dep not in existing_names:
                raise ValueError(f"Plugin '{descriptor.name}' requires '{dep}' which is not loaded")

    def resolve_order(self, plugins: list[PluginDescriptor]) -> list[PluginDescriptor]:
        graph: dict[str, set[str]] = {}
        for p in plugins:
            graph[p.name] = set(p.dependencies)

        visited: set[str] = set()
        result: list[PluginDescriptor] = []
        plugin_map = {p.name: p for p in plugins}

        def visit(name: str, path: set[str]) -> None:
            if name in path:
                raise ValueError(f"Circular dependency: {name}")
            if name in visited:
                return
            path.add(name)
            for dep in graph.get(name, set()):
                visit(dep, path)
            path.remove(name)
            visited.add(name)
            if name in plugin_map:
                result.append(plugin_map[name])

        for name in graph:
            if name not in visited:
                visit(name, set())

        return result
