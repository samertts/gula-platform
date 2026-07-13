from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.app.kernel.event_bus.events import Event

if TYPE_CHECKING:
    from backend.app.kernel.event_bus.bus import EventBus

logger = logging.getLogger("gula.kernel.event_bus.replay")


class EventReplay:
    def __init__(self, bus: EventBus):
        self.bus = bus

    def replay_event(self, event: Event) -> None:
        self.bus.publish(event)

    def replay_events(self, events: list[Event]) -> None:
        for event in events:
            self.replay_event(event)
