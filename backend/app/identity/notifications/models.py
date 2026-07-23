from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.identity.base import IdentityBaseEntity


class NotificationTemplate(IdentityBaseEntity):
    __tablename__ = "niam_notif_templates"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    template_id = Column(String(100), unique=True, nullable=False, index=True)

    name = Column(String(200), nullable=False)
    notification_type = Column(String(20), nullable=False, index=True)
    subject = Column(String(200), nullable=True)
    body = Column(Text, nullable=False)
    variables = Column(JSON, nullable=True)
    locale = Column(String(10), default="ar", nullable=False)
    version = Column(String(20), default="1.0", nullable=False)

    is_active = Column(Boolean, default=False, nullable=False)


class NotificationQueue(IdentityBaseEntity):
    __tablename__ = "niam_notif_queue"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    queue_id = Column(String(100), unique=True, nullable=False, index=True)

    recipient_id = Column(String(100), nullable=False, index=True)
    recipient_type = Column(String(30), nullable=False)
    notification_type = Column(String(20), nullable=False)
    channel = Column(String(20), nullable=False)
    template_id = Column(String(100), ForeignKey("niam_notif_templates.template_id", ondelete="SET NULL"), nullable=True)

    subject = Column(String(200), nullable=True)
    body = Column(Text, nullable=True)
    context = Column(JSON, nullable=True)

    priority = Column(String(20), default="medium", nullable=False, index=True)
    status = Column(String(20), default="queued", nullable=False, index=True)

    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    error_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    last_error = Column(Text, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=False, nullable=False)


class NotificationPreference(IdentityBaseEntity):
    __tablename__ = "niam_notif_preferences"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    preference_id = Column(String(100), unique=True, nullable=False, index=True)

    recipient_id = Column(String(100), nullable=False, index=True)
    recipient_type = Column(String(30), nullable=False)

    category = Column(String(30), nullable=False)
    channel = Column(String(20), nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)

    quiet_hours_start = Column(String(5), nullable=True)
    quiet_hours_end = Column(String(5), nullable=True)

    is_active = Column(Boolean, default=False, nullable=False)