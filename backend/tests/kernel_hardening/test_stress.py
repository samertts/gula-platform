from __future__ import annotations

import asyncio
import time

import pytest
from app.kernel import Kernel
from app.kernel.background.distributed_locks import DistributedLockManager
from app.kernel.background.priority_queue import PriorityQueue, PriorityTask
from app.kernel.background.task_queue import Task, TaskQueue
from app.kernel.event_bus.bus import EventBus
from app.kernel.event_bus.dead_letter_queue import DeadLetterEntry, DeadLetterQueue
from app.kernel.event_bus.events import Event
from app.kernel.event_bus.outbox import OutboxMessage, OutboxPattern
from app.kernel.event_bus.retry_queue import RetryEntry, RetryQueue
from app.kernel.event_bus.store import EventStore
from app.kernel.gateway.rate_limiting import RateLimiter

pytestmark = [
    pytest.mark.kernel,
    pytest.mark.stress,
    pytest.mark.slow,
]


class TestStressEventBus:
    def test_10k_events(self, kernel: Kernel):
        eb = EventBus(kernel)
        count = 0

        def handler(event):
            nonlocal count
            count += 1

        eb.subscribe("stress.test", handler)
        start = time.monotonic()
        for i in range(10_000):
            eb.publish(Event(name="stress.test", data={"i": i}))
        elapsed = time.monotonic() - start
        assert count == 10_000
        assert elapsed < 5.0, f"10k events took {elapsed:.2f}s (limit 5s)"

    def test_100k_events(self, kernel: Kernel):
        eb = EventBus(kernel)
        count = 0

        def handler(event):
            nonlocal count
            count += 1

        eb.subscribe("stress.big", handler)
        start = time.monotonic()
        for i in range(100_000):
            eb.publish(Event(name="stress.big", data={"i": i}))
        elapsed = time.monotonic() - start
        assert count == 100_000
        assert elapsed < 15.0, f"100k events took {elapsed:.2f}s (limit 15s)"

    async def test_concurrent_publishers(self, kernel: Kernel):
        eb = EventBus(kernel)
        count = 0

        def handler(event):
            nonlocal count
            count += 1

        eb.subscribe("concurrent.test", handler)

        async def publish_batch(n: int):
            for i in range(n):
                eb.publish(Event(name="concurrent.test", data={"i": i}))

        start = time.monotonic()
        await asyncio.gather(*[publish_batch(100) for _ in range(10)])
        elapsed = time.monotonic() - start
        assert count == 1000
        assert elapsed < 3.0, f"Concurrent publish took {elapsed:.2f}s (limit 3s)"


class TestStressEventStore:
    def test_10k_saves(self):
        store = EventStore()
        start = time.monotonic()
        for i in range(10_000):
            store.save(Event(name="store.test", data={"i": i}))
        elapsed = time.monotonic() - start
        assert store.count() == 10_000
        assert elapsed < 3.0, f"10k saves took {elapsed:.2f}s (limit 3s)"


class TestStressOutbox:
    def test_10k_messages(self):
        outbox = OutboxPattern()
        start = time.monotonic()
        for i in range(10_000):
            outbox.enqueue(OutboxMessage(id=f"m{i}", event_name="test", payload={"i": i}))
        elapsed = time.monotonic() - start
        assert len(outbox.list_pending()) == 10_000
        assert elapsed < 3.0, f"10k enqueue took {elapsed:.2f}s (limit 3s)"


class TestStressTaskQueue:
    def test_10k_tasks(self):
        tq = TaskQueue()
        start = time.monotonic()
        for i in range(10_000):
            tq.enqueue(Task(id=f"t{i}", name="stress", handler=lambda: None))
        elapsed = time.monotonic() - start
        assert tq.size() == 10_000
        assert elapsed < 2.0, f"10k enqueue took {elapsed:.2f}s (limit 2s)"

    def test_priority_ordering_large_set(self):
        pq = PriorityQueue()
        import random
        tasks = [PriorityTask(priority=random.randint(0, 100), name=f"t{i}") for i in range(1000)]
        start = time.monotonic()
        for t in tasks:
            pq.push(t)
        ordered = [pq.pop().name for _ in range(1000)]
        elapsed = time.monotonic() - start
        assert len(ordered) == 1000
        assert elapsed < 2.0, f"1000 push/pop took {elapsed:.2f}s (limit 2s)"


class TestStressRateLimiter:
    def test_high_frequency_checks(self):
        rl = RateLimiter()
        rl.set_limit("key", 1_000_000, 60)
        start = time.monotonic()
        for _ in range(100_000):
            rl.check("key")
        elapsed = time.monotonic() - start
        assert elapsed < 3.0, f"100k checks took {elapsed:.2f}s (limit 3s)"


class TestStressLocks:
    def test_contention(self):
        dlm = DistributedLockManager()
        start = time.monotonic()
        for i in range(1000):
            assert dlm.acquire(f"res_{i}", f"worker_{i % 10}")
        elapsed = time.monotonic() - start
        assert elapsed < 3.0, f"1000 lock acquires took {elapsed:.2f}s (limit 3s)"
