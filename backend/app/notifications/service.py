import logging
from dataclasses import dataclass
from typing import Any, Callable

from shared.circuit_breaker import CircuitBreaker, CircuitState
from shared.notifications.sender import get_sender
from shared.notifications.template import render_template

logger = logging.getLogger("gula.notifications")


@dataclass
class NotificationResult:
    success: bool
    channel: str
    recipient: str
    error: str | None = None
    audit_log_id: int | None = None


class NotificationService:
    def __init__(self) -> None:
        self._circuit_breaker = CircuitBreaker(
            name="notification",
            failure_threshold=10,
            recovery_timeout=30,
        )

    def _run_with_circuit(self, fn: Callable[[], bool]) -> tuple[bool, str | None]:
        if self._circuit_breaker.state == CircuitState.OPEN:
            return False, "Circuit breaker open"

        def guarded() -> bool:
            result = fn()
            if not result:
                raise RuntimeError("Delivery failed")
            return True

        try:
            self._circuit_breaker.call(guarded)
            return True, None
        except Exception as exc:
            return False, str(exc)

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
        if template_id:
            rendered = render_template(template_id, channel, template_data)
            if rendered:
                subject = rendered.get("subject", subject)
                body = rendered.get("body", body)

        sender = get_sender()
        if channel == "email":
            deliver = lambda: sender.send_email(to, subject, body)
        elif channel == "sms":
            deliver = lambda: sender.send_sms(to, body)
        elif channel == "whatsapp":
            deliver = lambda: sender.send_whatsapp(to, body)
        elif channel == "push":
            deliver = lambda: sender.send_push(to, subject, body, template_data)
        else:
            return NotificationResult(
                success=False,
                channel=channel,
                recipient=to,
                error=f"Unknown channel: {channel}",
            )

        success, error = self._run_with_circuit(deliver)
        if success:
            return NotificationResult(success=True, channel=channel, recipient=to)
        logger.error("[NOTIFICATION] %s delivery failed to %s: %s", channel, to, error)
        return NotificationResult(
            success=False,
            channel=channel,
            recipient=to,
            error=error,
        )

    def send_email(self, to: str, subject: str, body: str) -> NotificationResult:
        return self.send("email", to, subject=subject, body=body)

    def send_sms(self, to: str, body: str) -> NotificationResult:
        return self.send("sms", to, body=body)

    def send_push(
        self, token: str, title: str, body: str, data: dict[str, Any] | None = None,
    ) -> NotificationResult:
        return self.send("push", token, subject=title, body=body, template_data=data)

    def send_whatsapp(self, to: str, body: str) -> NotificationResult:
        return self.send("whatsapp", to, body=body)

    def send_telegram(self, bot_token: str, chat_id: str, message: str) -> NotificationResult:
        from .telegram import send_telegram

        success, error = self._run_with_circuit(lambda: send_telegram(bot_token, chat_id, message))
        return NotificationResult(
            success=success,
            channel="telegram",
            recipient=chat_id,
            error=error,
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
                success=False,
                channel=channel,
                recipient=to,
                error=f"Template not found: {template_id}",
            )
        return self.send(
            channel,
            to,
            subject=rendered.get("subject", ""),
            body=rendered.get("body", ""),
        )


_service: NotificationService | None = None


def get_service() -> NotificationService:
    global _service
    if _service is None:
        _service = NotificationService()
    return _service


__all__ = [
    "NotificationResult",
    "NotificationService",
    "get_service",
]
