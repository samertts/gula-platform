from __future__ import annotations

import pytest

from backend.app.kernel.event_bus.events import Event
from backend.app.kernel.event_bus.store import EventStore


class TestEventStore:
    def test_save_and_get(self):
        store = EventStore()
        event = Event(name="stored.event", data={"k": "v"})
        store.save(event)
        assert store.get(event.id) is not None
        assert len(store.list_by_name("stored.event")) == 1
        assert store.count() == 1

    def test_list_all(self):
        store = EventStore()
        store.save(Event(name="a", data={}))
        store.save(Event(name="b", data={}))
        assert len(store.list_all()) == 2
