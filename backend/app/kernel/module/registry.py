from __future__ import annotations

import logging
from typing import Dict, List, Optional

from backend.app.kernel.types import ModuleDescriptor

logger = logging.getLogger("gula.kernel.module.registry")


class ModuleRegistry:
    def __init__(self):
        self._modules: dict[str, ModuleDescriptor] = {}

    def register(self, descriptor: ModuleDescriptor) -> None:
        self._modules[descriptor.name] = descriptor
        logger.info(
            "Module registered",
            extra={"module": descriptor.name, "version": descriptor.version},
        )

    def unregister(self, name: str) -> None:
        self._modules.pop(name, None)

    def get(self, name: str) -> ModuleDescriptor | None:
        return self._modules.get(name)

    def has(self, name: str) -> bool:
        return name in self._modules

    def list_modules(self) -> list[ModuleDescriptor]:
        return list(self._modules.values())
