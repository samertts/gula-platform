from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field


@dataclass
class NotificationSent:
    notification_id: str
    channel: str
    recipient: str
    priority: str = "medium"
    category: str = "system"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    @property
    def event_name(self) -> str:
        return "national.notification.sent"


@dataclass
class NotificationDelivered:
    notification_id: str
    channel: str
    recipient: str
    delivered_at: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    @property
    def event_name(self) -> str:
        return "national.notification.delivered"


@dataclass
class NotificationFailed:
    notification_id: str
    channel: str
    recipient: str
    error: str
    attempt: int = 1
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    @property
    def event_name(self) -> str:
        return "national.notification.failed"


@dataclass
class NotificationRead:
    notification_id: str
    user_id: str
    read_at: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    @property
    def event_name(self) -> str:
        return "national.notification.read"


@dataclass
class NotificationBounced:
    notification_id: str
    channel: str
    recipient: str
    reason: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    @property
    def event_name(self) -> str:
        return "national.notification.bounced"


@dataclass
class NotificationScheduled:
    notification_id: str
    channel: str
    scheduled_at: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    @property
    def event_name(self) -> str:
        return "national.notification.scheduled"


@dataclass
class NotificationBatchCompleted:
    batch_id: str
    total: int
    success: int
    failure: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    @property
    def event_name(self) -> str:
        return "national.notification.batch_completed"


@dataclass
class TemplateCreated:
    template_id: str
    name: str
    channel: str
    language: str = "ar"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    @property
    def event_name(self) -> str:
        return "national.notification.template_created"
