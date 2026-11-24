"""Outbox Event model — Transactional Outbox Pattern.

Events are written to this table inside the same DB transaction as the
business operation that triggers them.  A background worker reads pending
events and delivers them (notifications, webhooks, sync signals, etc.).

This guarantees at-least-once delivery even when:
  - The message broker is temporarily unavailable
  - The application crashes between the operation and the notification
  - The network drops mid-flight

Status lifecycle:
    pending → processing → done
                ↓
              failed  (retried up to MAX_ATTEMPTS times)
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint

from app._compat import UTC

from ..database import Base

MAX_ATTEMPTS = 5  # after this, the event stays in 'failed' and alerts ops


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_outbox_events_event_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Canonical C09 fields. Defaults keep every legacy call site working while
    # making the durable row attributable, correlatable and idempotent.
    event_id = Column(
        String(120), nullable=False, default=lambda: f"legacy-{uuid.uuid4()}"
    )
    event_type = Column(String(100), nullable=False, index=True)
    schema_version = Column(Integer, nullable=False, default=1)
    source_service = Column(String(80), nullable=False, default="gula-outbox")
    tenant_id = Column(String(120), nullable=False, default="system", index=True)
    actor_id = Column(String(160), nullable=False, default="system")
    entity_id = Column(String(160), nullable=False, default="unknown")
    correlation_id = Column(
        String(160), nullable=False, default="legacy-outbox", index=True
    )
    idempotency_key = Column(String(200), nullable=False, default="legacy-outbox")
    sequence = Column(Integer, nullable=True)
    aggregate_type = Column(String(100), nullable=True)  # e.g. "order", "result"
    aggregate_id = Column(Integer, nullable=True, index=True)
    payload = Column(Text, nullable=False)  # JSON string
    status = Column(String(20), nullable=False, default="pending")
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)
