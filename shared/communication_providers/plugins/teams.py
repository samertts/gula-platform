"""Microsoft Teams webhook provider plugin (PROGRAM-COMM-002).

Delivers through a Teams workflow webhook (MessageCard / Adaptive Card)
over the shared HttpTransport: plain text cards, HTML-rich cards,
severity-coloured alerts. Attachments are rendered as links when they are
HTTP(S) references (workflow webhooks cannot upload files).
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
    ProviderOptions,
    RichTextCapability,
)

from ..base import BaseChannelProvider, ProviderSettings, Redactor
from ..secrets import SecretResolver
from ..transport import TransportResponse
from ._webhook_common import build_transport, resolve_webhook_url

logger = logging.getLogger("gula.communication.providers.teams")

_THEME_COLORS = {
    "critical": "FF0000",
    "warning": "FFA500",
    "info": "0078D4",
}


class TeamsProvider(BaseChannelProvider, RichTextCapability, AlertCapability):
    """Microsoft Teams delivery via workflow webhook (channel ``teams``)."""

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
        card = _message_card(message, message.content)
        response = self._transport.request("POST", self._webhook_url, json=card)
        return self._map(response)

    def deliver_rich(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        body = message.content
        if message.format == ContentFormat.HTML:
            body = _sanitize_teams_html(body)
        card = _message_card(message, body)
        response = self._transport.request("POST", self._webhook_url, json=card)
        return self._map(response)

    def deliver_alert(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        severity: str,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        card = _message_card(message, message.content)
        card["themeColor"] = _THEME_COLORS.get(severity.lower(), "0078D4")
        response = self._transport.request("POST", self._webhook_url, json=card)
        return self._map(response)

    # ── helpers ────────────────────────────────────────────────────────────

    def _map(self, response: TransportResponse) -> ProviderDeliveryResult:
        if response.ok:
            return self._result(success=True, delivery_ref=f"teams-{len(response.request_id)}")
        if response.status_code == 0:
            return self._result(
                success=False, error=response.text or "network failure", retryable=True
            )
        return self._result(
            success=False,
            error=f"teams webhook rejected: {response.status_code}",
            retryable=response.status_code >= 500,
        )


class TeamsPlugin(ProviderPlugin):
    """Self-registering Microsoft Teams webhook provider plugin."""

    metadata = PluginMetadata(
        id="teams",
        version="1.0.0",
        description="Microsoft Teams delivery via workflow webhook",
    )

    def __init__(self, resolver: SecretResolver | None = None) -> None:
        self._resolver = resolver or SecretResolver()

    def create_provider(self) -> TeamsProvider:
        settings = ProviderSettings(
            name="teams",
            channel="teams",
            timeout_seconds=float(self._resolver.get_int("TEAMS_TIMEOUT_SECONDS", 10)),
            max_retries=self._resolver.get_int("TEAMS_MAX_RETRIES", 2),
            rate_per_minute=self._resolver.get_int("TEAMS_RATE_PER_MINUTE", 60),
            circuit_failure_threshold=self._resolver.get_int("TEAMS_CIRCUIT_FAILURE_THRESHOLD", 5),
            circuit_recovery_timeout=float(
                self._resolver.get_int("TEAMS_CIRCUIT_RECOVERY_TIMEOUT", 30)
            ),
            enabled=self._resolver.get_bool("TEAMS_ENABLED", True),
        )
        webhook_url = resolve_webhook_url("teams", self._resolver)
        return TeamsProvider(settings, webhook_url=webhook_url)

    def activate(self, context: dict[str, Any] | None = None) -> None:
        logger.info("communication_plugin_activate id=%s", self.metadata.id)

    def deactivate(self) -> None:
        logger.info("communication_plugin_deactivate id=%s", self.metadata.id)


def create_plugin() -> TeamsPlugin:
    return TeamsPlugin()


def _message_card(message: OutboundMessage, body: str) -> dict[str, Any]:
    """Build a legacy MessageCard payload (Teams workflow webhook v1)."""
    attachments_links = [
        a.reference for a in message.attachments if a.reference.startswith(("http://", "https://"))
    ]
    text = body
    if attachments_links:
        text = f"{text}\n\n{chr(10).join(attachments_links)}"
    return {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": message.subject or "GULA notification",
        "title": message.subject or "",
        "text": text[:28000],
    }


def _sanitize_teams_html(html: str) -> str:
    """Teams cards render a limited HTML subset; drop unsafe tags."""
    import re

    return re.sub(
        r"<(script|style|iframe|object|embed)[^>]*>.*?</\1>",
        "",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )


__all__ = ["TeamsPlugin", "TeamsProvider", "create_plugin"]
