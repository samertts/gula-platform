from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from fastapi.routing import APIRoute

logger = logging.getLogger("gula.knowledge_graph.api_catalog")


@dataclass
class EndpointEntry:
    method: str
    path: str
    summary: str
    description: str
    operation_id: str
    tags: list[str] = field(default_factory=list)
    parameters: list[dict] = field(default_factory=list)
    request_body: dict | None = None
    responses: dict = field(default_factory=dict)
    security: list[dict] | None = None
    deprecated: bool = False
    module: str = ""

    def to_dict(self) -> dict:
        return {
            "method": self.method,
            "path": self.path,
            "summary": self.summary,
            "description": self.description,
            "operation_id": self.operation_id,
            "tags": self.tags,
            "parameters": self.parameters,
            "request_body": self.request_body,
            "responses": self.responses,
            "security": self.security,
            "deprecated": self.deprecated,
            "module": self.module,
        }


@dataclass
class ApiGroupEntry:
    name: str
    prefix: str
    tags: list[str] = field(default_factory=list)
    endpoints: list[EndpointEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "prefix": self.prefix,
            "tags": self.tags,
            "endpoints": [e.to_dict() for e in self.endpoints],
        }


class APICatalog:
    def __init__(self):
        self._endpoints: dict[str, EndpointEntry] = {}
        self._groups: dict[str, ApiGroupEntry] = {}

    def discover_endpoints(self, app: Any = None) -> list[EndpointEntry]:
        if app is None:
            return list(self._endpoints.values())
        discovered: list[EndpointEntry] = []
        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue
            for method in route.methods:
                if method == "HEAD":
                    continue
                doc = route.endpoint.__doc__
                entry = EndpointEntry(
                    method=method.lower(),
                    path=route.path,
                    summary=route.summary or (doc.strip()[:80] if doc else ""),
                    description=doc.strip() if doc else (route.description or ""),
                    operation_id=route.name or f"{method.lower()}_{route.path.replace('/', '_')}",
                    tags=list(route.tags) if route.tags else [],
                    deprecated=getattr(route, "deprecated", False),
                    module=route.endpoint.__module__
                    if hasattr(route.endpoint, "__module__")
                    else "",
                )
                key = f"{entry.method}:{entry.path}"
                self._endpoints[key] = entry
                discovered.append(entry)
        logger.info("Discovered %d API endpoints", len(discovered))
        return discovered

    def discover_groups(self, app: Any = None) -> list[ApiGroupEntry]:
        if app is None:
            return list(self._groups.values())
        groups: dict[str, ApiGroupEntry] = {}
        for route in app.routes:
            if not isinstance(route, APIRoute):
                continue
            prefix = self._extract_prefix(route.path)
            tags = list(route.tags) if route.tags else [prefix.strip("/") or "default"]
            if prefix not in groups:
                groups[prefix] = ApiGroupEntry(
                    name=prefix.strip("/") or "root",
                    prefix=prefix,
                    tags=tags,
                )
            for method in route.methods:
                if method == "HEAD":
                    continue
                doc = route.endpoint.__doc__
                groups[prefix].endpoints.append(
                    EndpointEntry(
                        method=method.lower(),
                        path=route.path,
                        summary=route.summary or (doc.strip()[:80] if doc else ""),
                        description=doc.strip() if doc else "",
                        operation_id=route.name or "",
                        tags=list(route.tags) if route.tags else [],
                        deprecated=getattr(route, "deprecated", False),
                        module=route.endpoint.__module__
                        if hasattr(route.endpoint, "__module__")
                        else "",
                    ),
                )
        self._groups = groups
        return list(groups.values())

    def search_endpoints(self, query: str) -> list[EndpointEntry]:
        q = query.lower()
        results = []
        for entry in self._endpoints.values():
            if (
                q in entry.path.lower()
                or q in entry.method.lower()
                or q in entry.summary.lower()
                or q in entry.operation_id.lower()
                or any(q in t.lower() for t in entry.tags)
            ):
                results.append(entry)
        return results

    def get_endpoint(self, path: str, method: str | None = None) -> EndpointEntry | None:
        if method:
            return self._endpoints.get(f"{method.lower()}:{path}")
        for _key, entry in self._endpoints.items():
            if entry.path == path:
                return entry
        return None

    def get_all_endpoints(self) -> list[EndpointEntry]:
        return list(self._endpoints.values())

    def count(self) -> int:
        return len(self._endpoints)

    def get_summary(self) -> dict:
        methods: dict[str, int] = {}
        tags: dict[str, int] = {}
        for entry in self._endpoints.values():
            methods[entry.method.upper()] = methods.get(entry.method.upper(), 0) + 1
            for t in entry.tags:
                tags[t] = tags.get(t, 0) + 1
        return {
            "total_endpoints": self.count(),
            "by_method": dict(sorted(methods.items())),
            "by_tag": dict(sorted(tags.items(), key=lambda x: -x[1])),
        }

    def _extract_prefix(self, path: str) -> str:
        parts = path.strip("/").split("/")
        return f"/{parts[0]}" if parts else "/"


api_catalog = APICatalog()
