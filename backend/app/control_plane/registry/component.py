from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.control_plane.enums import ComponentStatus, PlatformComponent
from app.kernel.integration import get_kernel

logger = logging.getLogger("gula.control_plane.registry.component")


@dataclass
class ComponentDescriptor:
    name: str
    component_type: PlatformComponent
    version: str = "1.0.0"
    status: ComponentStatus = ComponentStatus.REGISTERED
    description: str = ""
    owner: str = ""
    dependencies: list[str] = field(default_factory=list)
    health_endpoint: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    registered_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class ComponentRegistry:
    _instance: ComponentRegistry | None = None

    def __init__(self):
        if ComponentRegistry._instance is not None:
            raise RuntimeError("ComponentRegistry is a singleton. Use get_instance().")
        self._components: dict[str, ComponentDescriptor] = {}
        self._kernel_registry = None
        ComponentRegistry._instance = self

    @classmethod
    def get_instance(cls) -> ComponentRegistry:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None

    def _get_kernel_service_registry(self):
        if self._kernel_registry is None:
            kernel = get_kernel()
            self._kernel_registry = kernel.get_component("service_registry")
        return self._kernel_registry

    def register(self, descriptor: ComponentDescriptor) -> None:
        self._components[descriptor.name] = descriptor
        sr = self._get_kernel_service_registry()
        if sr and not sr.has(descriptor.name):
            sr.register(
                descriptor.name,
                descriptor,
                singleton=True,
                metadata={
                    "type": descriptor.component_type.value,
                    "version": descriptor.version,
                    "status": descriptor.status.value,
                },
            )
        logger.info(
            "Component registered: %s (%s v%s)",
            descriptor.name,
            descriptor.component_type.value,
            descriptor.version,
        )

    def unregister(self, name: str) -> None:
        self._components.pop(name, None)
        sr = self._get_kernel_service_registry()
        if sr:
            sr.unregister(name)
        logger.info("Component unregistered: %s", name)

    def get(self, name: str) -> ComponentDescriptor | None:
        return self._components.get(name)

    def get_required(self, name: str) -> ComponentDescriptor:
        comp = self._components.get(name)
        if comp is None:
            raise KeyError(f"Component not found: {name}")
        return comp

    def list(self, component_type: PlatformComponent | None = None) -> list[ComponentDescriptor]:
        if component_type:
            return [c for c in self._components.values() if c.component_type == component_type]
        return list(self._components.values())

    def update_status(self, name: str, status: ComponentStatus) -> ComponentDescriptor | None:
        comp = self._components.get(name)
        if comp:
            comp.status = status
            comp.metadata["status_updated_at"] = datetime.now(UTC).isoformat()
            logger.info("Component %s status updated to %s", name, status.value)
        return comp

    def count(self) -> int:
        return len(self._components)

    def discover(self, name_pattern: str) -> list[ComponentDescriptor]:
        return [c for c in self._components.values() if name_pattern.lower() in c.name.lower()]
