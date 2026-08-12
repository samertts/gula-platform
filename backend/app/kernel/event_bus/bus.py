from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from app.kernel.event_bus.dead_letter_queue import DeadLetterQueue
from app.kernel.event_bus.dispatcher import EventDispatcher
from app.kernel.event_bus.events import Event
from app.kernel.event_bus.inbox import InboxPattern
from app.kernel.event_bus.outbox import OutboxPattern
from app.kernel.event_bus.recovery import RecoveryEngine
from app.kernel.event_bus.replay import EventReplay
from app.kernel.event_bus.retry_queue import RetryQueue
from app.kernel.event_bus.snapshot import SnapshotEngine
from app.kernel.event_bus.store import EventStore
from app.kernel.event_bus.versioning import EventVersioning

if TYPE_CHECKING:
    from app.kernel import Kernel

logger = logging.getLogger("gula.kernel.event_bus")


class EventBus:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.dispatcher = EventDispatcher()
        self.store = EventStore()
        self.outbox = OutboxPattern()
        self.inbox = InboxPattern()
        self.retry_queue = RetryQueue()
        self.dead_letter_queue = DeadLetterQueue()
        self.replay = EventReplay(self)
        self.snapshot = SnapshotEngine()
        self.recovery = RecoveryEngine()
        self.versioning = EventVersioning()
        self._subscribers: dict[str, list[Callable]] = {}

    def publish(self, event: Event) -> None:
        self.store.save(event)
        self.dispatcher.dispatch(event, self._subscribers.get(event.name, []))

    def subscribe(self, event_name: str, handler: Callable) -> None:
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: Callable) -> None:
        handlers = self._subscribers.get(event_name, [])
        if handler in handlers:
            handlers.remove(handler)
