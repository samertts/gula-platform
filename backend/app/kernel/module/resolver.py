from __future__ import annotations

import logging

from app.kernel.types import ModuleDescriptor

logger = logging.getLogger("gula.kernel.module.resolver")


class ModuleDependencyResolver:
    def validate(self, descriptor: ModuleDescriptor, existing: list[ModuleDescriptor]) -> None:
        existing_names = {m.name: m.version for m in existing}
        for dep_name, _dep_version in descriptor.dependencies.items():
            if dep_name not in existing_names:
                raise ValueError(
                    f"Module '{descriptor.name}' requires '{dep_name}' which is not loaded"
                )

    def resolve_order(self, modules: list[ModuleDescriptor]) -> list[ModuleDescriptor]:
        graph: dict[str, set[str]] = {}
        for m in modules:
            graph[m.name] = set(m.dependencies.keys())

        visited: set[str] = set()
        result: list[ModuleDescriptor] = []
        module_map = {m.name: m for m in modules}

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
            if name in module_map:
                result.append(module_map[name])

        for name in graph:
            if name not in visited:
                visit(name, set())

        return result
