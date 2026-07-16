from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.integration.api_management.catalog")


@dataclass
class APIEndpoint:
    path: str = ""
    method: str = "GET"
    description: str = ""
    version: str = "1.0"
    tags: list[str] = field(default_factory=list)
    parameters: list[dict[str, Any]] = field(default_factory=list)
    security: list[str] = field(default_factory=list)
    rate_limit: int = 0
    active: bool = True


@dataclass
class APIService:
    id: str = ""
    name: str = ""
    version: str = "1.0.0"
    base_url: str = ""
    description: str = ""
    provider: str = ""
    endpoints: list[APIEndpoint] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    documentation_url: str = ""
    status: str = "active"
    health_check_url: str = ""


class APICatalog:
    def __init__(self):
        self._services: dict[str, APIService] = {}

    def register_service(self, service: APIService) -> None:
        self._services[service.id] = service
        logger.info("API service registered: %s (%s)", service.name, service.id)

    def unregister_service(self, service_id: str) -> bool:
        if service_id in self._services:
            del self._services[service_id]
            logger.info("API service unregistered: %s", service_id)
            return True
        return False

    def get_service(self, service_id: str) -> APIService | None:
        return self._services.get(service_id)

    def find_by_tag(self, tag: str) -> list[APIService]:
        return [s for s in self._services.values() if tag in s.tags]

    def find_by_name(self, name: str) -> APIService | None:
        for s in self._services.values():
            if s.name == name:
                return s
        return None

    def list_services(self) -> list[APIService]:
        return list(self._services.values())

    def list_active(self) -> list[APIService]:
        return [s for s in self._services.values() if s.status == "active"]

    def get_endpoint(self, service_id: str, path: str, method: str) -> APIEndpoint | None:
        service = self._services.get(service_id)
        if not service:
            return None
        for ep in service.endpoints:
            if ep.path == path and ep.method.upper() == method.upper():
                return ep
        return None

    def count(self) -> int:
        return len(self._services)
