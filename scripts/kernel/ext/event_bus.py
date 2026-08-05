"""GULA-KERNEL-EXT-001 Phase 5 — Enterprise Event Bus.

AI-operational event bus for loose coupling between Kernel engines and
extensions. This is the AI-operational bus ONLY (documented boundary from
the domain outbox pattern in backend/app/outbox/). Per 16_EVENT_CONSTITUTION:
at-least-once delivery semantics, idempotent handlers, failed handlers do
not block other handlers, ordering preserved per publisher, event replay
for recovery. In-memory + persisted journal; no I/O at import time.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core import utcnow

EVENT_JOURNAL = ".ai/core/events/"

EVENT_KINDS = ("domain", "integration", "system")
EVENT_PRIORITIES = ("low", "normal", "high", "critical")

HandlerFn = Callable[[dict[str, Any]], None]


class EventBusError(Exception):
    """Raised for invalid event-bus inputs."""


@dataclass
class Event:
    """One event on the AI-operational bus."""

    id: str
    name: str
    publisher: str
    payload: dict[str, Any] = field(default_factory=dict)
    kind: str = "system"
    priority: str = "normal"
    emitted_at: str = field(default_factory=utcnow)

    def __post_init__(self) -> None:
        if not self.id.startswith("EVT-"):
            raise EventBusError(f"event id must start with EVT-: {self.id!r}")
        if not self.name:
            raise EventBusError("event name is required")
        if self.kind not in EVENT_KINDS:
            raise EventBusError(f"unknown event kind: {self.kind!r}")
        if self.priority not in EVENT_PRIORITIES:
            raise EventBusError(f"unknown priority: {self.priority!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "publisher": self.publisher,
            "payload": self.payload,
            "kind": self.kind,
            "priority": self.priority,
            "emitted_at": self.emitted_at,
        }


@dataclass
class Delivery:
    """Audit record of one handler delivery attempt."""

    event_id: str
    handler: str
    status: str
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"event_id": self.event_id, "handler": self.handler, "status": self.status, "detail": self.detail}


class EventBus:
    """Decoupled publish/subscribe bus with audit and replay."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[tuple[str, HandlerFn]]] = {}
        self._events: list[Event] = []
        self._deliveries: list[Delivery] = []
        self._seen: set[str] = set()

    def subscribe(self, event_name: str, handler_name: str, handler: HandlerFn) -> None:
        """Register a handler; '*' subscribes to every event."""
        self._handlers.setdefault(event_name, []).append((handler_name, handler))

    def publish(self, event: Event) -> list[Delivery]:
        """Route event to matching handlers; deliver once per event id."""
        if event.id in self._seen:
            return []
        self._seen.add(event.id)
        self._events.append(event)
        deliveries: list[Delivery] = []
        for handler_name, handler in self._handlers.get(event.name, []) + self._handlers.get("*", []):
            try:
                handler(event.to_dict())
                deliveries.append(Delivery(event.id, handler_name, "delivered"))
            except Exception as exc:
                deliveries.append(Delivery(event.id, handler_name, "failed", str(exc)))
        self._deliveries.extend(deliveries)
        return deliveries

    def replay(self, name: str | None = None) -> list[Event]:
        """Replay events (optionally filtered by name) for recovery."""
        events = [e for e in self._events if name is None or e.name == name]
        for event in events:
            self._seen.discard(event.id)
            self.publish(event)
        return events

    def events(self, name: str | None = None) -> list[Event]:
        if name is None:
            return list(self._events)
        return [e for e in self._events if e.name == name]

    def deliveries(self, event_id: str | None = None) -> list[Delivery]:
        if event_id is None:
            return list(self._deliveries)
        return [d for d in self._deliveries if d.event_id == event_id]

    def failures(self) -> list[Delivery]:
        return [d for d in self._deliveries if d.status == "failed"]

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "events": [e.to_dict() for e in self._events],
            "deliveries": [d.to_dict() for d in self._deliveries],
        }

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.snapshot(), indent=2) + "\n", encoding="utf-8")
        return path
