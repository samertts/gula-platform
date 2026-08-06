import asyncio
import logging
from collections.abc import Callable
from typing import Any


class TaskScheduler:
    def __init__(self):
        self._logger = logging.getLogger("gula.runtime.scheduler")
        self._tasks: dict[str, dict[str, Any]] = {}
        self._running = False

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False

    def schedule_once(self, name: str, delay: float, callback: Callable) -> None:
        async def _run():
            await asyncio.sleep(delay)
            try:
                await callback() if hasattr(callback, "__await__") else callback()
            except Exception as e:
                self._logger.error("Scheduled task '%s' failed: %s", name, e)
        task = asyncio.create_task(_run(), name=f"sched-{name}")
        self._tasks[name] = {"task": task, "type": "once", "callback": callback}

    def schedule_interval(self, name: str, interval: float, callback: Callable) -> None:
        async def _run():
            while self._running:
                await asyncio.sleep(interval)
                try:
                    await callback() if hasattr(callback, "__await__") else callback()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._logger.error("Interval task '%s' failed: %s", name, e)
        task = asyncio.create_task(_run(), name=f"sched-{name}")
        self._tasks[name] = {"task": task, "type": "interval", "callback": callback}

    def schedule_cron(self, name: str, expression: str, callback: Callable) -> None:
        self._logger.warning("Cron scheduling requires aioschcdul; using interval fallback")
        self.schedule_interval(name, 60.0, callback)

    def cancel(self, name: str) -> bool:
        entry = self._tasks.pop(name, None)
        if entry:
            entry["task"].cancel()
            return True
        return False

    async def cancel_all(self) -> None:
        for name in list(self._tasks.keys()):
            self.cancel(name)
