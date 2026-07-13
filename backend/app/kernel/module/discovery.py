from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from backend.app.kernel.types import ModuleDescriptor

logger = logging.getLogger("gula.kernel.module.discovery")


class ModuleDiscovery:
    def __init__(self):
        self._search_paths: list[str] = []

    def add_search_path(self, path: str) -> None:
        self._search_paths.append(path)

    def discover(self) -> list[str]:
        discovered = []
        for search_path in self._search_paths:
            base = Path(search_path)
            if not base.exists():
                continue
            for entry in base.iterdir():
                if entry.is_dir() and (entry / "module.json").exists():
                    discovered.append(str(entry))
        return discovered
