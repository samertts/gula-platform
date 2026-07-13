from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("gula.kernel.startup")


class StartupTask:
    def __init__(
        self,
        name: str,
        handler: Callable,
        required: bool = True,
        timeout: float = 30.0,
        dependencies: list[str] | None = None,
    ):
        self.name = name
        self.handler = handler
        self.required = required
        self.timeout = timeout
        self.dependencies = dependencies or []
        self.completed = False
        self.error: str | None = None
        self.duration_ms: float = 0.0


class StartupManager:
    def __init__(self):
        self._tasks: dict[str, StartupTask] = {}

    def register(self, task: StartupTask) -> None:
        self._tasks[task.name] = task

    async def execute_all(self) -> list[dict]:
        results = []
        for name, task in self._tasks.items():
            start = time.monotonic()
            try:
                result = task.handler()
                if hasattr(result, "__await__"):
                    await result
                task.completed = True
                task.duration_ms = round((time.monotonic() - start) * 1000)
                logger.info(
                    "Startup task completed",
                    extra={"task": name, "duration_ms": task.duration_ms},
                )
            except Exception as e:
                task.completed = False
                task.error = str(e)
                task.duration_ms = round((time.monotonic() - start) * 1000)
                logger.error(
                    "Startup task failed",
                    extra={"task": name, "error": str(e)},
                )
                if task.required:
                    raise
            results.append(
                {
                    "name": name,
                    "completed": task.completed,
                    "error": task.error,
                    "duration_ms": task.duration_ms,
                }
            )
        return results
