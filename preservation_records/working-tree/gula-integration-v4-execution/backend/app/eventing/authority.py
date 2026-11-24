"""Single authoritative implementation for durable event publish and drain.

C09 target: one durable, ordered, attributable, correlation-aware outbox with
explicit acknowledgement. Legacy adapters can relax strict acknowledgement to
preserve their historical behavior, but no other module implements delivery
semantics directly.
"""
from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from pydantic import Field

from app._compat import UTC as GULA_UTC
from app.contracts.integration import IntegrationEventEnvelope
from app.core.events import events as default_bus
from app.models.outbox import MAX_ATTEMPTS, OutboxEvent

logger = logging.getLogger("gula.eventing.authority")

_BATCH_SIZE = 50


class CanonicalEventEnvelope(IntegrationEventEnvelope):
    """Integration envelope extended with aggregate identity and ordering."""

    aggregate_type: str = Field(min_length=1, max_length=100)
    aggregate_id: str = Field(min_length=1, max_length=160)
    sequence: int | None = Field(default=None, ge=0)


Dispatcher = Callable[[str, dict[str, Any]], int]


def _now() -> datetime:
    return datetime.now(GULA_UTC)


class NationalEventAuthority:
    """Durable event substrate shared by every historical event stack."""

    @staticmethod
    def validate(value: CanonicalEventEnvelope | dict[str, Any]) -> CanonicalEventEnvelope:
        if isinstance(value, CanonicalEventEnvelope):
            return value
        return CanonicalEventEnvelope.model_validate(value)

    @staticmethod
    def publish(
        db: Any,
        envelope: CanonicalEventEnvelope | dict[str, Any],
    ) -> OutboxEvent:
        """Persist a canonical event inside the caller's transaction.

        No commit is performed. Rolling back the caller's unit of work removes
        the event, preserving the atomic business-event guarantee.
        """
        event = NationalEventAuthority.validate(envelope)
        try:
            numeric_aggregate_id = (
                int(event.aggregate_id) if event.aggregate_id.isdigit() else None
            )
        except (TypeError, ValueError):
            numeric_aggregate_id = None

        row = OutboxEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            schema_version=event.schema_version,
            source_service=event.source_service,
            tenant_id=event.tenant_id,
            actor_id=event.actor_id,
            entity_id=event.entity_id,
            correlation_id=event.correlation_id,
            idempotency_key=event.idempotency_key,
            sequence=event.sequence,
            aggregate_type=event.aggregate_type,
            aggregate_id=numeric_aggregate_id,
            payload=json.dumps(event.payload, ensure_ascii=False, sort_keys=True),
            status="pending",
            attempts=0,
            created_at=_now(),
        )
        db.add(row)
        db.flush()
        return row

    @staticmethod
    def stage_inbound(db: Any, envelope: IntegrationEventEnvelope | dict[str, Any]) -> Any:
        """Stage an inbound versioned event through the durable inbox."""
        from app.integration.inbox import stage_event

        parsed = (
            envelope
            if isinstance(envelope, IntegrationEventEnvelope)
            else IntegrationEventEnvelope.model_validate(envelope)
        )
        return stage_event(db, parsed)

    @staticmethod
    def drain(
        db: Any,
        *,
        require_handler: bool = False,
        dispatcher: Dispatcher | None = None,
    ) -> dict[str, int]:
        """Dispatch one batch and acknowledge only successful deliveries.

        ``require_handler=False`` is the legacy compatibility mode. The
        canonical C09 path passes ``True`` so an event with zero subscribers is
        retried instead of being falsely acknowledged as delivered.
        """
        summary = {"processed": 0, "failed": 0, "skipped": 0}
        processed_at = _now()
        dispatch = dispatcher or (lambda name, payload: default_bus.emit(name, payload))

        batch = (
            db.query(OutboxEvent)
            .filter(
                OutboxEvent.status.in_(["pending", "failed"]),
                OutboxEvent.attempts < MAX_ATTEMPTS,
            )
            .order_by(OutboxEvent.sequence.asc(), OutboxEvent.created_at.asc(), OutboxEvent.id.asc())
            .limit(_BATCH_SIZE)
            .with_for_update(skip_locked=True)
            .all()
        )

        for row in batch:
            row.status = "processing"
            row.attempts = (row.attempts or 0) + 1
            db.flush()
            try:
                payload = json.loads(row.payload)
                delivered = dispatch(row.event_type, payload)
                if require_handler and delivered < 1:
                    raise RuntimeError(
                        f"no registered handler accepted event_type={row.event_type}"
                    )
                row.status = "done"
                row.processed_at = processed_at
                row.last_error = None
                summary["processed"] += 1
                logger.info(
                    "[EVENT-AUTHORITY] acknowledged event_id=%s type=%s handlers=%d",
                    row.event_id,
                    row.event_type,
                    delivered,
                )
            except Exception as exc:
                row.last_error = str(exc)[:500]
                row.status = "failed"
                if row.attempts >= MAX_ATTEMPTS:
                    summary["failed"] += 1
                    logger.error(
                        "[EVENT-AUTHORITY] permanently failed event_id=%s after %d attempts: %s",
                        row.event_id,
                        row.attempts,
                        exc,
                    )
                else:
                    summary["skipped"] += 1
                    logger.warning(
                        "[EVENT-AUTHORITY] attempt %d/%d failed event_id=%s: %s",
                        row.attempts,
                        MAX_ATTEMPTS,
                        row.event_id,
                        exc,
                    )
            db.flush()

        db.commit()
        return summary
