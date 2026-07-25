from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.kernel.event_bus.events import Event
from app.kernel.event_bus.store import EventStore as KernelEventStore

logger = logging.getLogger("gula.health_data.event_store")


@dataclass
class StoredEvent:
    event_id: str
    event_name: str
    aggregate_id: str
    aggregate_type: str
    version: int
    data: dict[str, Any]
    metadata: dict[str, Any]
    timestamp: datetime
    correlation_id: str = ""
    causation_id: str = ""
    tenant_id: str = ""


class HealthEventStore:
    def __init__(self, kernel_store: KernelEventStore | None = None):
        self._kernel_store = kernel_store
        self._events: dict[str, StoredEvent] = {}
        self._by_aggregate: dict[str, list[str]] = {}
        self._by_name: dict[str, list[str]] = {}
        self._stream: list[str] = []

    def append(
        self,
        aggregate_id: str,
        aggregate_type: str,
        event_name: str,
        data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        correlation_id: str = "",
        causation_id: str = "",
        tenant_id: str = "",
    ) -> StoredEvent:
        event_id = str(uuid.uuid4())
        version = len(self._by_aggregate.get(aggregate_id, [])) + 1

        stored = StoredEvent(
            event_id=event_id,
            event_name=event_name,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            version=version,
            data=data,
            metadata=metadata or {},
            timestamp=datetime.now(UTC),
            correlation_id=correlation_id,
            causation_id=causation_id,
            tenant_id=tenant_id,
        )
        self._events[event_id] = stored
        self._by_aggregate.setdefault(aggregate_id, []).append(event_id)
        self._by_name.setdefault(event_name, []).append(event_id)
        self._stream.append(event_id)

        if self._kernel_store:
            kernel_event = Event(
                name=event_name,
                data=data,
                version=version,
                id=event_id,
                correlation_id=correlation_id,
                tenant_id=tenant_id,
            )
            self._kernel_store.save(kernel_event)

        logger.debug(
            "Event appended: %s for %s/%s v%d", event_name, aggregate_type, aggregate_id, version
        )
        return stored

    def get(self, event_id: str) -> StoredEvent | None:
        return self._events.get(event_id)

    def replay_aggregate(self, aggregate_id: str) -> list[StoredEvent]:
        event_ids = self._by_aggregate.get(aggregate_id, [])
        return [self._events[eid] for eid in event_ids if eid in self._events]

    def replay_by_name(self, event_name: str) -> list[StoredEvent]:
        event_ids = self._by_name.get(event_name, [])
        return [self._events[eid] for eid in event_ids if eid in self._events]

    def replay_by_time_range(self, start: datetime, end: datetime) -> list[StoredEvent]:
        return [e for e in self._events.values() if start <= e.timestamp <= end]

    def replay_all(self, after_version: int = 0) -> list[StoredEvent]:
        return list(self._events.values())

    def count(self) -> int:
        return len(self._events)

    def get_stream_summary(self) -> dict[str, Any]:
        return {
            "total_events": len(self._events),
            "total_aggregates": len(self._by_aggregate),
            "event_types": {name: len(ids) for name, ids in self._by_name.items()},
            "stream_length": len(self._stream),
        }
