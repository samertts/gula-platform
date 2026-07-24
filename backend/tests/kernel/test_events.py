from __future__ import annotations

import pytest
from app.kernel.event_bus.dead_letter_queue import DeadLetterEntry
from app.kernel.event_bus.events import Event
from app.kernel.event_bus.inbox import InboxMessage
from app.kernel.event_bus.outbox import OutboxMessage
from app.kernel.event_bus.retry_queue import RetryEntry


class TestEventDefaults:
    def test_event_defaults(self):
        event = Event(name="test", data={"k": "v"})
        assert event.id != ""
        assert event.timestamp > 0
        assert event.version == 1
        assert event.source == ""
        assert event.correlation_id == ""
        assert event.tenant_id == ""

    def test_outbox_message_defaults(self):
        msg = OutboxMessage(id="m1", event_name="test", payload={"k": "v"})
        assert msg.status == "pending"
        assert msg.retry_count == 0

    def test_inbox_message_defaults(self):
        msg = InboxMessage(id="m1", event_name="test", payload={"k": "v"}, source="src")
        assert msg.status == "received"

    def test_dead_letter_entry_defaults(self):
        event = Event(name="test", data={"k": "v"})
        entry = DeadLetterEntry(event=event, reason="fail")
        assert entry.failed_at > 0
        assert entry.retry_count == 0

    def test_retry_entry_defaults(self):
        event = Event(name="test", data={"k": "v"})
        entry = RetryEntry(event=event)
        assert entry.retry_count == 0
        assert entry.max_retries == 3


class TestEventReplay:
    def test_replay(self, kernel, event_bus):
        import asyncio
        received = []

        def handler(event):
            received.append(event)

        event_bus.subscribe("test.event", handler)
        event = Event(name="test.event", data={"k": "v"})
        event_bus.publish(event)
        event_bus.replay.replay_event(event)
        assert len(received) == 2
