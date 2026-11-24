"""Generic webhook provider plugin (PROGRAM-COMM-002).

Delivers a structured JSON payload to any HTTP(S) endpoint:

  - recipient.address is used as the webhook URL when it starts with
    ``http(s)://``; otherwise a configured ``WEBHOOK_URL`` base is used and
    the address is appended as a path.
  - Optional HMAC-SHA256 signature header (``X-GULA-Signature``) and bearer
    token for authenticated sinks.
  - Attachments are forwarded as URL references in the payload (no upload).

This is the escape hatch for "any other system": ops webhooks, HTTP
gateways, future enterprise integrations — no Core change required.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
import uuid
from typing import Any

from shared.communication.model import (
    ContentFormat,
    OutboundMessage,
    ProviderDeliveryResult,
    Recipient,
)
from shared.communication.plugins import PluginMetadata, ProviderPlugin
from shared.communication.providers import (
    MediaCapability,
    ProviderOptions,
    RichTextCapability,
    StatusCallbackCapability,
)

from ..base import BaseChannelProvider, ProviderSettings, Redactor
from ..secrets import SecretResolver
from ..transport import TransportResponse
from ._webhook_common import build_transport

logger = logging.getLogger("gula.communication.providers.webhook")

_SIGNATURE_HEADER = "X-GULA-Signature"


class WebhookProvider(
    BaseChannelProvider,
    RichTextCapability,
    MediaCapability,
    StatusCallbackCapability,
):
    """Generic HTTP(S) webhook delivery (channel ``webhook``)."""

    def __init__(
        self,
        settings: ProviderSettings,
        *,
        base_url: str = "",
        auth_token: str = "",
        signing_secret: str = "",
        http_client: Any = None,
    ) -> None:
        redactor = Redactor()
        redactor.register(base_url)
        redactor.register(auth_token)
        redactor.register(signing_secret)
        super().__init__(settings, redactor=redactor)
        self._base_url = base_url.rstrip("/") if base_url else ""
        self._auth_token = auth_token
        self._signing_secret = signing_secret
        self._transport = build_transport(settings, redactor=redactor, http_client=http_client)
        self.status_changes: list[tuple[str, str]] = []

    @property
    def is_configured(self) -> bool:
        return bool(self._base_url)

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
        return self._send(recipient, message, options)

    def deliver_rich(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        return self._send(recipient, message, options)

    def deliver_media(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        return self._send(recipient, message, options)

    def on_status_change(self, delivery_ref: str, status: str) -> None:
        self.status_changes.append((delivery_ref, status))

    # ── internals ──────────────────────────────────────────────────────────

    def _send(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None,
    ) -> ProviderDeliveryResult:
        url = self._url_for(recipient.address)
        if not url:
            return self._result(
                success=False,
                error="webhook provider not configured (WEBHOOK_URL) and recipient is not a URL",
                retryable=False,
            )
        delivery_ref = f"wh-{uuid.uuid4().hex[:12]}"
        payload: dict[str, Any] = {
            "delivery_ref": delivery_ref,
            "recipient": recipient.address,
            "subject": message.subject,
            "content": message.content,
            "format": message.format.value
            if isinstance(message.format, ContentFormat)
            else str(message.format),
            "priority": (options.priority if options else "") or "normal",
            "timestamp": time.time(),
            "metadata": message.metadata,
        }
        if message.format == ContentFormat.HTML:
            payload["html"] = message.content
        elif message.format == ContentFormat.MARKDOWN:
            payload["markdown"] = message.content
        if message.attachments:
            payload["attachments"] = [
                {
                    "reference": a.reference,
                    "name": a.name,
                    "mime_type": a.mime_type,
                    "kind": a.kind,
                }
                for a in message.attachments
            ]
        headers: dict[str, str] = {}
        if self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"
        if self._signing_secret:
            headers[_SIGNATURE_HEADER] = _sign_payload(payload, self._signing_secret)
        response = self._transport.request("POST", url, json=payload, headers=headers)
        return self._map(response, delivery_ref)

    def _url_for(self, address: str) -> str:
        if address.startswith(("http://", "https://")):
            return address
        if not self._base_url:
            return ""
        return f"{self._base_url}/{address.lstrip('/')}" if address else self._base_url

    def _map(self, response: TransportResponse, delivery_ref: str) -> ProviderDeliveryResult:
        if response.ok:
            return self._result(success=True, delivery_ref=delivery_ref)
        if response.status_code == 0:
            return self._result(
                success=False, error=response.text or "network failure", retryable=True
            )
        if response.status_code == 429:
            return self._result(success=False, error="webhook rate limited", retryable=True)
        return self._result(
            success=False,
            error=f"webhook rejected: {response.status_code}",
            retryable=response.status_code >= 500,
            delivery_ref=delivery_ref,
        )


class WebhookPlugin(ProviderPlugin):
    """Self-registering generic webhook provider plugin."""

    metadata = PluginMetadata(
        id="webhook",
        version="1.0.0",
        description="Generic HTTP(S) webhook delivery",
    )

    def __init__(self, resolver: SecretResolver | None = None) -> None:
        self._resolver = resolver or SecretResolver()

    def create_provider(self) -> WebhookProvider:
        settings = ProviderSettings(
            name="webhook",
            channel="webhook",
            timeout_seconds=float(self._resolver.get_int("WEBHOOK_TIMEOUT_SECONDS", 10)),
            max_retries=self._resolver.get_int("WEBHOOK_MAX_RETRIES", 2),
            rate_per_minute=self._resolver.get_int("WEBHOOK_RATE_PER_MINUTE", 120),
            circuit_failure_threshold=self._resolver.get_int(
                "WEBHOOK_CIRCUIT_FAILURE_THRESHOLD", 5
            ),
            circuit_recovery_timeout=float(
                self._resolver.get_int("WEBHOOK_CIRCUIT_RECOVERY_TIMEOUT", 30)
            ),
            enabled=self._resolver.get_bool("WEBHOOK_ENABLED", True),
        )
        base_url = self._resolver.resolve(
            type("S", (), {"env_names": ("WEBHOOK_URL",), "file_names": ("webhook_url",)})(),
        )
        auth_token = self._resolver.resolve(
            type(
                "S",
                (),
                {"env_names": ("WEBHOOK_AUTH_TOKEN",), "file_names": ("webhook_auth_token",)},
            )(),
        )
        signing_secret = self._resolver.resolve(
            type(
                "S",
                (),
                {
                    "env_names": ("WEBHOOK_SIGNING_SECRET",),
                    "file_names": ("webhook_signing_secret",),
                },
            )(),
        )
        return WebhookProvider(
            settings,
            base_url=base_url,
            auth_token=auth_token,
            signing_secret=signing_secret,
        )

    def activate(self, context: dict[str, Any] | None = None) -> None:
        logger.info("communication_plugin_activate id=%s", self.metadata.id)

    def deactivate(self) -> None:
        logger.info("communication_plugin_deactivate id=%s", self.metadata.id)


def create_plugin() -> WebhookPlugin:
    return WebhookPlugin()


def _sign_payload(payload: dict[str, Any], secret: str) -> str:
    """HMAC-SHA256 of the canonical JSON payload for sink verification."""
    import json

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hmac.new(secret.encode(), canonical, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


__all__ = ["WebhookPlugin", "WebhookProvider", "create_plugin"]
