from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from backend.app.kernel.exceptions import ModuleLoadError
from backend.app.kernel.module.registry import ModuleRegistry
from backend.app.kernel.module.metadata import ModuleMetadataParser
from backend.app.kernel.module.discovery import ModuleDiscovery
from backend.app.kernel.module.resolver import ModuleDependencyResolver
from backend.app.kernel.module.compatibility import ModuleVersionCompatibility
from backend.app.kernel.types import ModuleDescriptor

if TYPE_CHECKING:
    from backend.app.kernel import Kernel

logger = logging.getLogger("gula.kernel.module.loader")


class ModuleLoader:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.registry = ModuleRegistry()
        self.metadata_parser = ModuleMetadataParser()
        self.discovery = ModuleDiscovery()
        self.resolver = ModuleDependencyResolver()
        self.compatibility = ModuleVersionCompatibility()

    async def load(self, path: str) -> ModuleDescriptor:
        metadata = self.metadata_parser.parse(path)
        self.resolver.validate(metadata, self.registry.list_modules())
        self.compatibility.check(metadata)
        self.registry.register(metadata)
        return metadata

    async def unload(self, name: str) -> None:
        self.registry.unregister(name)

    def list_modules(self) -> list[ModuleDescriptor]:
        return self.registry.list_modules()
