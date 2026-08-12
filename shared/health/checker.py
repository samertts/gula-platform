from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("gula.health")


class HealthStatus(Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


@dataclass
class ComponentHealth:
    name: str
    status: HealthStatus
    latency_ms: float = 0.0
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


class HealthCheck(ABC):
    @abstractmethod
    def check(self) -> ComponentHealth:
        ...


class HealthChecker:
    def __init__(self) -> None:
        self._checks: dict[str, HealthCheck | Callable[[], ComponentHealth]] = {}

    def register(self, name: str, check: HealthCheck | Callable[[], ComponentHealth]) -> None:
        self._checks[name] = check

    def check_all(self) -> dict[str, ComponentHealth]:
        results: dict[str, ComponentHealth] = {}
        for name, check in self._checks.items():
            start = time.time()
            try:
                result = check() if callable(check) else check.check()
                result.latency_ms = (time.time() - start) * 1000
            except Exception as exc:
                result = ComponentHealth(
                    name=name,
                    status=HealthStatus.RED,
                    error=str(exc),
                    latency_ms=(time.time() - start) * 1000,
                )
            results[name] = result
        return results

    def overall_status(self) -> HealthStatus:
        results = self.check_all()
        statuses = [r.status for r in results.values()]
        if any(s == HealthStatus.RED for s in statuses):
            return HealthStatus.RED
        if any(s == HealthStatus.YELLOW for s in statuses):
            return HealthStatus.YELLOW
        return HealthStatus.GREEN

    def grade(self) -> str:
        return self.overall_status().value
