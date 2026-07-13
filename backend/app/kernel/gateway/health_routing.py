from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("gula.kernel.gateway.health")


class HealthRouter:
    def __init__(self):
        self._health_checks: dict[str, Callable] = {}

    def register(self, name: str, check: Callable) -> None:
        self._health_checks[name] = check

    def check_all(self) -> dict[str, dict]:
        results = {}
        for name, check in self._health_checks.items():
            try:
                result = check()
                results[name] = {"healthy": True, "data": result}
            except Exception as e:
                results[name] = {"healthy": False, "error": str(e)}
        return results
