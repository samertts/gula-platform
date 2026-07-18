import asyncio
import logging
import time
from enum import Enum
from typing import Any


class HealthStatus(Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    UNKNOWN = "unknown"


class HealthComponent:
    def __init__(self, name: str, check_fn=None):
        self.name = name
        self._check_fn = check_fn
        self.status = HealthStatus.UNKNOWN
        self.last_check = 0.0
        self.latency_ms = 0.0
        self.error: str | None = None

    async def check(self) -> HealthStatus:
        if self._check_fn is None:
            return HealthStatus.UNKNOWN
        start = time.monotonic()
        try:
            result = await self._check_fn()
            self.status = result if isinstance(result, HealthStatus) else HealthStatus.GREEN
            self.error = None
        except Exception as e:
            self.status = HealthStatus.RED
            self.error = str(e)
        self.latency_ms = (time.monotonic() - start) * 1000
        self.last_check = time.time()
        return self.status


class HealthManager:
    def __init__(self, check_interval: float = 30.0):
        self._logger = logging.getLogger("gula.kernel.health")
        self._components: dict[str, HealthComponent] = {}
        self._check_interval = check_interval
        self._system_ready = False
        self._task: asyncio.Task | None = None

    def register(self, name: str, check_fn=None) -> HealthComponent:
        component = HealthComponent(name, check_fn)
        self._components[name] = component
        self._logger.debug("Health component registered: %s", name)
        return component

    def unregister(self, name: str) -> None:
        self._components.pop(name, None)

    def set_system_ready(self, ready: bool) -> None:
        self._system_ready = ready
        self._logger.info("System ready: %s", ready)

    def is_system_ready(self) -> bool:
        return self._system_ready

    def get_component(self, name: str) -> HealthComponent | None:
        return self._components.get(name)

    def get_aggregate_status(self) -> HealthStatus:
        if not self._system_ready:
            return HealthStatus.RED
        if not self._components:
            return HealthStatus.UNKNOWN
        statuses = [c.status for c in self._components.values()]
        if any(s == HealthStatus.RED for s in statuses):
            return HealthStatus.RED
        if any(s == HealthStatus.YELLOW for s in statuses):
            return HealthStatus.YELLOW
        if any(s == HealthStatus.UNKNOWN for s in statuses):
            return HealthStatus.UNKNOWN
        return HealthStatus.GREEN

    async def check_all(self) -> dict[str, HealthStatus]:
        results = {}
        for name, component in self._components.items():
            status = await component.check()
            results[name] = status
        return results

    def get_diagnostics(self) -> dict[str, Any]:
        return {
            "system_ready": self._system_ready,
            "aggregate_status": self.get_aggregate_status().value,
            "components": {
                name: {
                    "status": c.status.value,
                    "latency_ms": round(c.latency_ms, 2),
                    "last_check": c.last_check,
                    "error": c.error,
                }
                for name, c in self._components.items()
            },
        }

    async def start_periodic_checks(self) -> None:
        async def _loop():
            while True:
                await asyncio.sleep(self._check_interval)
                try:
                    await self.check_all()
                except Exception as e:
                    self._logger.error("Health check error: %s", e)
        self._task = asyncio.create_task(_loop())

    async def stop_periodic_checks(self) -> None:
        if self._task:
            self._task.cancel()
            self._task = None
