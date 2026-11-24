"""In-app notification provider plugin (PROGRAM-COMM-002).

The ultimate failover channel: delivery never leaves the platform and
always succeeds locally. Deliveries are recorded into an injectable sink
(``InAppSink`` protocol); the default is an in-memory ring buffer, and the
platform composition root can bind a durable sink (outbox table, WebSocket
fan-out, …) without touching the Core.
"""

from __future__ import annotations

import logging
import threading
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Protocol

from shared.communication.model import OutboundMessage, ProviderDeliveryResult, Recipient
from shared.communication.plugins import PluginMetadata, ProviderPlugin
from shared.communication.providers import (
    MediaCapability,
    ProviderOptions,
    RichTextCapability,
    StatusCallbackCapability,
)

from ..base import BaseChannelProvider, ProviderSettings

logger = logging.getLogger("gula.communication.providers.inapp")


class InAppSink(Protocol):
    """Receives in-app notifications. Implemented outside the Core."""

    def record(self, delivery_ref: str, recipient: str, message: OutboundMessage) -> None: ...


@dataclass
class InAppRecord:
    delivery_ref: str
    recipient: str
    content: str
    format: str
    subject: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class InMemoryInAppSink:
    """Thread-safe ring buffer used as the default in-app sink."""

    def __init__(self, max_entries: int = 200) -> None:
        self._entries: deque[InAppRecord] = deque(maxlen=max_entries)
        self._lock = threading.Lock()

    def record(self, delivery_ref: str, recipient: str, message: OutboundMessage) -> None:
        with self._lock:
            self._entries.append(
                InAppRecord(
                    delivery_ref=delivery_ref,
                    recipient=recipient,
                    content=message.content,
                    format=message.format.value,
                    subject=message.subject,
                    metadata=dict(message.metadata),
                ),
            )

    def snapshot(self) -> list[dict[str, Any]]:
        with self._lock:
            return [r.__dict__ for r in list(self._entries)]


class InAppProvider(
    BaseChannelProvider, RichTextCapability, MediaCapability, StatusCallbackCapability
):
    """In-platform notification delivery (channel ``inapp``)."""

    def __init__(self, settings: ProviderSettings, sink: InAppSink | None = None) -> None:
        super().__init__(settings)
        self._sink = sink or InMemoryInAppSink()
        self.status_changes: list[tuple[str, str]] = []

    @property
    def is_configured(self) -> bool:
        return True

    def deliver(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        return self._deliver_protected(recipient, message, options, self._attempt)

    def deliver_rich(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        return self._deliver_protected(recipient, message, options, self._attempt)

    def deliver_media(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        return self._deliver_protected(recipient, message, options, self._attempt)

    def on_status_change(self, delivery_ref: str, status: str) -> None:
        self.status_changes.append((delivery_ref, status))

    def _attempt(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None,
    ) -> ProviderDeliveryResult:
        delivery_ref = f"inapp-{uuid.uuid4().hex[:12]}"
        try:
            self._sink.record(delivery_ref, recipient.address, message)
        except Exception as exc:
            return self._result(success=False, error=f"inapp sink failure: {exc}", retryable=False)
        return self._result(success=True, delivery_ref=delivery_ref)


class InAppPlugin(ProviderPlugin):
    """Self-registering in-app notification provider plugin."""

    metadata = PluginMetadata(
        id="inapp",
        version="1.0.0",
        description="In-platform notification channel (ultimate failover)",
    )

    def __init__(self, sink: InAppSink | None = None) -> None:
        self._sink = sink

    def create_provider(self) -> InAppProvider:
        return InAppProvider(
            ProviderSettings(name="inapp", channel="inapp", enabled=True),
            sink=self._sink,
        )

    def activate(self, context: dict[str, Any] | None = None) -> None:
        logger.info("communication_plugin_activate id=%s", self.metadata.id)

    def deactivate(self) -> None:
        logger.info("communication_plugin_deactivate id=%s", self.metadata.id)


def create_plugin() -> InAppPlugin:
    return InAppPlugin()


__all__ = ["InAppPlugin", "InAppProvider", "InAppRecord", "InMemoryInAppSink", "create_plugin"]
