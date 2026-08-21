import asyncio

import pytest
from app.tasks.queue import QueueBackpressureError, _InMemoryQueue
from app.tasks.schema import TaskPayload


def _task(index: int) -> TaskPayload:
    return TaskPayload(type="synthetic", payload={"index": index})


@pytest.mark.asyncio
async def test_in_memory_queue_rejects_when_capacity_is_reached() -> None:
    queue = _InMemoryQueue(max_depth=2)

    await queue.enqueue(_task(1))
    await queue.enqueue(_task(2))

    with pytest.raises(QueueBackpressureError, match="capacity reached"):
        await queue.enqueue(_task(3))

    assert await queue.queue_depth() == 2


@pytest.mark.asyncio
async def test_dequeue_releases_capacity_for_next_task() -> None:
    queue = _InMemoryQueue(max_depth=1)
    await queue.enqueue(_task(1))

    with pytest.raises(QueueBackpressureError):
        await queue.enqueue(_task(2))

    assert await queue.dequeue() is not None
    await queue.enqueue(_task(2))
    assert await queue.queue_depth() == 1


@pytest.mark.asyncio
async def test_empty_queue_dequeue_is_non_blocking() -> None:
    queue = _InMemoryQueue(max_depth=1)
    result = await asyncio.wait_for(queue.dequeue(timeout=5), timeout=0.2)
    assert result is None
