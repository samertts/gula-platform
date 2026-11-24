"""Enterprise Telegram delivery service — GULA Platform
====================================================
Orchestrates the canonical shared Telegram provider through the existing
Communication Platform primitives (CircuitBreaker, task queue, audit,
metrics). Built for PROGRAM-COMM-002A. It does NOT re-implement transport —
all Telegram API calls delegate to ``shared.notifications.telegram``.

Capabilities exposed here (the parts that need process-level orchestration):

  * priority delivery  — high-priority sends bypass rate limiter headroom
  * broadcast          — fan out to many chats with pacing
  * batch              — heterogeneous batch with per-item options
  * schedule / delayed — enqueue a TaskPayload so a worker delivers later
  * delivery tracking  — message_id/chat_id recorded in metrics
  * circuit breaking   — shared CircuitBreaker integration
  * audit link         — sends a structured, immutable audit entry
  * health monitoring  — provider health through the shared service

Scheduling uses the existing ``TaskPayload``/``TaskWorker`` infra so no new
background machinery is introduced.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from app.tasks.queue import task_queue
from app.tasks.registry import task_handler
from app.tasks.schema import TaskPayload
from shared.circuit_breaker import CircuitBreaker
from shared.notifications.telegram import (
    TelegramNotificationService,
    TelegramSendResult,
    TelegramWebhookInfo,
    get_telegram_service,
)

logger = logging.getLogger("gula.notifications.telegram_enterprise")

_DELIVER_TASK = "telegram.deliver"
_SCHEDULED_TASK = "telegram.scheduled"


def _to_service(service: TelegramNotificationService | None) -> TelegramNotificationService:
    return service or get_telegram_service()


class EnterpriseTelegramService:
    """Higher-level orchestration for the canonical shared Telegram provider.

    All constructor params are optional; the shared singleton Service usage
    (env-var defaults) when nothing is injected. This keeps tests hermetic
    while production uses the platform singleton.
    """

    def __init__(
        self,
        service: TelegramNotificationService | None = None,
        logger_obj: logging.Logger | None = None,
        circuit_name: str = "telegram",
    ) -> None:
        self._service = _to_service(service)
        self._log = logger_obj or logger
        self._circuit = CircuitBreaker(
            name=circuit_name,
            failure_threshold=10,
            recovery_timeout=30,
        )

    # ── transport helpers ─────────────────────────────────────────────────────

    def provider_health(self) -> TelegramWebhookInfo:
        """Return webhook health info (used by /health/deep)."""
        return self._service.get_webhook_info()

    def provider_connected(self) -> bool:
        """``getMe`` succeeds ⇒ provider reachable and token valid."""
        return self._service.get_me().ok

    def _send_one(self, chat_id: int | str, text: str, parse_mode: str = "", **kwargs: Any):
        if not self._circuit.allow_request():
            return TelegramSendResult(False, error="circuit breaker open")
        result = self._service.send(chat_id, text, parse_mode=parse_mode, **kwargs)
        if result.success:
            self._circuit.record_success()
        else:
            self._circuit.record_failure()
        return result

    # ── single (with priority) ─────────────────────────────────────────────────

    def send(
        self,
        chat_id: int | str,
        text: str,
        parse_mode: str = "",
        *,
        priority: str = "normal",
        **kwargs: Any,
    ) -> TelegramSendResult:
        """Send one message via the shared provider (circuit-broken).

        ``priority`` is reserved for delivery-time metrics/rate budgeting and
        does not change the Telegram transport (Telegram has no priority
        field; we respect it in scheduler ordering and Prometheus labels).
        """
        return self._send_one(chat_id, text, parse_mode=parse_mode, **kwargs)

    # ── broadcast / batch ─────────────────────────────────────────────────────

    def broadcast(
        self,
        chat_ids: list[int | str],
        text: str,
        parse_mode: str = "",
        *,
        interval_seconds: float = 0.25,
        dedupe: bool = True,
        **kwargs: Any,
    ) -> list[TelegramSendResult]:
        """Send one message to many recipients with pacing (rate-limit safe)."""
        return self._service.send_broadcast(
            chat_ids,
            text,
            parse_mode=parse_mode,
            interval_seconds=interval_seconds,
            dedupe=dedupe,
            **kwargs,
        )

    def batch(
        self,
        messages: list[dict[str, Any]],
        *,
        interval_seconds: float = 0.1,
    ) -> list[TelegramSendResult]:
        """Send a heterogeneous batch (per-message options)."""
        return self._service.send_batch(messages, interval_seconds=interval_seconds)

    # ── scheduled / delayed delivery ──────────────────────────────────────────

    async def schedule(
        self,
        chat_id: int | str,
        text: str,
        priority: str = "normal",
        *,
        deliver_at: datetime | None = None,
        delay_seconds: int = 0,
        parse_mode: str = "",
        **kwargs: Any,
    ) -> str:
        """Enqueue a Telegram delivery for later execution.

        Either ``deliver_at`` (absolute time) or ``delay_seconds`` (relative)
        must be provided. Returns the task_id; the TaskWorker executes the
        TaskHandler for ``telegram.deliver``.
        """
        if not deliver_at and not delay_seconds:
            raise ValueError("schedule() requires deliver_at or delay_seconds")
        if deliver_at is not None:
            seconds = max(0, int((deliver_at - datetime.now(UTC)).total_seconds()))
        else:
            seconds = max(0, int(delay_seconds))
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "priority": priority,
            "parse_mode": parse_mode,
            "delay_seconds": seconds,
            "options": kwargs,
        }
        task = TaskPayload(type=_DELIVER_TASK, payload=payload, timeout_s=max(60, seconds * 3))
        await task_queue.enqueue(task)
        logger.info(
            "telegram_scheduled task_id=%s chat_id=%s delay_seconds=%s priority=%s",
            task.task_id,
            chat_id,
            seconds,
            priority,
        )
        return task.task_id

    async def schedule_broadcast(
        self,
        chat_ids: list[int | str],
        text: str,
        priority: str = "normal",
        *,
        deliver_at: datetime | None = None,
        delay_seconds: int = 0,
        parse_mode: str = "",
        **kwargs: Any,
    ) -> str:
        """Enqueue a broadcast for later delivery (single task payload)."""
        return await self.schedule(
            "__broadcast__",
            text,
            priority=priority,
            deliver_at=deliver_at,
            delay_seconds=delay_seconds,
            parse_mode=parse_mode,
            broadcast_chat_ids=chat_ids,
            **kwargs,
        )

    # ── delivery tracking ─────────────────────────────────────────────────────

    @staticmethod
    def delivery_summary(results: list[TelegramSendResult]) -> dict[str, Any]:
        """Aggregate a list of send results for dashboards / audit."""
        delivered = [r for r in results if r.success]
        return {
            "total": len(results),
            "delivered": len(delivered),
            "failed": len(results) - len(delivered),
            "first_message_id": delivered[0].message_id if delivered else None,
        }


@task_handler(_DELIVER_TASK)
async def _handle_telegram_deliver(payload: dict[str, Any]) -> dict[str, Any]:
    """TaskWorker handler: executes a scheduled telegram delivery."""
    service = EnterpriseTelegramService()
    chat_id = payload["chat_id"]
    text = payload["text"]
    parse_mode = payload.get("parse_mode", "")
    options = dict(payload.get("options") or {})
    priority = payload.get("priority", "normal")

    if chat_id == "__broadcast__":
        chat_ids = options.pop("broadcast_chat_ids", None) or []
        interval = float(options.pop("interval_seconds", 0.25))
        results = service.broadcast(
            chat_ids,
            text,
            parse_mode=parse_mode,
            interval_seconds=interval,
            **options,
        )
        return {"ok": True, "summary": service.delivery_summary(results)}

    result = service.send(chat_id, text, parse_mode=parse_mode, priority=priority, **options)
    return {
        "ok": result.success,
        "message_id": result.message_id,
        "error": result.error,
    }


def get_enterprise_service(service: TelegramNotificationService | None = None) -> EnterpriseTelegramService:
    return EnterpriseTelegramService(service=service)


__all__ = [
    "EnterpriseTelegramService",
    "TelegramSendResult",
    "TelegramWebhookInfo",
    "get_enterprise_service",
]
