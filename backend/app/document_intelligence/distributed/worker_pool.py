from __future__ import annotations
import asyncio
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class WorkerPool:
    def __init__(
        self,
        min_workers: int = 2,
        max_workers: int = 20,
        idle_timeout: float = 60.0,
    ):
        self._min = min_workers
        self._max = max_workers
        self._idle_timeout = idle_timeout
        self._workers: set[asyncio.Task] = set()
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._active_count = 0
        self._running = False

    async def start(self):
        self._running = True
        for _ in range(self._min):
            worker = asyncio.create_task(self._worker_loop())
            self._workers.add(worker)
        logger.info("Worker pool started with %d workers", self._min)

    async def stop(self):
        self._running = False
        for worker in self._workers:
            worker.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("Worker pool stopped")

    async def submit(self, handler: Callable, *args: Any, **kwargs: Any):
        await self._task_queue.put((handler, args, kwargs))

    async def _worker_loop(self):
        while self._running:
            try:
                handler, args, kwargs = await asyncio.wait_for(
                    self._task_queue.get(), timeout=1.0
                )
                self._active_count += 1
                try:
                    result = await handler(*args, **kwargs)
                    logger.debug("Worker completed task")
                except Exception as e:
                    logger.exception("Worker task failed: %s", e)
                finally:
                    self._active_count -= 1
                    self._task_queue.task_done()
            except asyncio.TimeoutError:
                if len(self._workers) > self._min:
                    break
            except asyncio.CancelledError:
                break

    @property
    def active_workers(self) -> int:
        return self._active_count

    @property
    def total_workers(self) -> int:
        return len(self._workers)

    @property
    def queue_size(self) -> int:
        return self._task_queue.qsize()
