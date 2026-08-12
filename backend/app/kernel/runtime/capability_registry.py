from __future__ import annotations

import json
import logging
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from app.kernel.types import CapabilityDescriptor, CapabilityStatus

logger = logging.getLogger("gula.kernel.capability_registry")


class CapabilityRegistry:
    def __init__(self, store_path: str | None = None):
        self._capabilities: dict[str, CapabilityDescriptor] = {}
        self._store_path = store_path
        self._dependency_graph: dict[str, set[str]] = {}

    def register(self, descriptor: CapabilityDescriptor) -> None:
        self._capabilities[descriptor.name] = descriptor
        self._rebuild_graph()
        logger.info(
            "Capability registered",
            extra={
                "capability": descriptor.name,
                "version": descriptor.version,
                "domain": descriptor.domain,
                "dependencies": len(descriptor.dependencies),
            },
        )

    def register_batch(self, descriptors: list[CapabilityDescriptor]) -> int:
        count = 0
        for d in descriptors:
            self._capabilities[d.name] = d
            count += 1
        self._rebuild_graph()
        logger.info("Batch registration complete", extra={"count": count})
        return count

    def has(self, name: str) -> bool:
        return name in self._capabilities

    def get(self, name: str) -> CapabilityDescriptor | None:
        return self._capabilities.get(name)

    def is_enabled(self, name: str) -> bool:
        cap = self._capabilities.get(name)
        return cap is not None and cap.enabled

    def enable(self, name: str) -> None:
        cap = self._capabilities.get(name)
        if cap:
            cap.enabled = True
            logger.info("Capability enabled", extra={"capability": name})

    def disable(self, name: str) -> None:
        cap = self._capabilities.get(name)
        if cap:
            cap.enabled = False
            logger.info("Capability disabled", extra={"capability": name})

    def set_status(self, name: str, status: CapabilityStatus) -> None:
        cap = self._capabilities.get(name)
        if cap:
            cap.status = status
            logger.info(
                "Capability status changed",
                extra={"capability": name, "status": status.value},
            )

    def list_capabilities(self) -> list[CapabilityDescriptor]:
        return list(self._capabilities.values())

    def list_enabled(self) -> list[CapabilityDescriptor]:
        return [c for c in self._capabilities.values() if c.enabled]

    def list_by_domain(self, domain: str) -> list[CapabilityDescriptor]:
        return [c for c in self._capabilities.values() if c.domain == domain]

    def list_by_status(self, status: CapabilityStatus) -> list[CapabilityDescriptor]:
        return [c for c in self._capabilities.values() if c.status == status]

    def check_dependencies(self, name: str) -> bool:
        cap = self._capabilities.get(name)
        if not cap:
            return False
        return all(dep in self._capabilities for dep in cap.dependencies)

    def get_unresolved_dependencies(self, name: str) -> list[str]:
        cap = self._capabilities.get(name)
        if not cap:
            return [name]
        return [dep for dep in cap.dependencies if dep not in self._capabilities]

    def get_dependents(self, name: str) -> list[str]:
        dependents = []
        for cap_name, cap in self._capabilities.items():
            if name in cap.dependencies:
                dependents.append(cap_name)
        return dependents

    def topological_sort(self) -> list[str]:
        in_degree: dict[str, int] = defaultdict(int)
        adj: dict[str, list[str]] = defaultdict(list)
        for cap_name, cap in self._capabilities.items():
            if cap_name not in in_degree:
                in_degree[cap_name] = 0
            for dep in cap.dependencies:
                adj.setdefault(dep, []).append(cap_name)
                in_degree[cap_name] += 1

        queue = deque([name for name, deg in in_degree.items() if deg == 0])
        sorted_list = []
        while queue:
            node = queue.popleft()
            sorted_list.append(node)
            for neighbor in adj.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        remaining = [name for name, deg in in_degree.items() if deg > 0]
        if remaining:
            logger.warning(
                "Circular dependencies detected",
                extra={"circular": remaining},
            )
        return sorted_list

    def impact_analysis(self, name: str) -> dict[str, Any]:
        result: dict[str, Any] = {
            "target": name,
            "direct_dependents": [],
            "transitive_dependents": [],
            "all_affected": set(),
            "found": name in self._capabilities,
        }
        if not result["found"]:
            return result

        cap = self._capabilities[name]
        result["dependencies"] = cap.dependencies
        result["unresolved"] = self.get_unresolved_dependencies(name)
        result["domain"] = cap.domain

        visited: set[str] = set()
        queue = deque([name])
        while queue:
            current = queue.popleft()
            for dep_name in self.get_dependents(current):
                if dep_name not in visited:
                    visited.add(dep_name)
                    queue.append(dep_name)

        result["direct_dependents"] = self.get_dependents(name)
        result["transitive_dependents"] = list(visited - set(self.get_dependents(name)))
        result["all_affected"] = list(visited)
        return result

    def get_dependency_graph(self) -> dict[str, list[str]]:
        graph = {}
        for cap_name, cap in self._capabilities.items():
            graph[cap_name] = list(cap.dependencies)
        return graph

    def count(self) -> int:
        return len(self._capabilities)

    def get_summary(self) -> dict[str, Any]:
        domains: dict[str, int] = {}
        statuses: dict[str, int] = {}
        total_deps = 0
        enabled_count = 0
        for cap in self._capabilities.values():
            domains[cap.domain] = domains.get(cap.domain, 0) + 1
            statuses[cap.status.value] = statuses.get(cap.status.value, 0) + 1
            total_deps += len(cap.dependencies)
            if cap.enabled:
                enabled_count += 1
        return {
            "total": self.count(),
            "enabled": enabled_count,
            "domains": domains,
            "statuses": statuses,
            "total_dependencies": total_deps,
            "boot_order": self.topological_sort(),
        }

    def save(self, path: str | None = None) -> None:
        store = path or self._store_path
        if not store:
            return
        data = []
        for cap in self._capabilities.values():
            data.append({
                "capability_id": cap.capability_id,
                "name": cap.name,
                "version": cap.version,
                "description": cap.description,
                "owner": cap.owner,
                "status": cap.status.value,
                "domain": cap.domain,
                "layer": cap.layer,
                "dependencies": cap.dependencies,
                "enabled": cap.enabled,
                "required": cap.required,
                "tags": cap.tags,
            })
        Path(store).parent.mkdir(parents=True, exist_ok=True)
        Path(store).write_text(json.dumps(data, indent=2))
        logger.info("Capability registry saved", extra={"path": store, "count": len(data)})

    def load(self, path: str | None = None) -> int:
        store = path or self._store_path
        if not store or not Path(store).exists():
            return 0
        data = json.loads(Path(store).read_text())
        count = 0
        for item in data:
            desc = CapabilityDescriptor(
                capability_id=item.get("capability_id", ""),
                name=item["name"],
                version=item["version"],
                description=item.get("description", ""),
                owner=item.get("owner", "platform-team"),
                status=CapabilityStatus(item.get("status", "active")),
                domain=item.get("domain", "core"),
                layer=item.get("layer", "application"),
                dependencies=item.get("dependencies", []),
                enabled=item.get("enabled", True),
                required=item.get("required", False),
                tags=item.get("tags", []),
            )
            self._capabilities[desc.name] = desc
            count += 1
        self._rebuild_graph()
        logger.info("Capability registry loaded", extra={"path": store, "count": count})
        return count

    def _rebuild_graph(self) -> None:
        self._dependency_graph = {
            name: set(cap.dependencies) for name, cap in self._capabilities.items()
        }
