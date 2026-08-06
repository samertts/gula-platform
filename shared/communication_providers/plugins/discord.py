"""Discord webhook provider plugin (PROGRAM-COMM-002).

Delivers through a Discord incoming webhook over the shared HttpTransport:
plain text, rich embeds, severity-coloured alerts, file attachments and
status callbacks. The webhook URL (which embeds a token) is treated as a
secret — loaded from env/docker/k8s only and redacted everywhere.
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
    MediaCapability,
    ProviderOptions,
    RichTextCapability,
    StatusCallbackCapability,
)

from ..base import BaseChannelProvider, ProviderSettings, Redactor
from ..secrets import SecretResolver
from ..transport import TransportResponse
from ._webhook_common import (
    attachment_bytes,
    attachment_filename,
    build_transport,
    resolve_webhook_url,
)

logger = logging.getLogger("gula.communication.providers.discord")

_DISCORD_BASE_URL = "https://discord.com/api/webhooks"

_COLORS = {
    "critical": 15548997,  # red
    "warning": 16705372,  # yellow
    "info": 3066993,  # green
}
_PRIORITY_COLORS = {
    "low": 9868954,
    "normal": 3066993,
    "high": 15105570,
    "urgent": 16705372,
    "mandatory": 15548997,
}


class DiscordProvider(
    BaseChannelProvider,
    RichTextCapability,
    MediaCapability,
    AlertCapability,
    StatusCallbackCapability,
):
    """Discord delivery via incoming webhook (channel ``discord``)."""

    def __init__(
        self,
        settings: ProviderSettings,
        *,
        webhook_url: str,
        http_client: Any = None,
    ) -> None:
        redactor = Redactor()
        redactor.register(webhook_url)
        super().__init__(settings, redactor=redactor)
        self._webhook_url = webhook_url
        self._transport = build_transport(settings, redactor=redactor, http_client=http_client)
        self.status_changes: list[tuple[str, str]] = []

    @property
    def is_configured(self) -> bool:
        return bool(self._webhook_url)

    def health(self) -> Any:
        from shared.communication.providers import ProviderHealth

        if not self.is_configured or not self._settings.enabled:
            return ProviderHealth.DOWN
        if self._transport._circuit.state.value == "OPEN":
            return ProviderHealth.DOWN
        return ProviderHealth.OK

    # ── delivery ───────────────────────────────────────────────────────────

    def deliver(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        response = self._transport.request(
            "POST",
            self._webhook_url,
            json={"content": message.content},
        )
        return self._map(response)

    def deliver_rich(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        description = message.content
        if message.format == ContentFormat.HTML:
            description = _strip_html(description)
        embed: dict[str, Any] = {"description": description[:2000]}
        if message.subject:
            embed["title"] = message.subject[:256]
        embed["color"] = _PRIORITY_COLORS.get(
            (options.priority if options else "") or "normal",
            _COLORS["info"],
        )
        response = self._transport.request(
            "POST",
            self._webhook_url,
            json={"embeds": [embed]},
        )
        return self._map(response)

    def deliver_media(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        if not message.attachments:
            return self._result(success=False, error="no attachments", retryable=False)
        try:
            payload = {
                f"files[{index}]": (
                    attachment_filename(a),
                    attachment_bytes(a),
                    a.mime_type or "application/octet-stream",
                )
                for index, a in enumerate(message.attachments[:10])
            }
        except OSError as exc:
            return self._result(
                success=False, error=f"attachment unreadable: {exc}", retryable=False
            )
        response = self._transport.request(
            "POST",
            self._webhook_url,
            files=payload,
        )
        return self._map(response)

    def deliver_alert(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        severity: str,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        color = _COLORS.get(severity.lower(), _COLORS["info"])
        description = (
            _strip_html(message.content)
            if message.format == ContentFormat.HTML
            else message.content
        )
        response = self._transport.request(
            "POST",
            self._webhook_url,
            json={
                "embeds": [
                    {
                        "title": message.subject or f"[{severity.upper()}]",
                        "description": description[:2000],
                        "color": color,
                    },
                ],
            },
        )
        return self._map(response)

    def on_status_change(self, delivery_ref: str, status: str) -> None:
        self.status_changes.append((delivery_ref, status))

    # ── helpers ────────────────────────────────────────────────────────────

    def _map(self, response: TransportResponse) -> ProviderDeliveryResult:
        if response.ok:
            return self._result(success=True, delivery_ref=f"discord-{len(self.status_changes)}")
        if response.status_code == 429:
            return self._result(success=False, error="discord rate limited", retryable=True)
        if response.status_code == 0:
            return self._result(
                success=False, error=response.text or "network failure", retryable=True
            )
        return self._result(
            success=False,
            error=f"discord webhook rejected: {response.status_code}",
            retryable=response.status_code >= 500,
        )


class DiscordPlugin(ProviderPlugin):
    """Self-registering Discord webhook provider plugin."""

    metadata = PluginMetadata(
        id="discord",
        version="1.0.0",
        description="Discord delivery via incoming webhook",
    )

    def __init__(self, resolver: SecretResolver | None = None) -> None:
        self._resolver = resolver or SecretResolver()

    def create_provider(self) -> DiscordProvider:
        settings = ProviderSettings(
            name="discord",
            channel="discord",
            timeout_seconds=float(self._resolver.get_int("DISCORD_TIMEOUT_SECONDS", 10)),
            max_retries=self._resolver.get_int("DISCORD_MAX_RETRIES", 2),
            rate_per_minute=self._resolver.get_int("DISCORD_RATE_PER_MINUTE", 30),
            circuit_failure_threshold=self._resolver.get_int(
                "DISCORD_CIRCUIT_FAILURE_THRESHOLD", 5
            ),
            circuit_recovery_timeout=float(
                self._resolver.get_int("DISCORD_CIRCUIT_RECOVERY_TIMEOUT", 30)
            ),
            enabled=self._resolver.get_bool("DISCORD_ENABLED", True),
        )
        webhook_url = resolve_webhook_url("discord", self._resolver)
        return DiscordProvider(settings, webhook_url=webhook_url)

    def activate(self, context: dict[str, Any] | None = None) -> None:
        logger.info("communication_plugin_activate id=%s", self.metadata.id)

    def deactivate(self) -> None:
        logger.info("communication_plugin_deactivate id=%s", self.metadata.id)


def create_plugin() -> DiscordPlugin:
    return DiscordPlugin()


def _strip_html(html: str) -> str:
    import re

    return (
        re.sub(r"<[^>]+>", "", html).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    )


__all__ = ["DiscordPlugin", "DiscordProvider", "create_plugin"]
