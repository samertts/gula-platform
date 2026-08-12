from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.knowledge_graph.service_catalog")


@dataclass
class CapabilityEntry:
    name: str
    version: str
    description: str
    domain: str
    layer: str
    status: str
    enabled: bool
    required: bool
    dependencies: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    api_endpoints: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    entities: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "domain": self.domain,
            "layer": self.layer,
            "status": self.status,
            "enabled": self.enabled,
            "required": self.required,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "api_endpoints": self.api_endpoints,
            "events": self.events,
            "entities": self.entities,
        }


@dataclass
class ServiceEntry:
    name: str
    version: str = "1.0.0"
    status: str = "active"
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    apis: list[str] = field(default_factory=list)
    events_published: list[str] = field(default_factory=list)
    events_subscribed: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "description": self.description,
            "dependencies": self.dependencies,
            "apis": self.apis,
            "events_published": self.events_published,
            "events_subscribed": self.events_subscribed,
            "tags": self.tags,
        }


class ServiceCatalog:
    def __init__(self):
        self._services: dict[str, ServiceEntry] = {}
        self._capabilities: dict[str, CapabilityEntry] = {}

    def discover_services(self, kernel: Any = None) -> list[ServiceEntry]:
        if kernel is None:
            return list(self._services.values())
        try:
            sr = kernel.get_component("service_registry")
            if sr is None:
                logger.warning("ServiceRegistry not found in kernel components")
                return list(self._services.values())
            names = sr.list_services()
            for name in names:
                meta = sr.get_metadata(name) or {}
                self._services[name] = ServiceEntry(
                    name=name,
                    version=meta.get("version", "1.0.0"),
                    status=meta.get("status", "active"),
                    description=meta.get("description", ""),
                    dependencies=meta.get("dependencies", []),
                    apis=meta.get("apis", []),
                    tags=meta.get("tags", []),
                )
            logger.info("Discovered %d services from kernel", len(self._services))
        except Exception as exc:
            logger.warning("Failed to discover services from kernel: %s", exc)
        return list(self._services.values())

    def discover_capabilities(self, kernel: Any = None) -> list[CapabilityEntry]:
        if kernel is None:
            return list(self._capabilities.values())
        try:
            cr = kernel.get_component("capability_registry")
            if cr is None:
                logger.warning("CapabilityRegistry not found in kernel components")
                return list(self._capabilities.values())
            descriptors = cr.list_capabilities()
            for desc in descriptors:
                self._capabilities[desc.name] = CapabilityEntry(
                    name=desc.name,
                    version=desc.version,
                    description=desc.description,
                    domain=desc.domain,
                    layer=desc.layer,
                    status=desc.status.value if hasattr(desc.status, "value") else str(desc.status),
                    enabled=desc.enabled,
                    required=desc.required,
                    dependencies=list(desc.dependencies),
                    tags=list(desc.tags),
                    api_endpoints=[e.__dict__ if hasattr(e, "__dict__") else {"path": e.path, "method": e.method} for e in getattr(desc, "api_endpoints", [])],
                    events=[e.__dict__ if hasattr(e, "__dict__") else {"name": e.name} for e in getattr(desc, "events", [])],
                    entities=[e.__dict__ if hasattr(e, "__dict__") else {"name": e.name} for e in getattr(desc, "entities", [])],
                )
            logger.info("Discovered %d capabilities from kernel", len(self._capabilities))
        except Exception as exc:
            logger.warning("Failed to discover capabilities from kernel: %s", exc)
        return list(self._capabilities.values())

    def get_dependency_graph(self) -> dict[str, list[str]]:
        graph: dict[str, list[str]] = {}
        for name, svc in self._services.items():
            graph[name] = list(svc.dependencies)
        for name, cap in self._capabilities.items():
            graph[f"capability:{name}"] = list(cap.dependencies)
        try:
            from app.kernel.integration import get_kernel
            kernel = get_kernel()
            cr = kernel.get_component("capability_registry")
            if cr and hasattr(cr, "get_dependency_graph"):
                cap_graph = cr.get_dependency_graph()
                for k, v in cap_graph.items():
                    graph[f"capability:{k}"] = v
        except Exception:
            pass
        return graph

    def get_service(self, name: str) -> ServiceEntry | None:
        return self._services.get(name)

    def get_capability(self, name: str) -> CapabilityEntry | None:
        return self._capabilities.get(name)

    def search(self, query: str) -> list[ServiceEntry | CapabilityEntry]:
        q = query.lower()
        results: list[ServiceEntry | CapabilityEntry] = []
        for s in self._services.values():
            if q in s.name.lower() or q in s.description.lower():
                results.append(s)
        for c in self._capabilities.values():
            if q in c.name.lower() or q in c.description.lower() or q in c.domain.lower():
                results.append(c)
        return results

    def get_summary(self) -> dict:
        return {
            "total_services": len(self._services),
            "total_capabilities": len(self._capabilities),
            "services": [s.name for s in self._services.values()],
            "capabilities": [c.name for c in self._capabilities.values()],
        }


service_catalog = ServiceCatalog()
