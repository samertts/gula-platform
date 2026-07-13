from __future__ import annotations

import logging
from pathlib import Path

from backend.app.kernel.types import ModuleDescriptor

logger = logging.getLogger("gula.kernel.module.metadata")


class ModuleMetadataParser:
    def parse(self, path: str) -> ModuleDescriptor:
        module_path = Path(path)
        metadata_file = module_path / "module.json"
        if metadata_file.exists():
            import json

            with open(metadata_file) as f:
                data = json.load(f)
            return ModuleDescriptor(
                name=data.get("name", module_path.stem),
                version=data.get("version", "1.0.0"),
                path=str(module_path),
                dependencies=data.get("dependencies", {}),
                entry_points=data.get("entry_points", []),
                enabled=data.get("enabled", True),
            )
        return ModuleDescriptor(
            name=module_path.stem,
            version="1.0.0",
            path=str(module_path),
        )
