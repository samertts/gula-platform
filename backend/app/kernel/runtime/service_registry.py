from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Type

from backend.app.kernel.exceptions import ServiceAlreadyRegisteredError, ServiceNotFoundError

logger = logging.getLogger("gula.kernel.service_registry")


class ServiceRegistry:
    def __init__(self):
        self._services: dict[str, Any] = {}
        self._singletons: dict[str, Any] = {}
        self._metadata: dict[str, dict] = {}

    def register(
        self,
        name: str,
        instance: Any,
        singleton: bool = True,
        metadata: dict | None = None,
    ) -> None:
        if name in self._services:
            raise ServiceAlreadyRegisteredError(name)
        self._services[name] = instance
        self._metadata[name] = metadata or {}

    def get(self, name: str) -> Any | None:
        return self._services.get(name)

    def get_required(self, name: str) -> Any:
        service = self._services.get(name)
        if service is None:
            raise ServiceNotFoundError(name)
        return service

    def has(self, name: str) -> bool:
        return name in self._services

    def unregister(self, name: str) -> None:
        self._services.pop(name, None)
        self._metadata.pop(name, None)

    def list_services(self) -> list[str]:
        return list(self._services.keys())

    def get_metadata(self, name: str) -> dict | None:
        return self._metadata.get(name)
