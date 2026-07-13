from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from shared.notifications.sender import get_sender
from shared.notifications.template import render_template

from shared.circuit_breaker import CircuitBreaker

logger = logging.getLogger("gula.notifications")


@dataclass
class NotificationResult:
    success: bool
    channel: str
    recipient: str
    error: Optional[str] = None
    audit_log_id: Optional[int] = None


class NotificationService:
    def __init__(self) -> None:
        self._circuit_breaker = CircuitBreaker(
            name="notification",
            failure_threshold=10,
            recovery_timeout=30,
        )

    def send(
        self,
        channel: str,
        to: str,
        subject: str = "",
        body: str = "",
        template_id: str = "",
        template_data: dict[str, Any] | None = None,
        priority: str = "normal",
    ) -> NotificationResult:
        if not self._circuit_breaker.allow_request():
            return NotificationResult(
                success=False,
                channel=channel,
                recipient=to,
                error="Circuit breaker open",
            )

        if template_id:
            rendered = render_template(template_id, channel, template_data)
            if rendered:
                subject = rendered.get("subject", subject)
                body = rendered.get("body", body)

        try:
            sender = get_sender()
            result: bool = False
            if channel == "email":
                result = sender.send_email(to, subject, body)
            elif channel == "sms":
                result = sender.send_sms(to, body)
            elif channel == "whatsapp":
                result = sender.send_whatsapp(to, body)
            elif channel == "push":
                result = sender.send_push(to, subject, body, template_data)
            else:
                return NotificationResult(
                    success=False, channel=channel, recipient=to, error=f"Unknown channel: {channel}"
                )

            if result:
                self._circuit_breaker.record_success()
                return NotificationResult(success=True, channel=channel, recipient=to)
            self._circuit_breaker.record_failure()
            return NotificationResult(
                success=False, channel=channel, recipient=to, error="Delivery failed"
            )
        except Exception as exc:
            self._circuit_breaker.record_failure()
            logger.error("[NOTIFICATION] %s delivery failed to %s: %s", channel, to, exc)
            return NotificationResult(
                success=False, channel=channel, recipient=to, error=str(exc)
            )

    def send_email(self, to: str, subject: str, body: str) -> NotificationResult:
        return self.send("email", to, subject=subject, body=body)

    def send_sms(self, to: str, body: str) -> NotificationResult:
        return self.send("sms", to, body=body)

    def send_push(self, token: str, title: str, body: str, data: dict[str, Any] | None = None) -> NotificationResult:
        return self.send("push", token, subject=title, body=body, template_data=data)

    def send_whatsapp(self, to: str, body: str) -> NotificationResult:
        return self.send("whatsapp", to, body=body)

    def send_telegram(self, bot_token: str, chat_id: str, message: str) -> NotificationResult:
        from .telegram import send_telegram
        result = send_telegram(bot_token, chat_id, message)
        if result:
            self._circuit_breaker.record_success()
            return NotificationResult(success=True, channel="telegram", recipient=chat_id)
        self._circuit_breaker.record_failure()
        return NotificationResult(
            success=False, channel="telegram", recipient=chat_id, error="Telegram delivery failed"
        )

    def send_template(
        self,
        template_id: str,
        channel: str,
        to: str,
        data: dict[str, Any] | None = None,
    ) -> NotificationResult:
        rendered = render_template(template_id, channel, data)
        if rendered is None:
            return NotificationResult(
                success=False, channel=channel, recipient=to, error=f"Template not found: {template_id}"
            )
        return self.send(channel, to, subject=rendered.get("subject", ""), body=rendered.get("body", ""))


_service: NotificationService | None = None


def get_service() -> NotificationService:
    global _service
    if _service is None:
        _service = NotificationService()
    return _service


__all__ = [
    "NotificationService",
    "NotificationResult",
    "get_service",
]
