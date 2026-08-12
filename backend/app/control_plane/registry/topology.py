from __future__ import annotations

import logging
from typing import Any

from app.control_plane.registry.component import ComponentRegistry

logger = logging.getLogger("gula.control_plane.registry.topology")


class TopologyManager:
    def __init__(self, registry: ComponentRegistry):
        self._registry = registry

    def build_dependency_graph(self) -> dict[str, list[str]]:
        graph: dict[str, list[str]] = {}
        for comp in self._registry.list():
            graph[comp.name] = list(comp.dependencies)
        return graph

    def build_dependents_map(self) -> dict[str, list[str]]:
        dependents: dict[str, list[str]] = {}
        for comp in self._registry.list():
            dependents.setdefault(comp.name, [])
            for dep in comp.dependencies:
                dependents.setdefault(dep, []).append(comp.name)
        return dependents

    def detect_circular_dependencies(self) -> list[list[str]]:
        graph = self.build_dependency_graph()
        visited: set[str] = set()
        path: list[str] = []
        cycles: list[list[str]] = []

        def dfs(node: str) -> None:
            if node in path:
                cycle_start = path.index(node)
                cycle = [*path[cycle_start:], node]
                cycles.append(cycle)
                return
            if node in visited:
                return
            path.append(node)
            visited.add(node)
            for neighbour in graph.get(node, []):
                if neighbour in graph:
                    dfs(neighbour)
            path.pop()

        for node in list(graph.keys()):
            dfs(node)

        if cycles:
            logger.warning("Circular dependencies detected: %s", cycles)
        return cycles

    def validate(self) -> list[str]:
        errors: list[str] = []
        for comp in self._registry.list():
            for dep in comp.dependencies:
                if not self._registry.get(dep):
                    errors.append(f"Component '{comp.name}' depends on missing component '{dep}'")
        cycles = self.detect_circular_dependencies()
        for cycle in cycles:
            errors.append(f"Circular dependency cycle: {' -> '.join(cycle)}")
        return errors

    def get_topological_order(self) -> list[str]:
        graph = self.build_dependency_graph()
        visited: set[str] = set()
        order: list[str] = []

        def dfs(node: str) -> None:
            if node in visited:
                return
            visited.add(node)
            for neighbour in graph.get(node, []):
                dfs(neighbour)
            order.append(node)

        for node in list(graph.keys()):
            dfs(node)
        return order

    def component_level(self, name: str) -> int:
        graph = self.build_dependency_graph()
        depths: dict[str, int] = {}

        def compute_depth(node: str) -> int:
            if node in depths:
                return depths[node]
            if not graph.get(node):
                depths[node] = 0
                return 0
            max_dep = 0
            for dep in graph[node]:
                max_dep = max(max_dep, compute_depth(dep) + 1)
            depths[node] = max_dep
            return max_dep

        if name not in graph:
            return -1
        return compute_depth(name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph": self.build_dependency_graph(),
            "dependents": self.build_dependents_map(),
            "topological_order": self.get_topological_order(),
            "cycles": self.detect_circular_dependencies(),
        }
