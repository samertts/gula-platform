from __future__ import annotations

import pytest

from backend.app.kernel.event_bus.inbox import InboxMessage, InboxPattern


class TestInboxPattern:
    def test_receive_and_process(self):
        inbox = InboxPattern()
        msg = InboxMessage(id="m1", event_name="test.event", payload={"k": "v"}, source="test")
        inbox.receive(msg)
        assert not inbox.has_been_processed("m1")
        inbox.mark_processed("m1")
        assert inbox.has_been_processed("m1")

    def test_duplicate_detection(self):
        inbox = InboxPattern()
        msg = InboxMessage(id="m1", event_name="test", payload={}, source="src")
        inbox.receive(msg)
        inbox.mark_processed("m1")
        assert inbox.has_been_processed("m1")
