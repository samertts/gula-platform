from __future__ import annotations

import logging
import time

from app.kernel import Kernel

logger = logging.getLogger("gula.kernel.validation.performance")


class PerformanceValidator:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel

    def validate(self) -> list[dict]:
        issues = []
        start = time.monotonic()
        _ = self.kernel.get_component("service_registry")
        elapsed = (time.monotonic() - start) * 1000
        if elapsed > 100:
            issues.append(
                {
                    "type": "slow_component_access",
                    "component": "service_registry",
                    "duration_ms": round(elapsed, 2),
                },
            )
        return issues
