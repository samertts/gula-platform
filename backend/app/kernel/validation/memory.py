from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.app.kernel import Kernel

logger = logging.getLogger("gula.kernel.validation.memory")


class MemoryValidator:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel

    def validate(self) -> list[dict]:
        issues = []
        import gc
        gc.collect()
        return issues
