from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("gula.kernel.lifecycle")


class LifecycleComponent:
    def __init__(self, name: str):
        self.name = name
        self.state = "created"
        self._start_hooks: list[Callable] = []
        self._stop_hooks: list[Callable] = []
        self._health_hooks: list[Callable] = []

    def on_start(self, hook: Callable) -> None:
        self._start_hooks.append(hook)

    def on_stop(self, hook: Callable) -> None:
        self._stop_hooks.append(hook)

    def on_health(self, hook: Callable) -> None:
        self._health_hooks.append(hook)

    async def start(self) -> None:
        self.state = "starting"
        for hook in self._start_hooks:
            result = hook()
            if hasattr(result, "__await__"):
                await result
        self.state = "running"

    async def stop(self) -> None:
        self.state = "stopping"
        for hook in reversed(self._stop_hooks):
            result = hook()
            if hasattr(result, "__await__"):
                await result
        self.state = "stopped"

    def health(self) -> dict:
        result = {"state": self.state}
        for hook in self._health_hooks:
            result.update(hook())
        return result


class LifecycleManager:
    def __init__(self):
        self._components: dict[str, LifecycleComponent] = {}
        self._start_order: list[str] = []
        self._stop_order: list[str] = []

    def register(self, component: LifecycleComponent) -> None:
        self._components[component.name] = component
        self._start_order.append(component.name)
        self._stop_order.insert(0, component.name)

    def get(self, name: str) -> LifecycleComponent | None:
        return self._components.get(name)

    async def start_all(self) -> None:
        for name in self._start_order:
            component = self._components[name]
            try:
                await component.start()
                logger.info("Component started", extra={"component": name})
            except Exception as e:
                logger.error(
                    "Component start failed",
                    extra={"component": name, "error": str(e)},
                )
                component.state = "failed"

    async def stop_all(self) -> None:
        for name in self._stop_order:
            component = self._components[name]
            try:
                await component.stop()
                logger.info("Component stopped", extra={"component": name})
            except Exception as e:
                logger.error(
                    "Component stop failed",
                    extra={"component": name, "error": str(e)},
                )

    def health(self) -> dict[str, dict]:
        return {name: comp.health() for name, comp in self._components.items()}
