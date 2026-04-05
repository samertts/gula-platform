"""ProcessedEvent — idempotency guard for event consumers.

Every event consumer (worker, webhook handler, stream processor) must:
  1. Check if event_id already exists in processed_events (SELECT).
  2. If yes  → skip (already processed, at-least-once semantics handled).
  3. If no   → process + INSERT processed_event in same transaction.

This prevents duplicate side-effects when the outbox worker retries
a previously-dispatched event after a crash between dispatch and ACK.

DLQ (Dead Letter Queue):
  Events that exceed MAX_DLQ_ATTEMPTS are moved to status='dlq'.
  Ops team is alerted; manual review / replay is required.
  DLQ events are NEVER retried automatically.

Usage::

    from app.models.processed_event import ProcessedEvent, is_processed, mark_processed

    # In your event handler
    def handle_order_validated(db, event_id, payload):
        if is_processed(db, event_id):
            return   # duplicate — skip silently
        # ... do the work ...
        mark_processed(db, event_id, consumer="order_validator",
                       event_type="order.validated")
        # commit happens in the caller's transaction
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Session

from ..database import Base

MAX_DLQ_ATTEMPTS = 5   # failed events beyond this threshold go to DLQ


class ProcessedEvent(Base):
    """Records every successfully processed event to prevent duplicate execution."""
    __tablename__ = "processed_events"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    event_id     = Column(String(100), nullable=False)   # outbox_events.id or external ID
    consumer     = Column(String(100), nullable=False)   # which worker processed it
    event_type   = Column(String(100), nullable=True)
    processed_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    # Extra context for debugging
    notes        = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("event_id", "consumer", name="uq_processed_event_id_consumer"),
        Index("ix_processed_events_event_id", "event_id"),
        Index("ix_processed_events_processed_at", "processed_at"),
    )


class DLQEvent(Base):
    """Dead Letter Queue — events that failed too many times."""
    __tablename__ = "dlq_events"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    original_id    = Column(Integer, nullable=True, index=True)  # outbox_events.id
    event_type     = Column(String(100), nullable=False, index=True)
    payload        = Column(Text, nullable=False)    # JSON string
    attempts       = Column(Integer, nullable=False, default=0)
    last_error     = Column(Text, nullable=True)
    consumer       = Column(String(100), nullable=True)
    created_at     = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    resolved_at    = Column(DateTime(timezone=True), nullable=True)
    resolved_by    = Column(String(100), nullable=True)
    resolution     = Column(Text, nullable=True)   # "replayed" | "discarded" | notes


# ── Helper functions ──────────────────────────────────────────────────────────

def is_processed(db: Session, event_id: str | int, consumer: str = "default") -> bool:
    """Return True if this event has already been processed by this consumer."""
    return (
        db.query(ProcessedEvent.id)
        .filter(
            ProcessedEvent.event_id == str(event_id),
            ProcessedEvent.consumer == consumer,
        )
        .first()
    ) is not None


def mark_processed(
    db: Session,
    event_id: str | int,
    consumer: str = "default",
    event_type: str | None = None,
    notes: str | None = None,
) -> ProcessedEvent:
    """
    Record this event as processed. Call inside the same transaction as the work.

    Does NOT commit — the caller's transaction handles that.
    """
    record = ProcessedEvent(
        event_id     = str(event_id),
        consumer     = consumer,
        event_type   = event_type,
        processed_at = datetime.now(timezone.utc),
        notes        = notes,
    )
    db.add(record)
    db.flush()
    return record


def move_to_dlq(
    db: Session,
    original_id: int | None,
    event_type: str,
    payload: str,
    attempts: int,
    last_error: str,
    consumer: str | None = None,
) -> DLQEvent:
    """
    Move a repeatedly-failing event to the Dead Letter Queue.

    Caller must commit. Ops alerts should be triggered after commit.
    """
    dlq_event = DLQEvent(
        original_id = original_id,
        event_type  = event_type,
        payload     = payload,
        attempts    = attempts,
        last_error  = last_error,
        consumer    = consumer,
        created_at  = datetime.now(timezone.utc),
    )
    db.add(dlq_event)
    db.flush()
    return dlq_event
