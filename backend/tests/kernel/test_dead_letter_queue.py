from __future__ import annotations

import pytest
from app.kernel.event_bus.dead_letter_queue import DeadLetterEntry, DeadLetterQueue
from app.kernel.event_bus.events import Event


class TestDeadLetterQueue:
    def test_send_and_replay(self):
        dlq = DeadLetterQueue()
        event = Event(name="failed.event", data={"error": "test"})
        entry = DeadLetterEntry(event=event, reason="test failure")
        dlq.send(entry)
        assert len(dlq.list_all()) == 1
        replayed = dlq.replay(event.id)
        assert replayed is not None
        assert len(dlq.list_all()) == 0

    def test_replay_nonexistent(self):
        dlq = DeadLetterQueue()
        assert dlq.replay("nonexistent") is None
