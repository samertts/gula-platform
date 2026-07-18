import logging
from typing import Any


class ServiceRegistry:
    def __init__(self):
        self._logger = logging.getLogger("gula.kernel.service_registry")
        self._services: dict[str, Any] = {}
        self._aliases: dict[str, str] = {}

    def register(self, name: str, service: Any, alias: str | None = None) -> None:
        if name in self._services:
            self._logger.warning("Service '%s' already registered, overwriting", name)
        self._services[name] = service
        if alias:
            self._aliases[alias] = name
        self._logger.debug("Service registered: %s%s", name, f" (alias: {alias})" if alias else "")

    def resolve(self, name: str) -> Any:
        resolved_name = self._aliases.get(name, name)
        service = self._services.get(resolved_name)
        if service is None:
            raise KeyError(f"Service '{name}' not found in registry")
        return service

    def get(self, name: str, default: Any = None) -> Any:
        try:
            return self.resolve(name)
        except KeyError:
            return default

    def unregister(self, name: str) -> bool:
        if name in self._services:
            del self._services[name]
            self._logger.debug("Service unregistered: %s", name)
            return True
        aliases_to_remove = [a for a, n in self._aliases.items() if n == name]
        for alias in aliases_to_remove:
            del self._aliases[alias]
        return False

    def has(self, name: str) -> bool:
        return name in self._services or name in self._aliases

    def list(self) -> list[str]:
        return list(self._services.keys())

    def clear(self) -> None:
        self._services.clear()
        self._aliases.clear()
        self._logger.debug("Service registry cleared")
