"""TaskWorker — discrete task consumer with crash isolation and retry.

Each task executes in its own try/except block. A crash in one task:
  - does NOT affect the worker loop
  - retries up to task.max_retries with exponential backoff
  - sends exhausted tasks to the dead-letter queue

Backoff formula: 2 ** attempt seconds (1s, 2s, 4s, 8s …) capped at 60s.

Usage (in app/worker.py):
    from app.tasks.worker import TaskWorker
    from app.tasks.queue import task_queue

    worker = TaskWorker(task_queue)
    await worker.run()        # runs until cancelled
    await worker.run_once()   # processes one batch (useful in tests)
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

from .queue import _InMemoryQueue, _RedisTaskQueue
from .registry import get_handler
from .schema import TaskPayload, TaskResult, TaskStatus

logger = logging.getLogger("gula.task_worker")

_MAX_BACKOFF_S = 60.0


class TaskWorker:
    def __init__(
        self,
        queue: _InMemoryQueue | _RedisTaskQueue,
        *,
        poll_timeout_s: int = 5,
    ) -> None:
        self._queue          = queue
        self._poll_timeout_s = poll_timeout_s
        self._running        = False

    # ── Public interface ─────────────────────────────────────────────────────

    async def run(self) -> None:
        """Main loop — runs until cancelled."""
        self._running = True
        logger.info("TaskWorker started (poll_timeout=%ds)", self._poll_timeout_s)
        try:
            while self._running:
                task = await self._queue.dequeue(timeout=self._poll_timeout_s)
                if task is None:
                    continue
                await self._process_one(task)
        except asyncio.CancelledError:
            logger.info("TaskWorker cancelled — shutting down cleanly")
            raise
        finally:
            self._running = False

    async def run_once(self) -> Optional[TaskResult]:
        """Drain exactly one task (or return None if queue is empty).

        Useful for synchronous test scenarios that enqueue a single task and
        then immediately call run_once() to drive execution.
        """
        task = await self._queue.dequeue(timeout=0)
        if task is None:
            return None
        return await self._process_one(task)

    def stop(self) -> None:
        self._running = False

    # ── Internal ─────────────────────────────────────────────────────────────

    async def _process_one(self, task: TaskPayload) -> TaskResult:
        handler = get_handler(task.type)
        if handler is None:
            logger.error("No handler for task type %r — sending to DLQ", task.type)
            await self._queue.dead_letter(
                task.model_copy(update={"retry_count": task.max_retries}),
                f"no handler registered for type={task.type!r}",
            )
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.DEAD,
                error=f"no handler for type={task.type!r}",
                attempt=task.retry_count,
            )

        await self._queue.mark_running(task.task_id)
        t0 = time.monotonic()
        try:
            result_value: Any = await asyncio.wait_for(
                handler(task.payload),
                timeout=task.timeout_s,
            )
            duration_ms = (time.monotonic() - t0) * 1000
            await self._queue.ack(task.task_id)
            logger.info("Task %s (%s) done in %.1fms", task.task_id, task.type, duration_ms)
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.DONE,
                result=result_value,
                attempt=task.retry_count,
                duration_ms=duration_ms,
            )

        except asyncio.CancelledError:
            await self._queue.ack(task.task_id)
            raise

        except Exception as exc:
            duration_ms = (time.monotonic() - t0) * 1000
            error_msg   = f"{type(exc).__name__}: {exc}"
            logger.warning(
                "Task %s (%s) failed (attempt %d/%d) — %s",
                task.task_id, task.type, task.retry_count + 1, task.max_retries, error_msg,
            )
            await self._queue.ack(task.task_id)
            return await self._retry_or_dead_letter(task, error_msg)

    async def _retry_or_dead_letter(
        self, task: TaskPayload, error: str
    ) -> TaskResult:
        next_task = task.next_attempt()
        if next_task.exhausted:
            await self._queue.dead_letter(next_task, error)
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.DEAD,
                error=error,
                attempt=next_task.retry_count,
            )

        backoff = min(2.0 ** next_task.retry_count, _MAX_BACKOFF_S)
        logger.info(
            "Task %s retrying in %.0fs (attempt %d/%d)",
            task.task_id, backoff, next_task.retry_count, task.max_retries,
        )
        await asyncio.sleep(backoff)
        await self._queue.enqueue(next_task)
        return TaskResult(
            task_id=task.task_id,
            status=TaskStatus.FAILED,
            error=error,
            attempt=next_task.retry_count,
        )
