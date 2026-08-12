from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

logger = logging.getLogger("gula.scheduler")


class ScheduledTask:
    def __init__(
        self,
        name: str,
        interval_seconds: int,
        coro: Callable[[], Coroutine[Any, Any, None]],
        delay_first: int = 0,
    ) -> None:
        self._name = name
        self._interval = interval_seconds
        self._coro = coro
        self._delay_first = delay_first
        self._task: asyncio.Task[None] | None = None
        self._running = False

    @property
    def name(self) -> str:
        return self._name

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        if self._delay_first > 0:
            await asyncio.sleep(self._delay_first)
        while self._running:
            try:
                await self._coro()
            except Exception:
                logger.exception("Scheduled task '%s' failed", self._name)
            await asyncio.sleep(self._interval)

    def stop(self) -> None:
        self._running = False


class Scheduler:
    def __init__(self) -> None:
        self._tasks: dict[str, ScheduledTask] = {}

    def every(
        self,
        name: str,
        interval_seconds: int,
        delay_first: int = 0,
    ) -> Callable[[Callable[[], Coroutine[Any, Any, None]]], Callable[[], Coroutine[Any, Any, None]]]:
        def decorator(fn: Callable[[], Coroutine[Any, Any, None]]) -> Callable[[], Coroutine[Any, Any, None]]:
            task = ScheduledTask(name, interval_seconds, fn, delay_first)
            self._tasks[name] = task
            return fn
        return decorator

    def add(self, task: ScheduledTask) -> None:
        self._tasks[task.name] = task

    async def run_all(self) -> list[asyncio.Task[None]]:
        return [asyncio.create_task(task.start()) for task in self._tasks.values()]

    def stop_all(self) -> None:
        for task in self._tasks.values():
            task.stop()

    def get(self, name: str) -> ScheduledTask | None:
        return self._tasks.get(name)


scheduler = Scheduler()

__all__ = ["ScheduledTask", "Scheduler", "scheduler"]
