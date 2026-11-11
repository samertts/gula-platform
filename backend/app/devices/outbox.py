"""Tenant-scoped transactional outbox for safe device gateway envelopes.

The current dispatcher is deliberately simulation-only. It exercises durable queue
semantics without opening a socket or sending a clinical payload to a real device.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC

from .models import DEVICE_OUTBOX_MAX_ATTEMPTS, DeviceOutboxMessage
from .schemas import _ensure_secret_free


_ACTIVE_STATUSES = ("pending", "retry", "processing")


def utc_now() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _retry_delay(attempts: int) -> timedelta:
    return timedelta(seconds=min(900, 10 * (2 ** max(attempts - 1, 0))))


def enqueue_message(
    db: Session,
    *,
    lab_id: int,
    event_type: str,
    payload_safe: dict,
    idempotency_key: str,
    gateway_ref: str | None = None,
    aggregate_type: str = "device_event",
    aggregate_id: int | None = None,
    correlation_id: str | None = None,
) -> DeviceOutboxMessage:
    """Insert or return an idempotent safe envelope within the current transaction."""
    if not idempotency_key or len(idempotency_key) > 160:
        raise ValueError("idempotency_key is required and must be at most 160 characters")
    _ensure_secret_free(payload_safe)
    existing = (
        db.query(DeviceOutboxMessage)
        .filter(
            DeviceOutboxMessage.lab_id == lab_id,
            DeviceOutboxMessage.idempotency_key == idempotency_key,
        )
        .first()
    )
    if existing is not None:
        same_envelope = (
            existing.event_type == event_type
            and existing.gateway_ref == gateway_ref
            and existing.payload_safe == payload_safe
        )
        if not same_envelope:
            raise ValueError("idempotency key is already used for a different device envelope")
        return existing

    message = DeviceOutboxMessage(
        lab_id=lab_id,
        gateway_ref=gateway_ref,
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        idempotency_key=idempotency_key,
        correlation_id=correlation_id or idempotency_key,
        payload_safe=payload_safe,
        status="pending",
        attempts=0,
        max_attempts=DEVICE_OUTBOX_MAX_ATTEMPTS,
        next_attempt_at=utc_now(),
        simulation_only=True,
    )
    db.add(message)
    return message


def get_message(db: Session, lab_id: int, message_id: int) -> DeviceOutboxMessage | None:
    return (
        db.query(DeviceOutboxMessage)
        .filter(DeviceOutboxMessage.lab_id == lab_id, DeviceOutboxMessage.id == message_id)
        .first()
    )


def list_messages(
    db: Session,
    lab_id: int,
    *,
    status: str | None = None,
    gateway_ref: str | None = None,
    limit: int = 100,
) -> tuple[int, list[DeviceOutboxMessage]]:
    query = db.query(DeviceOutboxMessage).filter(DeviceOutboxMessage.lab_id == lab_id)
    if status:
        query = query.filter(DeviceOutboxMessage.status == status)
    if gateway_ref:
        query = query.filter(DeviceOutboxMessage.gateway_ref == gateway_ref)
    total = query.count()
    rows = query.order_by(DeviceOutboxMessage.created_at.desc()).limit(limit).all()
    return total, rows


def summarize(db: Session, lab_id: int, *, now: datetime | None = None) -> dict:
    now = now or utc_now()
    counts = {
        row.status: int(row.count)
        for row in (
            db.query(DeviceOutboxMessage.status, func.count(DeviceOutboxMessage.id).label("count"))
            .filter(DeviceOutboxMessage.lab_id == lab_id)
            .group_by(DeviceOutboxMessage.status)
            .all()
        )
    }
    oldest = (
        db.query(DeviceOutboxMessage.created_at)
        .filter(
            DeviceOutboxMessage.lab_id == lab_id,
            DeviceOutboxMessage.status.in_(_ACTIVE_STATUSES),
        )
        .order_by(DeviceOutboxMessage.created_at.asc())
        .first()
    )
    oldest_age = 0.0
    if oldest and oldest[0]:
        oldest_age = max(0.0, (now - _aware(oldest[0])).total_seconds())
    return {
        "pending_count": counts.get("pending", 0),
        "processing_count": counts.get("processing", 0),
        "retry_count": counts.get("retry", 0),
        "delivered_count": counts.get("delivered", 0),
        "dead_letter_count": counts.get("dead_letter", 0),
        "oldest_age_seconds": oldest_age,
    }


def recover_stale_processing(
    db: Session,
    lab_id: int,
    *,
    now: datetime | None = None,
    lease_seconds: int = 300,
) -> int:
    """Return abandoned processing messages to the retryable state."""
    now = now or utc_now()
    cutoff = now - timedelta(seconds=lease_seconds)
    stale = (
        db.query(DeviceOutboxMessage)
        .filter(
            DeviceOutboxMessage.lab_id == lab_id,
            DeviceOutboxMessage.status == "processing",
            DeviceOutboxMessage.locked_at.is_not(None),
            DeviceOutboxMessage.locked_at <= cutoff,
        )
        .all()
    )
    for message in stale:
        message.status = "retry"
        message.locked_at = None
        message.next_attempt_at = now
        message.last_error = "processing lease expired; message returned to retry queue"
    return len(stale)


def mark_failure(
    db: Session,
    message: DeviceOutboxMessage,
    error: str,
    *,
    now: datetime | None = None,
) -> DeviceOutboxMessage:
    now = now or utc_now()
    message.last_error = error[:500]
    message.locked_at = None
    if message.attempts >= message.max_attempts:
        message.status = "dead_letter"
        message.next_attempt_at = now
    else:
        message.status = "retry"
        message.next_attempt_at = now + _retry_delay(message.attempts)
    return message


def process_batch(
    db: Session,
    lab_id: int,
    *,
    limit: int = 50,
    now: datetime | None = None,
    dispatcher: Callable[[DeviceOutboxMessage], None] | None = None,
) -> dict:
    """Claim and process due messages; default dispatcher only simulates delivery."""
    now = now or utc_now()
    recovered = recover_stale_processing(db, lab_id, now=now)
    due = (
        db.query(DeviceOutboxMessage)
        .filter(
            DeviceOutboxMessage.lab_id == lab_id,
            DeviceOutboxMessage.status.in_(("pending", "retry")),
            DeviceOutboxMessage.next_attempt_at <= now,
        )
        .order_by(DeviceOutboxMessage.created_at.asc())
        .limit(limit)
        .with_for_update(skip_locked=True)
        .all()
    )
    processed = delivered = retried = dead_letter = 0
    for message in due:
        message.status = "processing"
        message.attempts += 1
        message.locked_at = now
        db.flush()
        try:
            if dispatcher is not None:
                dispatcher(message)
            message.status = "delivered"
            message.delivered_at = now
            message.locked_at = None
            message.last_error = None
            message.next_attempt_at = now
            delivered += 1
        except Exception as exc:  # pragma: no cover - exercised by focused tests
            mark_failure(db, message, str(exc), now=now)
            if message.status == "dead_letter":
                dead_letter += 1
            else:
                retried += 1
        processed += 1
    db.commit()
    return {
        "processed": processed,
        "recovered": recovered,
        "delivered": delivered,
        "retried": retried,
        "dead_letter": dead_letter,
        "simulation_only": True,
    }
