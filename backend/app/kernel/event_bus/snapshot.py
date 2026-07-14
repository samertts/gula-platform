from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from backend.app.kernel.event_bus.events import Event

logger = logging.getLogger("gula.kernel.event_bus.snapshot")


@dataclass
class Snapshot:
    id: str = ""
    aggregate_type: str = ""
    aggregate_id: str = ""
    state: dict[str, Any] = field(default_factory=dict)
    version: int = 1
    last_event_id: str = ""
    last_event_name: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = time.time()


class SnapshotEngine:
    def __init__(self):
        self._snapshots: dict[str, list[Snapshot]] = {}

    def save(self, snapshot: Snapshot) -> None:
        key = f"{snapshot.aggregate_type}:{snapshot.aggregate_id}"
        if key not in self._snapshots:
            self._snapshots[key] = []
        self._snapshots[key].append(snapshot)
        self._snapshots[key].sort(key=lambda s: s.version, reverse=True)
        logger.debug(
            "Snapshot saved for %s/%s v%d",
            snapshot.aggregate_type,
            snapshot.aggregate_id,
            snapshot.version,
        )

    def load_latest(
        self, aggregate_type: str, aggregate_id: str
    ) -> Snapshot | None:
        key = f"{aggregate_type}:{aggregate_id}"
        snapshots = self._snapshots.get(key, [])
        return snapshots[0] if snapshots else None

    def load_at_version(
        self, aggregate_type: str, aggregate_id: str, version: int
    ) -> Snapshot | None:
        key = f"{aggregate_type}:{aggregate_id}"
        for snap in self._snapshots.get(key, []):
            if snap.version == version:
                return snap
        return None

    def list_versions(
        self, aggregate_type: str, aggregate_id: str
    ) -> list[Snapshot]:
        key = f"{aggregate_type}:{aggregate_id}"
        return list(self._snapshots.get(key, []))

    def rebuild_from_events(
        self,
        aggregate_type: str,
        aggregate_id: str,
        events: list[Event],
        apply_fn: Any,
        initial_state: dict[str, Any] | None = None,
    ) -> Snapshot:
        state = dict(initial_state or {})
        last_event_id = ""
        last_event_name = ""
        version = 0

        for event in events:
            state = apply_fn(state, event)
            last_event_id = event.id
            last_event_name = event.name
            version += 1

        snapshot = Snapshot(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            state=state,
            version=version,
            last_event_id=last_event_id,
            last_event_name=last_event_name,
        )
        self.save(snapshot)
        logger.info(
            "Snapshot rebuilt for %s/%s from %d events",
            aggregate_type,
            aggregate_id,
            len(events),
        )
        return snapshot

    def purge(self, aggregate_type: str, aggregate_id: str) -> int:
        key = f"{aggregate_type}:{aggregate_id}"
        count = len(self._snapshots.get(key, []))
        self._snapshots.pop(key, None)
        return count

    def count(self) -> int:
        return sum(len(v) for v in self._snapshots.values())
