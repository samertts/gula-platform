from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC

from .enums import (
    DeliveryReportStatus,
    NotificationCategory,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    TemplateEngine,
)


@dataclass
class Notification:
    id: str
    channel: NotificationChannel
    recipients: list[str]
    subject: str = ""
    body: str = ""
    template_id: str | None = None
    template_data: dict[str, Any] | None = None
    priority: NotificationPriority = NotificationPriority.MEDIUM
    category: NotificationCategory = NotificationCategory.SYSTEM
    status: NotificationStatus = NotificationStatus.PENDING
    scheduled_at: datetime | None = None
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    read_at: datetime | None = None
    failed_at: datetime | None = None
    error_message: str | None = None
    metadata: dict[str, Any] | None = None
    correlation_id: str | None = None
    created_by: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class NotificationTemplate:
    id: str
    name: str
    description: str = ""
    channel: NotificationChannel = NotificationChannel.EMAIL
    language: str = "ar"
    subject_template: str = ""
    body_template: str = ""
    template_engine: TemplateEngine = TemplateEngine.JINJA2
    variables: list[str] | None = None
    category: NotificationCategory = NotificationCategory.SYSTEM
    created_by: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: int = 1


@dataclass
class DeliveryReport:
    id: str
    notification_id: str
    provider_status: str | None = None
    provider_message_id: str | None = None
    provider_response: str | None = None
    status: DeliveryReportStatus = DeliveryReportStatus.SENT_TO_PROVIDER
    attempted_at: datetime | None = None
    delivered_at: datetime | None = None
    error_message: str | None = None
    attempt: int = 1


@dataclass
class NotificationPreference:
    user_id: str
    channel: NotificationChannel
    enabled: bool = True
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    max_daily: int = 50
    categories_opt_in: list[NotificationCategory] | None = None
    categories_opt_out: list[NotificationCategory] | None = None


@dataclass
class NotificationSchedule:
    id: str
    notification_id: str
    scheduled_at: datetime
    timezone: str = "UTC"
    recurring: bool = False
    cron_expression: str | None = None
    recurring_end_at: datetime | None = None


@dataclass
class NotificationBatch:
    id: str
    batch_key: str
    notifications: list[str]
    status: NotificationStatus = NotificationStatus.PENDING
    total_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    created_by: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
