"""Notification service (CMD-024).

Provides the write- and read-side primitives the API and background workers
use to deliver durable messages to NHOP users. Writes are flushed but not
committed — the caller owns the transaction so a notification is created
atomically with the business event that triggered it (e.g. critical result
insertion).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..models.notification import (
    Notification,
    NotificationPriority,
    NotificationType,
)


def send_notification(
    db: Session,
    *,
    recipient_id: str,
    recipient_role: str,
    type: NotificationType,
    title: str,
    body: str,
    priority: NotificationPriority = NotificationPriority.medium,
    related_type: Optional[str] = None,
    related_id: Optional[str] = None,
) -> Notification:
    """Persist a notification for ``recipient_id``.

    The row is flushed so its ``id`` is available, but NOT committed: the
    caller decides when to commit, keeping the notification tied to the
    surrounding business transaction.
    """
    row = Notification(
        recipient_id=recipient_id,
        recipient_role=recipient_role,
        type=type,
        title=title,
        body=body,
        priority=priority,
        related_type=related_type,
        related_id=related_id,
    )
    db.add(row)
    db.flush()
    return row


def get_unread(
    db: Session,
    *,
    user_id: str,
    limit: int = 100,
) -> list[Notification]:
    """Return the user's unread notifications, newest-first."""
    return (
        db.query(Notification)
          .filter(
              Notification.recipient_id == user_id,
              Notification.is_read.is_(False),
          )
          .order_by(desc(Notification.created_at))
          .limit(limit)
          .all()
    )


def unread_count(db: Session, *, user_id: str) -> int:
    """Count of unread notifications for ``user_id``."""
    return (
        db.query(Notification)
          .filter(
              Notification.recipient_id == user_id,
              Notification.is_read.is_(False),
          )
          .count()
    )


def list_for_user(
    db: Session,
    *,
    user_id: str,
    skip: int = 0,
    limit: int = 20,
    unread_only: bool = False,
) -> tuple[int, list[Notification]]:
    """Paginated listing for a given user. Returns ``(total, rows)``."""
    query = db.query(Notification).filter(Notification.recipient_id == user_id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))

    total = query.count()
    rows = (
        query.order_by(desc(Notification.created_at))
             .offset(skip)
             .limit(limit)
             .all()
    )
    return total, rows


def mark_read(
    db: Session,
    *,
    notification_id: UUID,
    user_id: str,
) -> Optional[Notification]:
    """Mark a single notification as read.

    Returns the updated row, or ``None`` if the notification does not belong
    to ``user_id``. The row is flushed but not committed.
    """
    row = (
        db.query(Notification)
          .filter(
              Notification.id == notification_id,
              Notification.recipient_id == user_id,
          )
          .first()
    )
    if row is None:
        return None
    if not row.is_read:
        row.is_read = True
        row.read_at = datetime.now(timezone.utc)
        db.flush()
    return row
