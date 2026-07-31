"""Redis-backed task queue with dead-letter support.

Wire format: JSON-serialised TaskPayload pushed to a Redis List.

    QUEUE_KEY   — pending tasks (producers LPUSH, workers BRPOP)
    DLQ_KEY     — dead-letter tasks (tasks that exhausted max_retries)
    RUNNING_KEY — set of task_ids currently being executed (for visibility)

Fallback: when Redis is unavailable (REDIS_URL not set, or connection fails)
the queue transparently falls back to an asyncio.Queue in-memory store so
tests and development environments require zero infrastructure.

The in-memory fallback deliberately does NOT implement BRPOP blocking —
dequeue() returns immediately (None if empty) so test loops don't hang.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import threading

from ..config import REDIS_URL
from .schema import TaskPayload

logger = logging.getLogger("gula.task_queue")

# ── Redis key names ──────────────────────────────────────────────────────────
QUEUE_KEY = "gula:tasks:pending"
DLQ_KEY = "gula:tasks:dead"
RUNNING_SET = "gula:tasks:running"

# ── In-memory fallback ───────────────────────────────────────────────────────


class _InMemoryQueue:
    """asyncio.Queue wrapper that mirrors the RedisTaskQueue interface."""

    def __init__(self) -> None:
        self._pending: asyncio.Queue[str] = asyncio.Queue()
        self._dlq: list[str] = []
        self._running: set[str] = set()

    async def enqueue(self, task: TaskPayload) -> None:
        await self._pending.put(task.model_dump_json())

    async def dequeue(self, timeout: int = 5) -> TaskPayload | None:
        try:
            raw = self._pending.get_nowait()
            return TaskPayload.model_validate_json(raw)
        except asyncio.QueueEmpty:
            return None

    async def dead_letter(self, task: TaskPayload, error: str) -> None:
        entry = {"task": task.model_dump_json(), "error": error}
        self._dlq.append(json.dumps(entry))
        logger.warning(
            "DLQ: task %s (%s) after %d attempts — %s",
            task.task_id,
            task.type,
            task.retry_count,
            error,
        )

    async def ack(self, task_id: str) -> None:
        self._running.discard(task_id)

    async def mark_running(self, task_id: str) -> None:
        self._running.add(task_id)

    async def queue_depth(self) -> int:
        return self._pending.qsize()

    async def dlq_depth(self) -> int:
        return len(self._dlq)

    async def close(self) -> None:
        pass


# ── Redis-backed implementation ──────────────────────────────────────────────


class _RedisTaskQueue:
    """Production queue backed by Redis Lists.

    Uses BRPOP (blocking pop) with a configurable timeout so the worker
    yields control to the event loop rather than spinning.
    """

    def __init__(self, redis_client) -> None:
        self._r = redis_client

    async def enqueue(self, task: TaskPayload) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._r.lpush, QUEUE_KEY, task.model_dump_json())
        logger.debug("Enqueued task %s (%s)", task.task_id, task.type)

    async def dequeue(self, timeout: int = 5) -> TaskPayload | None:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self._r.brpop, QUEUE_KEY, timeout)
        if result is None:
            return None
        _key, raw = result
        return TaskPayload.model_validate_json(raw)

    async def dead_letter(self, task: TaskPayload, error: str) -> None:
        entry = json.dumps({"task": task.model_dump_json(), "error": error})
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._r.lpush, DLQ_KEY, entry)
        logger.warning(
            "DLQ: task %s (%s) after %d attempts — %s",
            task.task_id,
            task.type,
            task.retry_count,
            error,
        )

    async def ack(self, task_id: str) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._r.srem, RUNNING_SET, task_id)

    async def mark_running(self, task_id: str) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._r.sadd, RUNNING_SET, task_id)

    async def queue_depth(self) -> int:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._r.llen, QUEUE_KEY)

    async def dlq_depth(self) -> int:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._r.llen, DLQ_KEY)

    async def close(self) -> None:
        with contextlib.suppress(Exception):
            self._r.close()


# ── Public factory ───────────────────────────────────────────────────────────


def build_queue() -> _InMemoryQueue | _RedisTaskQueue:
    """Return the appropriate queue backend.

    Tries Redis first; silently falls back to in-memory so tests and
    development environments need no infrastructure.
    """
    if not REDIS_URL:
        logger.info("REDIS_URL not set — task queue using in-memory fallback")
        return _InMemoryQueue()

    try:
        import redis as redis_lib

        client = redis_lib.from_url(REDIS_URL, socket_connect_timeout=2, decode_responses=True)
        client.ping()
        logger.info("Task queue connected to Redis (%s)", REDIS_URL)
        return _RedisTaskQueue(client)
    except Exception as exc:
        logger.warning("Redis unavailable (%s) — task queue using in-memory fallback", exc)
        return _InMemoryQueue()


# Module-level singleton — created lazily so importing this module never
# connects to Redis. The first method call triggers _build_queue().
# Tests can replace task_queue with a fresh _InMemoryQueue() in their fixtures.
class _LazyTaskQueue:
    _instance = None
    _lock = threading.Lock()

    def _ensure(self):
        if self._instance is None:
            with self._lock:
                if self._instance is None:
                    self._instance = build_queue()
        return self._instance

    async def enqueue(self, task: TaskPayload) -> None:
        await self._ensure().enqueue(task)

    async def dequeue(self, timeout: int = 5) -> TaskPayload | None:
        return await self._ensure().dequeue(timeout)

    async def dead_letter(self, task: TaskPayload, error: str) -> None:
        await self._ensure().dead_letter(task, error)

    async def ack(self, task_id: str) -> None:
        await self._ensure().ack(task_id)

    async def mark_running(self, task_id: str) -> None:
        await self._ensure().mark_running(task_id)

    async def queue_depth(self) -> int:
        return await self._ensure().queue_depth()

    async def dlq_depth(self) -> int:
        return await self._ensure().dlq_depth()

    async def close(self) -> None:
        await self._ensure().close()


task_queue: _LazyTaskQueue = _LazyTaskQueue()
