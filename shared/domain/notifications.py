from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class NotificationChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NotificationPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Notification:
    id: str = ""
    recipient: str = ""
    channel: NotificationChannel = NotificationChannel.IN_APP
    title: str = ""
    body: str = ""
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: dict[str, Any] = field(default_factory=dict)
    read: bool = False
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid4())
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "recipient": self.recipient, "channel": self.channel.value,
            "title": self.title, "body": self.body, "priority": self.priority.value,
            "data": self.data, "read": self.read, "created_at": self.created_at,
        }


@dataclass
class NotificationTemplate:
    name: str = ""
    title_template: str = ""
    body_template: str = ""
    channel: NotificationChannel = NotificationChannel.IN_APP

    def render(self, **kwargs: Any) -> Notification:
        return Notification(
            title=self.title_template.format(**kwargs),
            body=self.body_template.format(**kwargs),
            channel=self.channel,
        )


@dataclass
class SubscriptionNotification:
    lab_id: int = 0
    event: str = ""
    channel: NotificationChannel = NotificationChannel.WEBHOOK
    target_url: str = ""
    enabled: bool = True


__all__ = ["Notification", "NotificationTemplate", "SubscriptionNotification",
           "NotificationChannel", "NotificationPriority"]
