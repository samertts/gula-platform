from __future__ import annotations

import asyncio

import pytest

from backend.app.kernel import Kernel
from backend.app.kernel.event_bus.bus import EventBus
from backend.app.kernel.event_bus.events import Event


class TestEventBus:
    def test_publish_subscribe(self, kernel: Kernel, event_bus: EventBus):
        received = []

        def handler(event):
            received.append(event)

        event_bus.subscribe("test.event", handler)
        event_bus.publish(Event(name="test.event", data={"k": "v"}))
        assert len(received) == 1
        event_bus.unsubscribe("test.event", handler)
        event_bus.publish(Event(name="test.event", data={"k": "v"}))
        assert len(received) == 1

    def test_multiple_subscribers(self, kernel: Kernel, event_bus: EventBus):
        received_1 = []
        received_2 = []

        def h1(event):
            received_1.append(event)

        def h2(event):
            received_2.append(event)

        event_bus.subscribe("test.event", h1)
        event_bus.subscribe("test.event", h2)
        event_bus.publish(Event(name="test.event", data={"k": "v"}))
        assert len(received_1) == 1
        assert len(received_2) == 1
