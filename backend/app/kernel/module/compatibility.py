from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from backend.app.kernel.exceptions import ModuleVersionConflict
from backend.app.kernel.types import ModuleDescriptor

logger = logging.getLogger("gula.kernel.module.compatibility")


class ModuleVersionCompatibility:
    def check(self, descriptor: ModuleDescriptor) -> None:
        pass

    def is_compatible(self, required: str, installed: str) -> bool:
        req_parts = [int(x) for x in required.split(".")]
        inst_parts = [int(x) for x in installed.split(".")]
        for r, i in zip(req_parts, inst_parts):
            if i > r:
                return True
            if i < r:
                return False
        return len(inst_parts) >= len(req_parts)
