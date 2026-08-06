import asyncio
import logging
import os
import threading
from platform.core.kernel import Kernel
from typing import Any


class RuntimeManager:
    def __init__(self):
        self._logger = logging.getLogger("gula.runtime")
        self._kernel = Kernel.instance()
        self._workers: dict[str, asyncio.Task] = {}
        self._threads: dict[str, threading.Thread] = {}
        self._running = False

    @property
    def active_workers(self) -> int:
        return len(self._workers)

    @property
    def active_threads(self) -> int:
        return len(self._threads)

    async def start_background_worker(self, name: str, coro, restart_on_failure: bool = True) -> None:
        async def _run():
            while self._running:
                try:
                    await coro
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._logger.error("Worker '%s' failed: %s", name, e, exc_info=True)
                    if not restart_on_failure:
                        break
                    await asyncio.sleep(5)
        task = asyncio.create_task(_run(), name=f"worker-{name}")
        self._workers[name] = task
        self._logger.info("Background worker started: %s", name)

    async def stop_worker(self, name: str) -> None:
        task = self._workers.pop(name, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            self._logger.info("Worker stopped: %s", name)

    async def stop_all_workers(self) -> None:
        for name in list(self._workers.keys()):
            await self.stop_worker(name)

    def start_thread(self, name: str, target, daemon: bool = True) -> None:
        thread = threading.Thread(target=target, name=f"gula-{name}", daemon=daemon)
        thread.start()
        self._threads[name] = thread
        self._logger.info("Thread started: %s (pid=%d)", name, thread.native_id)

    def get_resource_usage(self) -> dict[str, Any]:
        import psutil
        process = psutil.Process(os.getpid())
        return {
            "cpu_percent": process.cpu_percent(),
            "memory_rss": process.memory_info().rss,
            "memory_percent": process.memory_percent(),
            "threads": process.num_threads(),
            "open_files": process.num_fds() if hasattr(process, "num_fds") else 0,
            "active_workers": self.active_workers,
            "active_threads": self.active_threads,
        }

    async def start(self) -> None:
        self._running = True
        self._logger.info("Runtime manager started")

    async def stop(self) -> None:
        self._running = False
        await self.stop_all_workers()
        self._logger.info("Runtime manager stopped")
