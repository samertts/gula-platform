"""Slack webhook provider plugin (PROGRAM-COMM-002).

Delivers through a Slack incoming webhook over the shared HttpTransport:
plain text, mrkdwn-rich blocks, alert messages and (when a bot token is
configured) file uploads. The webhook URL and bot token are secrets — loaded
from env/docker/k8s only and redacted everywhere.
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

logger = logging.getLogger("gula.communication.providers.slack")


class SlackProvider(BaseChannelProvider, RichTextCapability, AlertCapability, MediaCapability):
    """Slack delivery via incoming webhook (channel ``slack``)."""

    def __init__(
        self,
        settings: ProviderSettings,
        *,
        webhook_url: str,
        api_token: str = "",
        http_client: Any = None,
    ) -> None:
        redactor = Redactor()
        redactor.register(webhook_url)
        redactor.register(api_token)
        super().__init__(settings, redactor=redactor)
        self._webhook_url = webhook_url
        self._api_token = api_token
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
        response = self._transport.request(
            "POST", self._webhook_url, json={"text": message.content}
        )
        return self._map(response)

    def deliver_rich(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        text = message.content
        if message.format == ContentFormat.HTML:
            text = _strip_html(text)
        payload: dict[str, Any] = {
            "text": message.subject or text[:1000],
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn" if message.format != ContentFormat.HTML else "plain_text",
                        "text": text[:3000],
                    },
                },
            ],
        }
        response = self._transport.request("POST", self._webhook_url, json=payload)
        return self._map(response)

    def deliver_alert(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        severity: str,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        prefix = {
            "critical": ":rotating_light:",
            "warning": ":warning:",
            "info": ":information_source:",
        }.get(
            severity.lower(),
            ":bell:",
        )
        text = message.content
        if message.format == ContentFormat.HTML:
            text = _strip_html(text)
        response = self._transport.request(
            "POST",
            self._webhook_url,
            json={"text": f"{prefix} *{message.subject or severity.upper()}*\n{text[:2000]}"},
        )
        return self._map(response)

    def deliver_media(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        if not self._api_token:
            return self._result(
                success=False,
                error="slack file upload requires SLACK_API_TOKEN",
                retryable=False,
            )
        if not message.attachments:
            return self._result(success=False, error="no attachments", retryable=False)
        attachment = message.attachments[0]
        try:
            payload = attachment_bytes(attachment)
        except OSError as exc:
            return self._result(
                success=False, error=f"attachment unreadable: {exc}", retryable=False
            )
        response = self._transport.request(
            "POST",
            "https://slack.com/api/files.upload",
            headers={"Authorization": f"Bearer {self._api_token}"},
            files={
                "file": (
                    attachment_filename(attachment),
                    payload,
                    attachment.mime_type or "application/octet-stream",
                ),
                "channels": (None, recipient.address, "text/plain"),
            },
        )
        if response.ok:
            body = response.json or {}
            if isinstance(body, dict) and body.get("ok") is not True:
                return self._result(success=False, error="slack upload rejected", retryable=False)
            return self._result(success=True, delivery_ref=f"slack-file-{len(self.status_changes)}")
        return self._result(
            success=False,
            error=f"slack upload failed: {response.status_code}",
            retryable=response.status_code >= 500,
        )

    def on_status_change(self, delivery_ref: str, status: str) -> None:
        self.status_changes.append((delivery_ref, status))

    # ── helpers ────────────────────────────────────────────────────────────

    def _map(self, response: TransportResponse) -> ProviderDeliveryResult:
        if response.ok:
            return self._result(success=True, delivery_ref=f"slack-{len(self.status_changes)}")
        if response.status_code == 0:
            return self._result(
                success=False, error=response.text or "network failure", retryable=True
            )
        return self._result(
            success=False,
            error=f"slack webhook rejected: {response.status_code}",
            retryable=response.status_code >= 500,
        )


class SlackPlugin(ProviderPlugin):
    """Self-registering Slack webhook provider plugin."""

    metadata = PluginMetadata(
        id="slack",
        version="1.0.0",
        description="Slack delivery via incoming webhook (+ optional bot token)",
    )

    def __init__(self, resolver: SecretResolver | None = None) -> None:
        self._resolver = resolver or SecretResolver()

    def create_provider(self) -> SlackProvider:
        settings = ProviderSettings(
            name="slack",
            channel="slack",
            timeout_seconds=float(self._resolver.get_int("SLACK_TIMEOUT_SECONDS", 10)),
            max_retries=self._resolver.get_int("SLACK_MAX_RETRIES", 2),
            rate_per_minute=self._resolver.get_int("SLACK_RATE_PER_MINUTE", 60),
            circuit_failure_threshold=self._resolver.get_int("SLACK_CIRCUIT_FAILURE_THRESHOLD", 5),
            circuit_recovery_timeout=float(
                self._resolver.get_int("SLACK_CIRCUIT_RECOVERY_TIMEOUT", 30)
            ),
            enabled=self._resolver.get_bool("SLACK_ENABLED", True),
        )
        webhook_url = resolve_webhook_url("slack", self._resolver)
        api_token = self._resolver.resolve(
            type(
                "S", (), {"env_names": ("SLACK_API_TOKEN",), "file_names": ("slack_api_token",)}
            )(),
        )
        return SlackProvider(settings, webhook_url=webhook_url, api_token=api_token)

    def activate(self, context: dict[str, Any] | None = None) -> None:
        logger.info("communication_plugin_activate id=%s", self.metadata.id)

    def deactivate(self) -> None:
        logger.info("communication_plugin_deactivate id=%s", self.metadata.id)


def create_plugin() -> SlackPlugin:
    return SlackPlugin()


def _strip_html(html: str) -> str:
    import re

    return (
        re.sub(r"<[^>]+>", "", html).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    )


__all__ = ["SlackPlugin", "SlackProvider", "create_plugin"]
