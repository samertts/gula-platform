"""SMS provider — abstraction only (PROGRAM-COMM-002).

The SMS channel is a PLACEHOLDER abstraction: no concrete SMS vendor
(Twilio, MessageBird, local aggregator) ships with this package. Third
parties implement the contract in their own plugin; ``NoopSmsProvider``
provides graceful failover behaviour.
"""

from __future__ import annotations

import logging
from typing import Any

from shared.communication.model import OutboundMessage, ProviderDeliveryResult, Recipient
from shared.communication.plugins import PluginMetadata, ProviderPlugin

from ..base import BaseChannelProvider, ProviderSettings

logger = logging.getLogger("gula.communication.providers.sms")


class SmsProvider(BaseChannelProvider):
    """Abstract base for concrete SMS vendors.

    Subclass, implement :meth:`deliver` and register through the plugin
    system — the Communication Core never changes.
    """

    def __init__(self, settings: ProviderSettings) -> None:
        super().__init__(settings)

    def deliver(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: Any = None,
    ) -> ProviderDeliveryResult:
        raise NotImplementedError(
            "SmsProvider is an abstraction: implement a concrete SMS vendor plugin",
        )


class NoopSmsProvider(SmsProvider):
    """Default SMS provider: delivery fails cleanly so failover continues."""

    def __init__(self, settings: ProviderSettings | None = None) -> None:
        super().__init__(
            settings
            or ProviderSettings(
                name="noop_sms",
                channel="sms",
                enabled=True,
            ),
        )

    @property
    def is_configured(self) -> bool:
        return False

    def deliver(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: Any = None,
    ) -> ProviderDeliveryResult:
        return self._result(
            success=False,
            error="sms provider not implemented (abstraction only)",
            retryable=False,
        )


class NoopSmsPlugin(ProviderPlugin):
    """Registers the abstract SMS channel placeholder."""

    metadata = PluginMetadata(
        id="sms",
        version="1.0.0",
        description="SMS channel abstraction (no vendor shipped)",
    )

    def create_provider(self) -> NoopSmsProvider:
        return NoopSmsProvider()

    def activate(self, context: dict[str, Any] | None = None) -> None:
        logger.info("communication_plugin_activate id=%s", self.metadata.id)

    def deactivate(self) -> None:
        logger.info("communication_plugin_deactivate id=%s", self.metadata.id)


def create_plugin() -> NoopSmsPlugin:
    return NoopSmsPlugin()


__all__ = ["NoopSmsPlugin", "NoopSmsProvider", "SmsProvider", "create_plugin"]
