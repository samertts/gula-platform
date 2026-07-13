from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from backend.app.kernel import Kernel

logger = logging.getLogger("gula.kernel.validation.stress")


class StressTester:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel

    async def run(self, iterations: int = 100) -> dict:
        import time
        start = time.monotonic()
        for _ in range(iterations):
            _ = self.kernel.get_component("service_registry")
        elapsed = time.monotonic() - start
        return {
            "iterations": iterations,
            "total_time_ms": round(elapsed * 1000, 2),
            "avg_time_ms": round((elapsed / iterations) * 1000, 4),
        }
