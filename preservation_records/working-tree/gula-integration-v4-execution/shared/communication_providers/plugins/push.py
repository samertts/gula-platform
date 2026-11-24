"""Push notification provider — abstraction only (PROGRAM-COMM-002).

The push channel is a PLACEHOLDER abstraction: no concrete push vendor
(FCM / APNS / Expo) ships with this package. Third parties implement the
contract in their own plugin; ``NoopPushProvider`` provides the fallback
behaviour so failover chains that include ``push`` terminate gracefully.
"""

from __future__ import annotations

import logging
from typing import Any

from shared.communication.model import OutboundMessage, ProviderDeliveryResult, Recipient
from shared.communication.plugins import PluginMetadata, ProviderPlugin

from ..base import BaseChannelProvider, ProviderSettings

logger = logging.getLogger("gula.communication.providers.push")


class PushProvider(BaseChannelProvider):
    """Abstract base for concrete push vendors (FCM, APNS, Expo, …).

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
            "PushProvider is an abstraction: implement a concrete push vendor plugin",
        )


class NoopPushProvider(PushProvider):
    """Default push provider: exists so policy fallback plans can include
    the ``push`` channel; delivery fails cleanly and the Policy Engine moves
    to the next channel."""

    def __init__(self, settings: ProviderSettings | None = None) -> None:
        super().__init__(
            settings
            or ProviderSettings(
                name="noop_push",
                channel="push",
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
            error="push provider not implemented (abstraction only)",
            retryable=False,
        )


class NoopPushPlugin(ProviderPlugin):
    """Registers the abstract push channel placeholder."""

    metadata = PluginMetadata(
        id="push",
        version="1.0.0",
        description="Push notification channel abstraction (no vendor shipped)",
    )

    def create_provider(self) -> NoopPushProvider:
        return NoopPushProvider()

    def activate(self, context: dict[str, Any] | None = None) -> None:
        logger.info("communication_plugin_activate id=%s", self.metadata.id)

    def deactivate(self) -> None:
        logger.info("communication_plugin_deactivate id=%s", self.metadata.id)


def create_plugin() -> NoopPushPlugin:
    return NoopPushPlugin()


__all__ = ["NoopPushPlugin", "NoopPushProvider", "PushProvider", "create_plugin"]
