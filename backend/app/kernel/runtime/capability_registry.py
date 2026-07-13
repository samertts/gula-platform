from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.app.kernel.types import CapabilityDescriptor

logger = logging.getLogger("gula.kernel.capability_registry")


class CapabilityRegistry:
    def __init__(self):
        self._capabilities: dict[str, CapabilityDescriptor] = {}

    def register(self, descriptor: CapabilityDescriptor) -> None:
        self._capabilities[descriptor.name] = descriptor
        logger.info(
            "Capability registered",
            extra={"capability": descriptor.name, "version": descriptor.version},
        )

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

    def disable(self, name: str) -> None:
        cap = self._capabilities.get(name)
        if cap:
            cap.enabled = False

    def list_capabilities(self) -> list[CapabilityDescriptor]:
        return list(self._capabilities.values())

    def list_enabled(self) -> list[CapabilityDescriptor]:
        return [c for c in self._capabilities.values() if c.enabled]

    def check_dependencies(self, name: str) -> bool:
        cap = self._capabilities.get(name)
        if not cap:
            return False
        return all(dep in self._capabilities for dep in cap.dependencies)
