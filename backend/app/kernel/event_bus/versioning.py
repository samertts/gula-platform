from __future__ import annotations

import logging

from app.kernel.event_bus.events import Event

logger = logging.getLogger("gula.kernel.event_bus.versioning")


class EventVersioning:
    def __init__(self):
        self._schemas: dict[str, dict] = {}

    def register_schema(self, event_name: str, version: int, schema: dict) -> None:
        key = f"{event_name}.v{version}"
        self._schemas[key] = schema

    def get_schema(self, event_name: str, version: int) -> dict | None:
        return self._schemas.get(f"{event_name}.v{version}")

    def migrate(self, event: Event, target_version: int) -> Event:
        if event.version == target_version:
            return event
        return Event(
            name=event.name,
            data=event.data,
            version=target_version,
            id=event.id,
            timestamp=event.timestamp,
            source=event.source,
            correlation_id=event.correlation_id,
            tenant_id=event.tenant_id,
        )
