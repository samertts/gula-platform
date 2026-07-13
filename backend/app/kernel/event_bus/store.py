from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from backend.app.kernel.event_bus.events import Event

logger = logging.getLogger("gula.kernel.event_bus.store")


class EventStore:
    def __init__(self):
        self._events: dict[str, Event] = {}

    def save(self, event: Event) -> None:
        self._events[event.id] = event

    def get(self, event_id: str) -> Event | None:
        return self._events.get(event_id)

    def list_by_name(self, name: str) -> list[Event]:
        return [e for e in self._events.values() if e.name == name]

    def list_all(self) -> list[Event]:
        return list(self._events.values())

    def count(self) -> int:
        return len(self._events)
