from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.kernel.runtime.capability_registry import CapabilityRegistry

logger = logging.getLogger("gula.kernel.features.capabilities")


class CapabilityFlagManager:
    def __init__(self, registry: CapabilityRegistry | None = None):
        self._capabilities: dict[str, bool] = {}
        self._registry = registry

    def set_registry(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def register(self, name: str, enabled: bool = False) -> None:
        self._capabilities[name] = enabled

    def is_enabled(self, name: str) -> bool:
        cap_enabled = self._capabilities.get(name, None)
        if cap_enabled is not None:
            return cap_enabled
        if self._registry:
            return self._registry.is_enabled(name)
        return False

    def enable(self, name: str) -> None:
        self._capabilities[name] = True
        if self._registry:
            self._registry.enable(name)

    def disable(self, name: str) -> None:
        self._capabilities[name] = False
        if self._registry:
            self._registry.disable(name)

    def sync_from_registry(self) -> int:
        if not self._registry:
            return 0
        count = 0
        for cap in self._registry.list_capabilities():
            self._capabilities[cap.name] = cap.enabled
            count += 1
        return count

    def sync_to_registry(self) -> int:
        if not self._registry:
            return 0
        count = 0
        for name, enabled in self._capabilities.items():
            if self._registry.has(name):
                if enabled:
                    self._registry.enable(name)
                else:
                    self._registry.disable(name)
                count += 1
        return count

    def list_all(self) -> dict[str, bool]:
        result = dict(self._capabilities)
        if self._registry:
            for cap in self._registry.list_capabilities():
                if cap.name not in result:
                    result[cap.name] = cap.enabled
        return result
