"""Synthetic offline event path for released laboratory results.

The pipeline reuses the existing store-forward engine and clinical conflict
resolver. Clinical conflicts are never auto-resolved, and replay is idempotent.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime

from app._compat import UTC
from app.integration.fhir_r4_exchange import InMemoryAuditRecorder, _safe_audit_resource_id
from app.integration.offline import ConflictResolver, OfflineQueueEntry, StoreForwardEngine
from app.lims.events import LIMSEvent, ResultValidated


@dataclass(frozen=True, slots=True)
class PipelineSummary:
    delivered: tuple[str, ...]
    duplicates: tuple[str, ...]
    conflicts: tuple[str, ...]
    queue_status: dict[str, int]


class SyntheticLabEventPipeline:
    """Bounded in-memory event path; no database or external broker is used."""

    def __init__(self) -> None:
        self.store_forward = StoreForwardEngine()
        self.conflict_resolver = ConflictResolver(strategy="last_write_wins")
        self.audit = InMemoryAuditRecorder()
        self._processed: set[str] = set()

    def publish(self, event: LIMSEvent) -> bool:
        """Enqueue a synthetic LIMS event; duplicate fingerprints are suppressed."""
        if not event.event_type.startswith("lims."):
            raise ValueError("only LIMS events can be published")
        entry = OfflineQueueEntry(
            id=f"{event.aggregate_id}-{event.event_type}",
            entity_type="Observation",
            entity_id=event.aggregate_id,
            action=event.event_type,
            payload={
                "event_type": event.event_type,
                "aggregate_id": event.aggregate_id,
                "version": int(event.payload.get("version", 1)),
            },
            timestamp=time.time(),
        )
        return self.store_forward.enqueue(entry)

    def process(self) -> PipelineSummary:
        """Deliver pending events once and fail closed on clinical conflicts."""
        delivered: list[str] = []
        duplicates: list[str] = []
        conflicts: list[str] = []
        for entry in self.store_forward.dequeue(50):
            safe_id = _safe_audit_resource_id(entry.id)
            if entry.id in self._processed:
                self.store_forward.mark_success(entry.id)
                duplicates.append(entry.id)
                self.audit.record(
                    action="lab_slice.event",
                    outcome="duplicate",
                    resource_type="Observation",
                    resource_id=safe_id,
                )
                continue

            version = int(entry.payload.get("version", 1))
            if version <= 0:
                resolution = self.conflict_resolver.resolve(
                    local={"status": "pending"},
                    remote=entry.payload,
                    version_local=version,
                    version_remote=version,
                    entity_type=entry.entity_type,
                )
                self.store_forward.mark_failed(entry.id, str(resolution.get("reason")))
                conflicts.append(entry.id)
                self.audit.record(
                    action="lab_slice.event",
                    outcome="quarantined",
                    resource_type="Observation",
                    resource_id=safe_id,
                )
                continue

            self.store_forward.mark_success(entry.id)
            self._processed.add(entry.id)
            delivered.append(entry.id)
            self.audit.record(
                action="lab_slice.event",
                outcome="delivered",
                resource_type="Observation",
                resource_id=safe_id,
            )

        return PipelineSummary(
            delivered=tuple(delivered),
            duplicates=tuple(duplicates),
            conflicts=tuple(conflicts),
            queue_status=self.store_forward.queue_size(),
        )

    @staticmethod
    def released_event(result_id: str, version: int = 1) -> LIMSEvent:
        """Create the canonical LIMS result-validated event shape."""
        return LIMSEvent(
            event_type=ResultValidated.event_type,
            aggregate_id=result_id,
            aggregate_type="Result",
            payload={"version": version},
            timestamp=datetime.now(UTC).isoformat(),
        )
