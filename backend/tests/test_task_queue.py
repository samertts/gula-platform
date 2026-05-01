"""Tests for the GULA task queue layer.

All tests use the in-memory queue backend so no Redis infrastructure is
required.  The conftest.py runtime isolation (RUNTIME_MODE=test,
FEATURE_BACKGROUND_TASKS=false) remains in force — these tests call the
task primitives directly and never spawn background loops.
"""
from __future__ import annotations

import asyncio
import pytest

from app.tasks.queue    import _InMemoryQueue
from app.tasks.registry import task_handler, get_handler, _REGISTRY
from app.tasks.schema   import TaskPayload, TaskStatus
from app.tasks.worker   import TaskWorker


# ── Helpers ───────────────────────────────────────────────────────────────────

def fresh_queue() -> _InMemoryQueue:
    """Return a brand-new in-memory queue (not the module singleton)."""
    return _InMemoryQueue()


def fresh_worker(queue: _InMemoryQueue) -> TaskWorker:
    return TaskWorker(queue, poll_timeout_s=0)


# ── Schema ────────────────────────────────────────────────────────────────────

def test_task_payload_defaults():
    t = TaskPayload(type="ping", payload={"x": 1})
    assert t.retry_count == 0
    assert t.max_retries == 3
    assert not t.exhausted
    assert t.task_id != ""


def test_task_payload_next_attempt():
    t = TaskPayload(type="ping", max_retries=2)
    t1 = t.next_attempt()
    assert t1.retry_count == 1
    assert not t1.exhausted
    t2 = t1.next_attempt()
    assert t2.retry_count == 2
    assert t2.exhausted


def test_task_payload_json_roundtrip():
    t = TaskPayload(type="send_notification", payload={"user": 99})
    raw = t.model_dump_json()
    t2  = TaskPayload.model_validate_json(raw)
    assert t2.task_id   == t.task_id
    assert t2.type      == t.type
    assert t2.payload   == t.payload


# ── Queue ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_queue_enqueue_dequeue():
    q   = fresh_queue()
    task = TaskPayload(type="ping")
    await q.enqueue(task)
    assert await q.queue_depth() == 1
    got = await q.dequeue()
    assert got is not None
    assert got.task_id == task.task_id
    assert await q.queue_depth() == 0


@pytest.mark.asyncio
async def test_queue_dequeue_empty_returns_none():
    q = fresh_queue()
    assert await q.dequeue() is None


@pytest.mark.asyncio
async def test_queue_dead_letter():
    q    = fresh_queue()
    task = TaskPayload(type="broken", max_retries=0)
    await q.dead_letter(task, "simulated failure")
    assert await q.dlq_depth() == 1
    assert await q.queue_depth() == 0


@pytest.mark.asyncio
async def test_queue_mark_running_and_ack():
    q    = fresh_queue()
    task = TaskPayload(type="ping")
    await q.mark_running(task.task_id)
    assert task.task_id in q._running
    await q.ack(task.task_id)
    assert task.task_id not in q._running


# ── Registry ─────────────────────────────────────────────────────────────────

def test_task_handler_decorator_registers():
    type_name = "_test_handler_registration"
    _REGISTRY.pop(type_name, None)

    @task_handler(type_name)
    async def _handler(payload: dict):
        return payload

    assert get_handler(type_name) is _handler
    _REGISTRY.pop(type_name, None)


def test_get_handler_unknown_returns_none():
    assert get_handler("__no_such_type__") is None


# ── TaskWorker — happy path ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_worker_executes_task_successfully():
    q    = fresh_queue()
    w    = fresh_worker(q)
    type_name = "_test_success"
    _REGISTRY.pop(type_name, None)

    @task_handler(type_name)
    async def _ok(payload: dict):
        return {"echo": payload["val"]}

    task = TaskPayload(type=type_name, payload={"val": 42})
    await q.enqueue(task)

    result = await w.run_once()
    assert result is not None
    assert result.status  == TaskStatus.DONE
    assert result.result  == {"echo": 42}
    assert result.task_id == task.task_id

    _REGISTRY.pop(type_name, None)


@pytest.mark.asyncio
async def test_worker_crash_isolation_single_task():
    """A crashing task must not stop the worker loop — siblings are unaffected."""
    q          = fresh_queue()
    w          = fresh_worker(q)
    type_crash = "_test_crash"
    type_ok    = "_test_after_crash"
    _REGISTRY.pop(type_crash, None)
    _REGISTRY.pop(type_ok,    None)

    @task_handler(type_crash)
    async def _crash(payload: dict):
        raise ValueError("boom")

    @task_handler(type_ok)
    async def _ok(payload: dict):
        return "survived"

    crash_task = TaskPayload(type=type_crash, max_retries=0)
    ok_task    = TaskPayload(type=type_ok)

    await q.enqueue(crash_task)
    await q.enqueue(ok_task)

    # First: crash_task → dead-lettered (max_retries=0)
    r1 = await w.run_once()
    assert r1.status == TaskStatus.DEAD

    # Second: ok_task — worker must still be running
    r2 = await w.run_once()
    assert r2.status == TaskStatus.DONE
    assert r2.result == "survived"

    _REGISTRY.pop(type_crash, None)
    _REGISTRY.pop(type_ok,    None)


# ── TaskWorker — retry logic ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_worker_retries_on_failure():
    """A task that fails should be re-enqueued with retry_count incremented."""
    q         = fresh_queue()
    type_name = "_test_retry"
    _REGISTRY.pop(type_name, None)

    call_count = {"n": 0}

    @task_handler(type_name)
    async def _flaky(payload: dict):
        call_count["n"] += 1
        raise RuntimeError("transient")

    # max_retries=2: executes at retry_count=0 (FAILED), then retry_count=1 (FAILED),
    # then next would be retry_count=2 which is exhausted → DEAD on 3rd run.
    task = TaskPayload(type=type_name, max_retries=3)
    await q.enqueue(task)

    # Patch sleep to avoid real waiting in tests
    async def _no_sleep(_):
        pass

    import app.tasks.worker as worker_mod
    original_sleep = asyncio.sleep
    worker_mod.asyncio.sleep = _no_sleep

    try:
        w   = fresh_worker(q)
        r1  = await w.run_once()    # retry_count=0 → next=1 (1<3) → FAILED
        assert r1.status == TaskStatus.FAILED
        assert await q.queue_depth() == 1

        r2 = await w.run_once()     # retry_count=1 → next=2 (2<3) → FAILED
        assert r2.status == TaskStatus.FAILED

        r3 = await w.run_once()     # retry_count=2 → next=3 (3>=3) → DEAD
        assert r3.status == TaskStatus.DEAD
        assert await q.dlq_depth() == 1
    finally:
        worker_mod.asyncio.sleep = original_sleep

    _REGISTRY.pop(type_name, None)


# ── TaskWorker — unknown task type → DLQ ─────────────────────────────────────

@pytest.mark.asyncio
async def test_worker_unknown_type_goes_to_dlq():
    q    = fresh_queue()
    w    = fresh_worker(q)
    task = TaskPayload(type="__no_handler_registered__")
    await q.enqueue(task)

    result = await w.run_once()
    assert result.status == TaskStatus.DEAD
    assert await q.dlq_depth() == 1


# ── TaskWorker — timeout enforcement ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_worker_timeout_error_goes_to_dlq():
    """asyncio.TimeoutError raised by a handler → DLQ when max_retries=0."""
    q         = fresh_queue()
    type_name = "_test_timeout"
    _REGISTRY.pop(type_name, None)

    @task_handler(type_name)
    async def _timeout_handler(payload: dict):
        # Simulate an internal deadline being exceeded (e.g. from a network call)
        raise asyncio.TimeoutError("deadline exceeded")

    task = TaskPayload(type=type_name, max_retries=0)
    await q.enqueue(task)

    try:
        w      = fresh_worker(q)
        result = await w.run_once()
        assert result.status == TaskStatus.DEAD
        assert await q.dlq_depth() == 1
    finally:
        _REGISTRY.pop(type_name, None)


# ── Queue FIFO ordering ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_queue_fifo_order():
    """Tasks must be dequeued in enqueue order (FIFO)."""
    q = fresh_queue()
    t1 = TaskPayload(type="ping", payload={"n": 1})
    t2 = TaskPayload(type="ping", payload={"n": 2})
    t3 = TaskPayload(type="ping", payload={"n": 3})
    for t in (t1, t2, t3):
        await q.enqueue(t)

    got1 = await q.dequeue()
    got2 = await q.dequeue()
    got3 = await q.dequeue()
    assert got1.task_id == t1.task_id
    assert got2.task_id == t2.task_id
    assert got3.task_id == t3.task_id
