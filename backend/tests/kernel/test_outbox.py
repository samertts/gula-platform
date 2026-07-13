from __future__ import annotations

import pytest

from backend.app.kernel.event_bus.outbox import OutboxMessage, OutboxPattern


class TestOutboxPattern:
    def test_enqueue_and_dequeue(self):
        outbox = OutboxPattern()
        msg = OutboxMessage(id="m1", event_name="test.event", payload={"k": "v"})
        outbox.enqueue(msg)
        assert len(outbox.list_pending()) == 1
        dequeued = outbox.dequeue()
        assert dequeued is not None
        assert dequeued.id == "m1"
        outbox.mark_completed("m1")

    def test_list_pending(self):
        outbox = OutboxPattern()
        outbox.enqueue(OutboxMessage(id="m1", event_name="test", payload={}))
        outbox.enqueue(OutboxMessage(id="m2", event_name="test", payload={}))
        assert len(outbox.list_pending()) == 2
        outbox.dequeue()
        assert len(outbox.list_pending()) == 1
