from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.national.notification_platform.domain.enums import NotificationChannel

logger = logging.getLogger("gula.national.notification_platform.adapters")


async def _canonical_deliver(
    channel: str,
    recipient: str,
    subject: str,
    body: str,
) -> SendResult:
    """Deliver through the canonical Shared Core notifications provider.

    The canonical NotificationService wraps the shared sender with a circuit
    breaker and returns NotificationResult(success, ...). Mapping is fail-closed:
    a provider exception or non-success result yields SendResult(success=False).
    """
    from app.notifications import get_service

    try:
        result = await asyncio.to_thread(
            get_service().send,
            channel,
            recipient,
            subject=subject,
            body=body,
        )
    except Exception as exc:
        logger.error("[%s] canonical delivery raised for %s: %s", channel, recipient, exc)
        return SendResult(success=False, error=str(exc))

    if result.success:
        return SendResult(success=True)
    logger.error("[%s] canonical delivery failed for %s: %s", channel, recipient, result.error)
    return SendResult(success=False, error=result.error or "Delivery failed")


@dataclass
class SendResult:
    success: bool
    provider_message_id: str | None = None
    provider_response: str | None = None
    error: str | None = None


class NotificationChannelAdapter(ABC):
    @abstractmethod
    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> SendResult: ...

    @property
    @abstractmethod
    def channel(self) -> NotificationChannel: ...


class EmailAdapter(NotificationChannelAdapter):
    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.EMAIL

    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> SendResult:
        return await _canonical_deliver(self.channel.value, recipient, subject, body)


class SMSAdapter(NotificationChannelAdapter):
    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.SMS

    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> SendResult:
        return await _canonical_deliver(self.channel.value, recipient, subject, body)


class PushAdapter(NotificationChannelAdapter):
    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.PUSH

    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> SendResult:
        return await _canonical_deliver(self.channel.value, recipient, subject, body)


class WebSocketAdapter(NotificationChannelAdapter):
    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.WEBSOCKET

    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> SendResult:
        return await _canonical_deliver(self.channel.value, recipient, subject, body)


class InAppAdapter(NotificationChannelAdapter):
    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.IN_APP

    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> SendResult:
        return await _canonical_deliver(self.channel.value, recipient, subject, body)


class WhatsAppAdapter(NotificationChannelAdapter):
    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.WHATSAPP

    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> SendResult:
        return await _canonical_deliver(self.channel.value, recipient, subject, body)


class TelegramAdapter(NotificationChannelAdapter):
    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.TELEGRAM

    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> SendResult:
        from app.notifications import send_telegram

        chat_id = recipient
        message = f"*{subject}*\n\n{body}" if subject else body
        bot_token = (metadata or {}).get("bot_token", "")
        if not bot_token:
            logger.error("[TELEGRAM] No bot_token provided for chat_id=%s", chat_id)
            return SendResult(success=False, error="No bot_token in metadata")
        result = send_telegram(bot_token, chat_id, message)
        if result:
            logger.info("[TELEGRAM] Sent to %s", chat_id)
            return SendResult(success=True, provider_message_id=f"tg_{chat_id[:8]}")
        logger.error("[TELEGRAM] Failed to send to %s", chat_id)
        return SendResult(success=False, error="Telegram delivery failed")


class GovernmentGatewayAdapter(NotificationChannelAdapter):
    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.GOVERNMENT_GATEWAY

    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> SendResult:
        return await _canonical_deliver(self.channel.value, recipient, subject, body)


class WebhookAdapter(NotificationChannelAdapter):
    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.WEBHOOK

    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> SendResult:
        import httpx

        url = recipient
        payload = {
            "subject": subject,
            "body": body,
            "metadata": metadata or {},
        }
        logger.info("[WEBHOOK] POST to %s — payload_size=%d", url, len(body))
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return SendResult(
                    success=True,
                    provider_message_id=f"wh_{url[:16]}",
                    provider_response=f"status={response.status_code}",
                )
        except Exception as exc:
            logger.error("[WEBHOOK] Failed to POST to %s: %s", url, exc)
            return SendResult(success=False, error=str(exc))


class FaxAdapter(NotificationChannelAdapter):
    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.FAX

    async def send(
        self,
        recipient: str,
        subject: str,
        body: str,
        metadata: dict[str, Any] | None = None,
    ) -> SendResult:
        return await _canonical_deliver(self.channel.value, recipient, subject, body)


__all__ = [
    "EmailAdapter",
    "FaxAdapter",
    "GovernmentGatewayAdapter",
    "InAppAdapter",
    "NotificationChannelAdapter",
    "PushAdapter",
    "SMSAdapter",
    "SendResult",
    "TelegramAdapter",
    "WebSocketAdapter",
    "WebhookAdapter",
    "WhatsAppAdapter",
]
