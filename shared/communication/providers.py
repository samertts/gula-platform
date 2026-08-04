"""Provider framework for the GULA Communication Platform Core.

The Core defines provider interfaces only. It never imports, knows, or
couples to any concrete provider (messaging services, email gateways,
webhooks, push services, …). Providers register themselves through the
plugin system; the Core routes through this registry.

Interface Segregation: a provider implements only the capability interfaces
it actually supports. Capability negotiation happens with ``isinstance``
against marker ABCs — adding a capability never changes existing providers.
"""

from __future__ import annotations

import contextlib
import enum
import logging
import threading
from abc import ABC, abstractmethod
from typing import Any, Protocol

from .model import (
    OutboundMessage,
    ProviderDeliveryResult,
    Recipient,
)

logger = logging.getLogger("gula.communication.providers")


class ChannelCapability(enum.StrEnum):
    """Capabilities a provider may advertise."""

    TEXT = "text"
    RICH_TEXT = "rich_text"  # html / markdown rendering support
    MEDIA = "media"  # photos, documents, attachments
    ALERT = "alert"  # severity-tagged alerts
    BULK = "bulk"  # multiple recipients in one call
    STATUS_CALLBACK = "status_callback"  # delivery → read/archived updates


class ProviderHealth(enum.StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"


class ProviderOptions(Protocol):
    """Per-attempt options resolved by the Policy Engine.

    Concrete options are provider-plugin concerns; the Core only passes
    them through (priority, retry budget, locale, quiet hours flag).
    """

    priority: str
    max_retries: int
    locale: str
    suppress_quiet_hours: bool


class ChannelProvider(ABC):
    """Base contract every communication provider must implement.

    ``name`` identifies the provider (e.g. ``ops_chat_bot``) and ``channel``
    is the logical channel family it serves (``chat``, ``email``,
    ``sms``, ``push``, ``webhook``, …). Multiple providers may serve one
    channel — the Policy Engine chooses among them.
    """

    name: str
    channel: str

    def health(self) -> ProviderHealth:
        """Return the provider health; defaults to OK."""
        return ProviderHealth.OK

    @abstractmethod
    def deliver(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        """Deliver one message to one recipient.

        Must return a result — never raise for delivery failures. Exceptions
        are bugs and are caught by the Core.
        """


class RichTextCapability(ABC):
    """Optional: provider can render HTML / Markdown content natively."""

    @abstractmethod
    def deliver_rich(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        """Deliver content in its native format (HTML/Markdown)."""


class MediaCapability(ABC):
    """Optional: provider can send attachments."""

    @abstractmethod
    def deliver_media(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        """Deliver the message together with its attachments."""


class AlertCapability(ABC):
    """Optional: provider supports severity-tagged alerts."""

    @abstractmethod
    def deliver_alert(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        severity: str,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        """Deliver a severity-tagged alert (info/warning/critical)."""


class BulkCapability(ABC):
    """Optional: provider can fan out to many recipients efficiently."""

    @abstractmethod
    def deliver_bulk(
        self,
        recipients: list[Recipient],
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> list[ProviderDeliveryResult]:
        """Deliver to many recipients; one result per recipient."""


class StatusCallbackCapability(ABC):
    """Optional: provider reports delivery status changes (read/archived)."""

    @abstractmethod
    def on_status_change(self, delivery_ref: str, status: str) -> None:
        """Receive a provider-reported status transition for a delivery."""


class ProviderRegistry:
    """Thread-safe registry mapping channel families to provider instances.

    The registry is the only object the Core consults to reach providers —
    it holds zero knowledge about provider implementations.
    """

    def __init__(self) -> None:
        self._by_channel: dict[str, list[ChannelProvider]] = {}
        self._by_name: dict[str, ChannelProvider] = {}
        self._lock = threading.Lock()

    def register(self, provider: ChannelProvider) -> None:
        if not provider.name or not provider.channel:
            raise ValueError("provider requires non-empty name and channel")
        with self._lock:
            if provider.name in self._by_name:
                raise ValueError(f"provider already registered: {provider.name}")
            self._by_name[provider.name] = provider
            self._by_channel.setdefault(provider.channel, []).append(provider)

    def unregister(self, name: str) -> bool:
        with self._lock:
            provider = self._by_name.pop(name, None)
            if provider is None:
                return False
            providers = self._by_channel.get(provider.channel, [])
            with contextlib.suppress(ValueError):
                providers.remove(provider)
            if not providers:
                self._by_channel.pop(provider.channel, None)
            return True

    def providers_for(self, channel: str) -> list[ChannelProvider]:
        with self._lock:
            return list(self._by_channel.get(channel, []))

    def get(self, name: str) -> ChannelProvider | None:
        with self._lock:
            return self._by_name.get(name)

    def all(self) -> list[ChannelProvider]:
        with self._lock:
            return list(self._by_name.values())

    def channels(self) -> list[str]:
        with self._lock:
            return sorted(self._by_channel)

    def supports(self, provider: ChannelProvider, capability: ChannelCapability) -> bool:
        checks: dict[ChannelCapability, type] = {
            ChannelCapability.RICH_TEXT: RichTextCapability,
            ChannelCapability.MEDIA: MediaCapability,
            ChannelCapability.ALERT: AlertCapability,
            ChannelCapability.BULK: BulkCapability,
            ChannelCapability.STATUS_CALLBACK: StatusCallbackCapability,
        }
        target = checks.get(capability)
        return isinstance(provider, target) if target else capability == ChannelCapability.TEXT

    def describe(self) -> list[dict[str, Any]]:
        """Snapshot of registered providers (health check / observability)."""
        out = []
        for provider in self.all():
            caps = [
                c.value
                for c in ChannelCapability
                if self.supports(provider, c)
            ]
            try:
                health = provider.health().value
            except Exception:
                health = ProviderHealth.DOWN.value
            out.append(
                {
                    "name": provider.name,
                    "channel": provider.channel,
                    "capabilities": caps,
                    "health": health,
                },
            )
        return out


__all__ = [
    "AlertCapability",
    "BulkCapability",
    "ChannelCapability",
    "ChannelProvider",
    "MediaCapability",
    "ProviderHealth",
    "ProviderOptions",
    "ProviderRegistry",
    "RichTextCapability",
    "StatusCallbackCapability",
]
