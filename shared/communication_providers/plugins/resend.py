"""Resend email provider plugin for the GULA Communication Platform.

Wraps the existing production Resend implementation
(``shared.notifications.resend.ResendEmailClient``) — no rebuilt transport,
no duplicated retry/timeout/redaction logic. The plugin adds provider-level
circuit breaking, rate limiting, metrics, health and cancellation on top,
then plugs into the Communication Core as a plain ``email``-channel
:class:`~shared.communication.providers.ChannelProvider`.
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
    ProviderOptions,
    RichTextCapability,
)

from ..base import BaseChannelProvider, ProviderSettings, TokenBucket
from ..secrets import SecretResolver

logger = logging.getLogger("gula.communication.providers.resend")


def _load_client() -> Any:
    """Lazy import keeps provider registration free of the resend SDK."""
    from shared.notifications.resend import ResendEmailClient

    return ResendEmailClient()


class ResendProvider(BaseChannelProvider, RichTextCapability, AlertCapability, BulkCapability):
    """Email delivery through the existing Resend client.

    Channel: ``email``. Supports plain text, HTML, alert severity tagging
    and multi-recipient bulk sends. Attachments are referenced as links in
    the body when they are HTTP(S) references (the Resend client owns the
    actual send).
    """

    def __init__(
        self,
        settings: ProviderSettings,
        *,
        client: Any = None,
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
        self._client = client or _load_client()
        red.register(self._client._api_key)

    @property
    def is_configured(self) -> bool:
        return bool(getattr(self._client, "is_configured", False))

    # ── delivery ───────────────────────────────────────────────────────────

    def deliver(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        return self._deliver_protected(recipient, message, options, self._attempt_deliver)

    def deliver_rich(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        return self._deliver_protected(recipient, message, options, self._attempt_deliver)

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
            tagged = f"[{severity.upper()}] {msg.content}"
            return self._attempt_deliver(rec, self._with_body(msg, tagged), opts)

        return self._deliver_protected(recipient, message, options, attempt)

    def deliver_bulk(
        self,
        recipients: list[Recipient],
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> list[ProviderDeliveryResult]:
        addresses = [r.address for r in recipients if r.address]
        if not addresses:
            return [
                ProviderDeliveryResult(
                    success=False,
                    channel=self.channel,
                    provider=self.name,
                    error="no recipients",
                    retryable=False,
                ),
            ]
        subject = self._default_subject(message)
        body = self._body_for(message, with_attachment_links=True)
        kwargs: dict[str, Any] = {}
        if message.format == ContentFormat.HTML:
            kwargs["html"] = body
        else:
            kwargs["text"] = body
        try:
            result = self._client.send(subject=subject, to=addresses, **kwargs)
            self.metrics.record_attempt(result.success)
            if result.success:
                return [
                    ProviderDeliveryResult(
                        success=True,
                        channel=self.channel,
                        provider=self.name,
                        delivery_ref=result.message_id,
                    )
                    for _ in recipients
                ]
            return [
                ProviderDeliveryResult(
                    success=False,
                    channel=self.channel,
                    provider=self.name,
                    error=result.error,
                    retryable=False,
                )
                for _ in recipients
            ]
        except Exception as exc:
            self.metrics.record_attempt(False)
            self.metrics.record_failure("exception")
            return [
                ProviderDeliveryResult(
                    success=False,
                    channel=self.channel,
                    provider=self.name,
                    error=self.redactor.redact(f"{type(exc).__name__}: {exc}"),
                    retryable=False,
                )
                for _ in recipients
            ]

    # ── internals ──────────────────────────────────────────────────────────

    def _attempt_deliver(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None,
    ) -> ProviderDeliveryResult:
        subject = self._default_subject(message)
        body = self._body_for(message, with_attachment_links=True)
        kwargs: dict[str, Any] = {"tags": [{"name": "priority", "value": self._priority_label(options)}]}
        if message.format == ContentFormat.HTML:
            kwargs["html"] = body
        else:
            kwargs["text"] = body
        try:
            result = self._client.send(subject=subject, to=[recipient.address], **kwargs)
        except Exception as exc:
            self.metrics.record_failure("exception")
            return self._result(
                success=False,
                error=f"{type(exc).__name__}: {exc}",
                retryable=False,
            )
        return self._result(
            success=result.success,
            delivery_ref=getattr(result, "message_id", "") or "",
            error=result.error,
            retryable=False,
        )

    def _body_for(self, message: OutboundMessage, *, with_attachment_links: bool) -> str:
        body = message.content
        if with_attachment_links:
            links = [
                a.reference for a in message.attachments if a.reference.startswith(("http://", "https://"))
            ]
            if links:
                body = f"{body}\n\n{chr(10).join(links)}"
        return body

    @staticmethod
    def _with_body(message: OutboundMessage, body: str) -> OutboundMessage:
        return OutboundMessage(
            content=body,
            format=message.format,
            subject=message.subject,
            locale=message.locale,
            template_id=message.template_id,
            template_version=message.template_version,
            attachments=message.attachments,
            metadata=message.metadata,
        )

    @staticmethod
    def _priority_label(options: ProviderOptions | None) -> str:
        return (options.priority if options else "normal") or "normal"


class ResendPlugin(ProviderPlugin):
    """Self-registering Resend provider plugin (env-only configuration)."""

    metadata = PluginMetadata(
        id="resend",
        version="1.0.0",
        description="Email delivery via Resend (wraps shared.notifications.resend)",
    )

    def __init__(self, resolver: SecretResolver | None = None) -> None:
        self._resolver = resolver or SecretResolver()

    def create_provider(self) -> ResendProvider:
        settings = ProviderSettings(
            name="resend",
            channel="email",
            timeout_seconds=float(self._resolver.get_int("RESEND_TIMEOUT_SECONDS", 30)),
            max_retries=0,  # retries live inside the Resend client
            rate_per_minute=self._resolver.get_int("RESEND_RATE_PER_MINUTE", 60),
            circuit_failure_threshold=self._resolver.get_int("RESEND_CIRCUIT_FAILURE_THRESHOLD", 5),
            circuit_recovery_timeout=float(self._resolver.get_int("RESEND_CIRCUIT_RECOVERY_TIMEOUT", 30)),
            enabled=self._resolver.get_bool("RESEND_ENABLED", True),
        )
        return ResendProvider(settings)

    def activate(self, context: dict[str, Any] | None = None) -> None:
        logger.info("communication_plugin_activate id=%s", self.metadata.id)

    def deactivate(self) -> None:
        logger.info("communication_plugin_deactivate id=%s", self.metadata.id)


def create_plugin() -> ResendPlugin:
    """Factory used by tests and entry-point consumers."""
    return ResendPlugin()


__all__ = ["ResendPlugin", "ResendProvider", "create_plugin"]