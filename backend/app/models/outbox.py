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

from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, String, Text

from app._compat import UTC

from ..database import Base

MAX_ATTEMPTS = 5  # after this, the event stays in 'failed' and alerts ops


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    __table_args__ = (
        Index("ix_outbox_events_status_next_attempt_created", "status", "next_attempt_at", "created_at"),
        Index("ix_outbox_events_type_status", "event_type", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(100), nullable=False, index=True)
    lab_id = Column(Integer, nullable=True, index=True)
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
    next_attempt_at = Column(DateTime(timezone=True), nullable=True, index=True)
    lease_until = Column(DateTime(timezone=True), nullable=True, index=True)
    payload_hash = Column(String(64), nullable=True, index=True)
    dead_letter_reason = Column(Text, nullable=True)
    replayed_by = Column(String(160), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
