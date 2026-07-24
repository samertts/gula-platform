from __future__ import annotations

import pytest
from app.kernel.event_bus.events import Event
from app.kernel.event_bus.retry_queue import RetryEntry, RetryQueue


class TestRetryQueue:
    def test_enqueue_and_dequeue_ready(self):
        rq = RetryQueue()
        event = Event(name="retry.event", data={"key": "value"})
        entry = RetryEntry(event=event)
        rq.enqueue(entry)
        entry.next_retry_at = 0.0
        ready = rq.dequeue_ready()
        assert len(ready) == 1

    def test_retry_count(self):
        rq = RetryQueue()
        event = Event(name="test", data={})
        entry = RetryEntry(event=event)
        rq.enqueue(entry)
        assert rq.retry_count(event.id) == 0
