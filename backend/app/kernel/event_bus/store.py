from __future__ import annotations

import logging

from app.kernel.event_bus.events import Event

logger = logging.getLogger("gula.kernel.event_bus.store")


class EventStore:
    """In-memory event history, bounded so a long-lived bus cannot leak.

    The store is held by the process-wide kernel EventBus, so an unbounded dict
    here grows for the life of the worker. Oldest-first eviction keeps the recent
    window that replay and diagnostics actually read. See IA-013a.
    """

    DEFAULT_MAX_EVENTS = 10_000

    def __init__(self, max_events: int = DEFAULT_MAX_EVENTS):
        if max_events < 1:
            raise ValueError("max_events must be >= 1")
        self.max_events = max_events
        self._events: dict[str, Event] = {}
        self._evicted = 0

    def save(self, event: Event) -> None:
        self._events[event.id] = event
        while len(self._events) > self.max_events:
            oldest = next(iter(self._events))
            del self._events[oldest]
            if self._evicted == 0:
                logger.warning(
                    "EventStore reached its %d-event bound; evicting oldest first",
                    self.max_events,
                )
            self._evicted += 1

    @property
    def evicted_count(self) -> int:
        return self._evicted

    def get(self, event_id: str) -> Event | None:
        return self._events.get(event_id)

    def list_by_name(self, name: str) -> list[Event]:
        return [e for e in self._events.values() if e.name == name]

    def list_all(self) -> list[Event]:
        return list(self._events.values())

    def count(self) -> int:
        return len(self._events)
