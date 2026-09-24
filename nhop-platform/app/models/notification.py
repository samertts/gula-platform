"""Notification records for NHOP users.

Notifications are durable messages delivered to a recipient (citizen, lab
staff, ministry officer). They are created by background processes — e.g.
critical test result alerts, outbreak detection, QC failures — and read via
the notifications API. Once delivered they may be marked read, but rows are
never hard-deleted from application code so that audit trails remain intact.
"""
from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Enum, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class NotificationType(enum.StrEnum):
    critical_result = "critical_result"
    abnormal_result = "abnormal_result"
    reminder = "reminder"
    outbreak = "outbreak"
    qc_alert = "qc_alert"


class NotificationPriority(enum.StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_recipient_unread", "recipient_id", "is_read"),
        Index("ix_notifications_recipient_created", "recipient_id", "created_at"),
        Index("ix_notifications_type_created", "type", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    recipient_id: Mapped[str] = mapped_column(String(80), nullable=False)
    recipient_role: Mapped[str] = mapped_column(String(40), nullable=False)

    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type"),
        nullable=False,
    )
    priority: Mapped[NotificationPriority] = mapped_column(
        Enum(NotificationPriority, name="notification_priority"),
        nullable=False,
        default=NotificationPriority.medium,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(String(2000), nullable=False)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Optional deep-link back to the entity that triggered this notification
    # (e.g. test_result:<uuid>). Kept as free-form strings so we don't need a
    # polymorphic FK across many target types.
    related_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    related_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
