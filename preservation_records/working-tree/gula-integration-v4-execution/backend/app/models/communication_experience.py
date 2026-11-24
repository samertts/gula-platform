"""User Communication Experience ORM rows (PROGRAM-COMM-003).

Three tables power every GULA application's communication experience:

  - ``comm_notifications``: the unified user inbox. Every communication
    that is delivered through the ``inapp`` channel is stored here; the
    row is a first-class citizen (state, pin, group, category, priority,
    optional action payload).
  - ``comm_notification_events``: append-only history (delivery, read,
    dismiss, retry, error, channel/provider per attempt).
  - ``comm_user_preferences``: one row per user with the full preference
    document (channels, categories, frequency, quiet hours, …).

State lifecycle (inbox): unread → read → archived | deleted (recoverable),
pinned is orthogonal. Deleted rows are soft-deleted so accelerated-delete
queries can purge them later without risk.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)

from app._compat import UTC

from ..database import Base


def _now() -> datetime:
    return datetime.now(UTC)


class UserNotification(Base):
    __tablename__ = "comm_notifications"
    __table_args__ = (
        Index("ix_comm_notifications_user_state", "user_id", "state"),
        Index("ix_comm_notifications_user_category", "user_id", "category"),
        Index("ix_comm_notifications_user_priority", "user_id", "priority"),
        Index("ix_comm_notifications_user_group", "user_id", "group_key"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    category = Column(String(40), nullable=False, default="system")
    priority = Column(String(20), nullable=False, default="medium")
    title = Column(String(255), nullable=False, default="")
    body = Column(Text, nullable=False, default="")
    data = Column(Text, nullable=True)  # JSON: action module/payload, deep link
    state = Column(String(20), nullable=False, default="unread", index=True)
    pinned = Column(Boolean, nullable=False, default=False)
    group_key = Column(String(100), nullable=True)
    delivery_id = Column(String(64), nullable=True, index=True)
    template_id = Column(String(100), nullable=True)
    locale = Column(String(10), nullable=False, default="ar")
    external_status = Column(String(40), nullable=True)  # per-channel status
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now, index=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category": self.category,
            "priority": self.priority,
            "title": self.title,
            "body": self.body,
            "data": self.data,
            "state": self.state,
            "pinned": bool(self.pinned),
            "group_key": self.group_key,
            "delivery_id": self.delivery_id,
            "template_id": self.template_id,
            "locale": self.locale,
            "external_status": self.external_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
        }


class NotificationEvent(Base):
    __tablename__ = "comm_notification_events"
    __table_args__ = (
        Index("ix_comm_notification_events_nid_created", "notification_id", "created_at"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    notification_id = Column(
        BigInteger,
        ForeignKey("comm_notifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type = Column(String(40), nullable=False)  # delivered/read/dismissed/retried/error
    channel = Column(String(40), nullable=True)
    provider = Column(String(40), nullable=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "notification_id": self.notification_id,
            "event_type": self.event_type,
            "channel": self.channel,
            "provider": self.provider,
            "detail": self.detail,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserPreferencesRow(Base):
    __tablename__ = "comm_user_preferences"

    user_id = Column(BigInteger, primary_key=True)
    preferences = Column(Text, nullable=False, default="{}")  # JSON document
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)
