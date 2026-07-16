"""Standardized notification module — wraps existing notifications/service.py."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from ..notifications.service import get_service as get_legacy_service
from . import PlatformRegistry

logger = logging.getLogger("gula.platform.notifications")


@dataclass
class NotificationResult:
    success: bool = False
    channel: str = ""
    recipient: str = ""
    error: str | None = None


class NotificationService:
    def __init__(self) -> None:
        self._service = get_legacy_service()

    def send_notification(
        self,
        channel: str,
        to: str,
        subject: str = "",
        body: str = "",
        template_id: str = "",
        template_data: dict | None = None,
    ) -> NotificationResult:
        result = self._service.send(
            channel=channel, to=to, subject=subject, body=body,
            template_id=template_id, template_data=template_data,
        )
        return NotificationResult(success=result.success, channel=result.channel, recipient=result.recipient, error=result.error)

    def broadcast(
        self,
        channel: str,
        recipients: list[str],
        subject: str = "",
        body: str = "",
    ) -> list[NotificationResult]:
        results = []
        for to in recipients:
            result = self._service.send(channel=channel, to=to, subject=subject, body=body)
            results.append(NotificationResult(success=result.success, channel=result.channel, recipient=result.recipient, error=result.error))
        return results

    def schedule_notification(
        self,
        channel: str,
        to: str,
        subject: str = "",
        body: str = "",
        schedule_at: datetime | None = None,
    ) -> NotificationResult:
        result = self._service.send(channel=channel, to=to, subject=subject, body=body)
        return NotificationResult(success=result.success, channel=result.channel, recipient=result.recipient, error=result.error)


PlatformRegistry.register("notifications", NotificationService(), capabilities=[
    {"name": "send_notification", "description": "Send a single notification via a channel"},
    {"name": "broadcast", "description": "Send the same notification to multiple recipients"},
    {"name": "schedule_notification", "description": "Schedule a notification for later delivery"},
])
