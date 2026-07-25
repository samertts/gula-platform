from __future__ import annotations

import asyncio
import contextlib
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class TaskPriority(Enum):
    low = 0
    normal = 1
    high = 2
    urgent = 3


@dataclass
class Task:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.pending
    priority: TaskPriority = TaskPriority.normal
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    result: Any = None
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    timeout: float = 300.0


class TaskQueue:
    def __init__(self, max_concurrent: int = 10):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._pending: dict[str, Task] = {}
        self._running: dict[str, Task] = {}
        self._completed: dict[str, Task] = {}
        self._failed: dict[str, Task] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._handlers: dict[str, Callable] = {}
        self._worker_task: asyncio.Task | None = None
        self._active_tasks: set[asyncio.Task] = set()

    def register_handler(self, task_name: str, handler: Callable):
        self._handlers[task_name] = handler

    async def enqueue(self, task: Task):
        await self._queue.put((-task.priority.value, time.time(), task))
        self._pending[task.id] = task
        logger.debug("Enqueued task %s (%s)", task.id, task.name)

    async def enqueue_batch(self, tasks: list[Task]):
        for task in tasks:
            await self.enqueue(task)

    async def start(self):
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._process_loop())
            logger.info("Task queue worker started")

    async def stop(self):
        if self._worker_task:
            self._worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker_task
            self._worker_task = None
            logger.info("Task queue worker stopped")

    async def _process_loop(self):
        while True:
            try:
                _, _, task = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=1.0,
                )
                _task = asyncio.create_task(self._execute_task(task))
                self._active_tasks.add(_task)
                _task.add_done_callback(self._active_tasks.discard)
            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception("Error in task processing loop: %s", e)

    async def _execute_task(self, task: Task):
        async with self._semaphore:
            handler = self._handlers.get(task.name)
            if handler is None:
                task.status = TaskStatus.failed
                task.error = f"No handler registered for task: {task.name}"
                self._pending.pop(task.id, None)
                self._failed[task.id] = task
                logger.error(task.error)
                return

            task.status = TaskStatus.running
            task.started_at = time.time()
            self._pending.pop(task.id, None)
            self._running[task.id] = task

            try:
                result = await asyncio.wait_for(
                    handler(task),
                    timeout=task.timeout,
                )
                task.status = TaskStatus.completed
                task.completed_at = time.time()
                task.result = result
                self._running.pop(task.id, None)
                self._completed[task.id] = task
                logger.info(
                    "Task %s completed in %.2fs",
                    task.id,
                    task.completed_at - task.started_at,
                )
            except TimeoutError:
                task.status = TaskStatus.failed
                task.error = f"Task timed out after {task.timeout}s"
                self._running.pop(task.id, None)
                self._failed[task.id] = task
                logger.error("Task %s timed out", task.id)
            except Exception as e:
                task.status = TaskStatus.failed
                task.error = str(e)
                self._running.pop(task.id, None)
                self._failed[task.id] = task
                logger.exception("Task %s failed: %s", task.id, e)

    def get_task(self, task_id: str) -> Task | None:
        return (
            self._pending.get(task_id)
            or self._running.get(task_id)
            or self._completed.get(task_id)
            or self._failed.get(task_id)
        )

    def get_stats(self) -> dict[str, Any]:
        return {
            "pending": len(self._pending),
            "running": len(self._running),
            "completed": len(self._completed),
            "failed": len(self._failed),
            "total": len(self._pending)
            + len(self._running)
            + len(self._completed)
            + len(self._failed),
        }

    async def cancel(self, task_id: str) -> bool:
        task = self._pending.pop(task_id, None)
        if task:
            task.status = TaskStatus.cancelled
            self._completed[task_id] = task
            return True
        return False

    async def retry(self, task_id: str) -> Task | None:
        task = self._failed.pop(task_id, None)
        if task and task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.pending
            task.error = None
            await self.enqueue(task)
            return task
        return None
