from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app._compat import UTC
from app.national.base import NationalBase

NOTIFICATION_TABLE = "national_notifications"
TEMPLATE_TABLE = "national_notification_templates"
DELIVERY_TABLE = "national_delivery_reports"
PREFERENCE_TABLE = "national_notification_preferences"
BATCH_TABLE = "national_notification_batches"


class NationalNotificationModel(NationalBase):
    __tablename__ = NOTIFICATION_TABLE

    id = Column(String(26), primary_key=True)
    channel = Column(String(32), nullable=False, index=True)
    recipient = Column(String(512), nullable=False)
    recipients = Column(JSON, nullable=False, default=list)
    subject = Column(String(512), nullable=False, default="")
    body = Column(Text, nullable=False, default="")
    template_id = Column(String(26), nullable=True, index=True)
    template_data = Column(JSON, nullable=True)
    priority = Column(String(16), nullable=False, default="medium")
    category = Column(String(32), nullable=False, default="system")
    status = Column(String(16), nullable=False, default="pending", index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    correlation_id = Column(String(64), nullable=True, index=True)
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    batch_id = Column(String(26), nullable=True, index=True)

    delivery_reports = relationship("NationalDeliveryReportModel", back_populates="notification", lazy="selectin")
    batch = relationship("NationalNotificationBatchModel", back_populates="notifications_rel", foreign_keys=[batch_id])


class NationalNotificationTemplateModel(NationalBase):
    __tablename__ = TEMPLATE_TABLE

    id = Column(String(26), primary_key=True)
    name = Column(String(128), nullable=False, index=True)
    description = Column(Text, nullable=True, default="")
    channel = Column(String(32), nullable=False, index=True)
    language = Column(String(8), nullable=False, default="ar")
    subject_template = Column(Text, nullable=False, default="")
    body_template = Column(Text, nullable=False, default="")
    template_engine = Column(String(16), nullable=False, default="jinja2")
    variables = Column(JSON, nullable=True)
    category = Column(String(32), nullable=False, default="system")
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    version = Column(Integer, nullable=False, default=1)


class NationalDeliveryReportModel(NationalBase):
    __tablename__ = DELIVERY_TABLE

    id = Column(String(26), primary_key=True)
    notification_id = Column(String(26), ForeignKey(f"{NOTIFICATION_TABLE}.id"), nullable=False, index=True)
    provider_status = Column(String(32), nullable=True)
    provider_message_id = Column(String(128), nullable=True)
    provider_response = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="sent_to_provider")
    attempted_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    attempt = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    notification = relationship("NationalNotificationModel", back_populates="delivery_reports")


class NationalNotificationPreferenceModel(NationalBase):
    __tablename__ = PREFERENCE_TABLE

    id = Column(String(26), primary_key=True)
    user_id = Column(String(64), nullable=False, index=True)
    channel = Column(String(32), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    quiet_hours_start = Column(String(5), nullable=True)
    quiet_hours_end = Column(String(5), nullable=True)
    max_daily = Column(Integer, nullable=False, default=50)
    categories_opt_in = Column(JSON, nullable=True)
    categories_opt_out = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    __table_args__ = (
        __import__("sqlalchemy").UniqueConstraint("user_id", "channel", name="uq_user_channel"),
    )


class NationalNotificationBatchModel(NationalBase):
    __tablename__ = BATCH_TABLE

    id = Column(String(26), primary_key=True)
    batch_key = Column(String(128), nullable=False, index=True)
    notification_ids = Column(JSON, nullable=False, default=list)
    status = Column(String(16), nullable=False, default="pending", index=True)
    total_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    failure_count = Column(Integer, nullable=False, default=0)
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    notifications_rel = relationship("NationalNotificationModel", lazy="selectin")


_ALL_MODELS: list[type[NationalBase]] = [
    NationalNotificationModel,
    NationalNotificationTemplateModel,
    NationalDeliveryReportModel,
    NationalNotificationPreferenceModel,
    NationalNotificationBatchModel,
]
