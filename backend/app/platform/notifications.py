"""Standardized notification module — wraps existing notifications/service.py."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from ..notifications.service import get_service as get_legacy_service
from ..notifications.telegram_enterprise import EnterpriseTelegramService
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
        self._telegram = EnterpriseTelegramService()

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
            channel=channel,
            to=to,
            subject=subject,
            body=body,
            template_id=template_id,
            template_data=template_data,
        )
        return NotificationResult(
            success=result.success,
            channel=result.channel,
            recipient=result.recipient,
            error=result.error,
        )

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
            results.append(
                NotificationResult(
                    success=result.success,
                    channel=result.channel,
                    recipient=result.recipient,
                    error=result.error,
                )
            )
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
        return NotificationResult(
            success=result.success,
            channel=result.channel,
            recipient=result.recipient,
            error=result.error,
        )

    def send_telegram(
        self,
        chat_id: int | str,
        text: str,
        parse_mode: str = "HTML",
        **kwargs,
    ) -> NotificationResult:
        """Send a Telegram message through the enterprise service."""
        return self._remap_telegram(self._telegram.send(chat_id, text, parse_mode=parse_mode, **kwargs))

    def broadcast_telegram(
        self,
        chat_ids: list,
        text: str,
        parse_mode: str = "HTML",
        interval_seconds: float = 0.25,
        **kwargs,
    ) -> list[NotificationResult]:
        """Broadcast to many Telegram recipients with pacing."""
        results = self._telegram.broadcast(
            chat_ids, text, parse_mode=parse_mode, interval_seconds=interval_seconds, **kwargs
        )
        return [self._remap_telegram(r) for r in results]

    def webhook_health(self) -> dict:
        """Provider health snapshot for /health/deep."""
        info = self._telegram.provider_health()
        return {
            "webhook_set": info.is_webhook_set,
            "pending_updates": info.pending_update_count,
            "last_error": info.last_error_message or None,
            "provider_connected": self._telegram.provider_connected(),
        }

    def capabilities(self) -> list[str]:
        return self._telegram._service.capabilities

    @staticmethod
    def _remap_telegram(result) -> NotificationResult:
        return NotificationResult(
            success=result.success,
            channel="telegram",
            recipient="",
            error=result.error,
        )


PlatformRegistry.register(
    "notifications",
    NotificationService(),
    capabilities=[
        {"name": "send_notification", "description": "Send a single notification via a channel"},
        {"name": "broadcast", "description": "Send the same notification to multiple recipients"},
        {
            "name": "schedule_notification",
            "description": "Schedule a notification for later delivery",
        },
        {"name": "send_telegram", "description": "Send a Telegram message (enterprise provider)"},
        {
            "name": "broadcast_telegram",
            "description": "Broadcast to many Telegram chats with pacing",
        },
        {"name": "telegram_webhook_health", "description": "Telegram provider/webhook health"},
        {
            "name": "telegram_capabilities",
            "description": "Advertise Telegram provider capabilities",
        },
    ],
)
