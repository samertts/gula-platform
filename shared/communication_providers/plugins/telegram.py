"""Telegram provider plugin for the GULA Communication Platform.

Wraps the existing enterprise Telegram implementation
(``shared.notifications.telegram.TelegramNotificationService``) — the
canonical transport with webhooks, media, keyboards, batching, rate
limiting and redaction stays untouched. This plugin adapts it to the
Communication Core ``telegram`` channel and adds provider-level circuit
breaking, metrics, health and cancellation.
"""

from __future__ import annotations

import logging
from typing import Any

from shared.communication.model import (
    ContentFormat,
    OutboundMessage,
    ProviderDeliveryResult,
    Recipient,
)
from shared.communication.plugins import PluginMetadata, ProviderPlugin
from shared.communication.providers import (
    AlertCapability,
    BulkCapability,
    MediaCapability,
    ProviderOptions,
    RichTextCapability,
    StatusCallbackCapability,
)

from ..base import BaseChannelProvider, ProviderSettings, TokenBucket
from ..secrets import SecretResolver

logger = logging.getLogger("gula.communication.providers.telegram")


def _load_service() -> Any:
    """Lazy import keeps plugin registration free of httpx."""
    from shared.notifications.telegram import TelegramNotificationService

    return TelegramNotificationService()


class TelegramProvider(
    BaseChannelProvider,
    RichTextCapability,
    MediaCapability,
    AlertCapability,
    BulkCapability,
    StatusCallbackCapability,
):
    """Telegram delivery through the existing enterprise service.

    Channel: ``telegram``. Supports text, HTML, MarkdownV2, attachments
    (documents/photo via file path or URL), severity alerts and broadcast.
    """

    def __init__(
        self,
        settings: ProviderSettings,
        *,
        service: Any = None,
        redactor: Any = None,
        rate_limiter: TokenBucket | None = None,
    ) -> None:
        from ..base import ProviderMetrics, Redactor

        metrics = ProviderMetrics(settings.name)
        red = redactor or Redactor()
        super().__init__(
            settings,
            redactor=red,
            rate_limiter=rate_limiter,
            metrics=metrics,
        )
        self._service = service or _load_service()
        token = getattr(self._service, "_bot_token", "")
        red.register(token)
        self.status_changes: list[tuple[str, str]] = []

    @property
    def is_configured(self) -> bool:
        return bool(getattr(self._service, "is_configured", False))

    # ── delivery ───────────────────────────────────────────────────────────

    def deliver(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        return self._deliver_protected(recipient, message, options, self._attempt_text)

    def deliver_rich(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        return self._deliver_protected(recipient, message, options, self._attempt_rich)

    def deliver_media(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        return self._deliver_protected(recipient, message, options, self._attempt_media)

    def deliver_alert(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        severity: str,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        def attempt(
            rec: Recipient,
            msg: OutboundMessage,
            opts: ProviderOptions | None,
        ) -> ProviderDeliveryResult:
            result = self._service.send_alert(rec.address, msg.content, level=severity)
            return self._result(
                success=result.success,
                delivery_ref=str(getattr(result, "message_id", "") or ""),
                error=result.error,
                retryable=False,
            )

        return self._deliver_protected(recipient, message, options, attempt)

    def deliver_bulk(
        self,
        recipients: list[Recipient],
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> list[ProviderDeliveryResult]:
        addresses = [r.address for r in recipients if r.address]
        if not addresses:
            return [self._result(success=False, error="no recipients")]
        results = self._service.send_broadcast(addresses, message.content, parse_mode="")
        self.metrics.record_attempt(any(r.success for r in results))
        return [
            self._result(
                success=result.success,
                delivery_ref=str(getattr(result, "message_id", "") or ""),
                error=result.error,
                retryable=False,
            )
            for result in results
        ]

    def on_status_change(self, delivery_ref: str, status: str) -> None:
        self.status_changes.append((delivery_ref, status))
        self._log.info(
            "communication_telegram_status ref=%s status=%s",
            delivery_ref,
            status,
        )

    # ── internals ──────────────────────────────────────────────────────────

    def _attempt_text(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None,
    ) -> ProviderDeliveryResult:
        result = self._service.send_text(recipient.address, message.content)
        return self._result(
            success=result.success,
            delivery_ref=str(getattr(result, "message_id", "") or ""),
            error=result.error,
            retryable=False,
        )

    def _attempt_rich(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None,
    ) -> ProviderDeliveryResult:
        if message.format == ContentFormat.MARKDOWN:
            result = self._service.send_markdown_v2(recipient.address, message.content)
        else:
            result = self._service.send_html(recipient.address, message.content)
        return self._result(
            success=result.success,
            delivery_ref=str(getattr(result, "message_id", "") or ""),
            error=result.error,
            retryable=False,
        )

    def _attempt_media(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None,
    ) -> ProviderDeliveryResult:
        caption = message.content
        first = message.attachments[0]
        if first.reference.startswith(("http://", "https://")):
            result = self._service.send_document(recipient.address, first.reference, caption=caption)
        else:
            result = self._service.send_file(recipient.address, first.reference, caption=caption)
        return self._result(
            success=result.success,
            delivery_ref=str(getattr(result, "message_id", "") or ""),
            error=result.error,
            retryable=False,
        )


class TelegramPlugin(ProviderPlugin):
    """Self-registering Telegram provider plugin (env-only configuration)."""

    metadata = PluginMetadata(
        id="telegram",
        version="1.0.0",
        description="Telegram delivery (wraps shared.notifications.telegram)",
    )

    def __init__(self, resolver: SecretResolver | None = None) -> None:
        self._resolver = resolver or SecretResolver()

    def create_provider(self) -> TelegramProvider:
        settings = ProviderSettings(
            name="telegram",
            channel="telegram",
            timeout_seconds=float(self._resolver.get_int("TELEGRAM_TIMEOUT_SECONDS", 30)),
            max_retries=0,  # retries live inside the Telegram service
            rate_per_minute=self._resolver.get_int("TELEGRAM_RATE_PER_MINUTE", 60),
            circuit_failure_threshold=self._resolver.get_int("TELEGRAM_CIRCUIT_FAILURE_THRESHOLD", 5),
            circuit_recovery_timeout=float(self._resolver.get_int("TELEGRAM_CIRCUIT_RECOVERY_TIMEOUT", 30)),
            enabled=self._resolver.get_bool("TELEGRAM_ENABLED", True),
        )
        return TelegramProvider(settings)

    def activate(self, context: dict[str, Any] | None = None) -> None:
        logger.info("communication_plugin_activate id=%s", self.metadata.id)

    def deactivate(self) -> None:
        logger.info("communication_plugin_deactivate id=%s", self.metadata.id)


def create_plugin() -> TelegramPlugin:
    """Factory used by tests and entry-point consumers."""
    return TelegramPlugin()


__all__ = ["TelegramPlugin", "TelegramProvider", "create_plugin"]