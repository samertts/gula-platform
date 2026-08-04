"""Test doubles for the Communication Platform Core tests.

These are TEST-ONLY fakes — deliberately shipped in the test package, never
in the Core. They exercise the provider/plugin/queue/state interfaces as a
third party would (contract tests).
"""

from __future__ import annotations

from typing import Any

from shared.communication.audit import AuditEvent
from shared.communication.model import (
    ContentFormat,
    OutboundMessage,
    ProviderDeliveryResult,
    Recipient,
)
from shared.communication.plugins import PluginMetadata, ProviderPlugin
from shared.communication.policy import RecipientPreferences
from shared.communication.providers import (
    AlertCapability,
    BulkCapability,
    ChannelProvider,
    MediaCapability,
    ProviderHealth,
    ProviderOptions,
    RichTextCapability,
    StatusCallbackCapability,
)
from shared.communication.queue import DeliveryJob
from shared.communication.state import DeliveryRecord, DeliveryState, StateStore


class RecordingAuditSink:
    """Captures every audit event for assertions."""

    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        self.events.append(event)

    def actions(self) -> list[str]:
        return [e.action.value for e in self.events]

    def count(self, action: str) -> int:
        return sum(1 for e in self.events if e.action.value == action)


class InMemoryStateStore(StateStore):
    """In-memory StateStore implementation (test double)."""

    def __init__(self) -> None:
        self.records: dict[str, DeliveryRecord] = {}

    def save(self, record: DeliveryRecord) -> None:
        self.records[record.delivery_id] = record

    def get(self, delivery_id: str) -> DeliveryRecord | None:
        return self.records.get(delivery_id)

    def update_state(
        self,
        delivery_id: str,
        state: DeliveryState,
        error: str | None = None,
    ) -> bool:
        record = self.records.get(delivery_id)
        if record is None:
            return False
        record.state = state
        record.error = error
        return True


class InMemoryDeliveryQueue:
    """Test double implementing the DeliveryQueue protocol."""

    def __init__(self) -> None:
        self.jobs: list[DeliveryJob] = []
        self.dead: list[tuple[str, str]] = []
        self.requeued: list[tuple[str, str]] = []
        self.acked: list[str] = []

    async def enqueue(self, job: DeliveryJob) -> None:
        self.jobs.append(job)

    async def dequeue(self, timeout: int = 5) -> DeliveryJob | None:
        return self.jobs.pop(0) if self.jobs else None

    async def ack(self, job_id: str) -> None:
        self.acked.append(job_id)

    async def requeue(self, job_id: str, error: str) -> None:
        self.requeued.append((job_id, error))

    async def dead_letter(self, job_id: str, error: str) -> None:
        self.dead.append((job_id, error))

    async def depth(self) -> int:
        return len(self.jobs)


class FakeProvider(ChannelProvider):
    """Configurable provider used across the suite.

    ``fail_on`` : set of delivery keys (or "always") that fail.
    ``fail_retryable`` : whether failed deliveries are marked retryable.
    """

    name = "fake"
    channel = "email"

    def __init__(
        self,
        *,
        name: str = "fake",
        channel: str = "email",
        health: ProviderHealth = ProviderHealth.OK,
        fail_on: set[str] | None = None,
        fail_retryable: bool = False,
    ) -> None:
        self.name = name
        self.channel = channel
        self._health = health
        self._fail_on = fail_on or set()
        self._fail_retryable = fail_retryable
        self.deliveries: list[tuple[Recipient, OutboundMessage]] = []
        self.calls: list[str] = []

    def health(self) -> ProviderHealth:
        return self._health

    def _make_result(self, success: bool, retryable: bool = False) -> ProviderDeliveryResult:
        if not success:
            return ProviderDeliveryResult(
                success=False,
                channel=self.channel,
                provider=self.name,
                error="fake failure",
                retryable=retryable,
            )
        return ProviderDeliveryResult(
            success=True,
            channel=self.channel,
            provider=self.name,
            delivery_ref=f"{self.name}-msg-{len(self.deliveries)}",
        )

    def deliver(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        self.calls.append("deliver")
        self.deliveries.append((recipient, message))
        if "always" in self._fail_on or "deliver" in self._fail_on:
            return ProviderDeliveryResult(
                success=False,
                channel=self.channel,
                provider=self.name,
                error="fake failure",
                retryable=self._fail_retryable,
            )
        return ProviderDeliveryResult(
            success=True,
            channel=self.channel,
            provider=self.name,
            delivery_ref=f"{self.name}-msg-{len(self.deliveries)}",
        )


class RichFakeProvider(FakeProvider, RichTextCapability):
    """Rich-capable provider defaulting to the chat channel."""

    def __init__(self, *, channel: str = "chat", **kwargs: Any) -> None:
        super().__init__(channel=channel, **kwargs)

    def deliver_rich(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        self.calls.append("deliver_rich")
        self.deliveries.append((recipient, message))
        if "always" in self._fail_on or "deliver_rich" in self._fail_on:
            return ProviderDeliveryResult(
                success=False,
                channel=self.channel,
                provider=self.name,
                error="fake rich failure",
                retryable=self._fail_retryable,
            )
        return ProviderDeliveryResult(
            success=True,
            channel=self.channel,
            provider=self.name,
            delivery_ref=f"{self.name}-rich-{len(self.deliveries)}",
        )


class AlertFakeProvider(FakeProvider, AlertCapability):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.alert_severities: list[str] = []

    def deliver_alert(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        severity: str,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        self.calls.append("deliver_alert")
        self.alert_severities.append(severity)
        self.deliveries.append((recipient, message))
        return ProviderDeliveryResult(
            success=True,
            channel=self.channel,
            provider=self.name,
            delivery_ref=f"{self.name}-alert-{len(self.deliveries)}",
        )


class MediaFakeProvider(FakeProvider, MediaCapability):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.media_attachments: list[tuple] = []

    def deliver_media(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        self.calls.append("deliver_media")
        self.media_attachments.append((recipient, message.attachments))
        self.deliveries.append((recipient, message))
        return ProviderDeliveryResult(
            success=True,
            channel=self.channel,
            provider=self.name,
            delivery_ref=f"{self.name}-media-{len(self.deliveries)}",
        )


class StatusFakeProvider(FakeProvider, StatusCallbackCapability):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.status_changes: list[tuple[str, str]] = []

    def on_status_change(self, delivery_ref: str, status: str) -> None:
        self.status_changes.append((delivery_ref, status))


class BulkFakeProvider(FakeProvider, BulkCapability):
    def deliver_bulk(
        self,
        recipients: list[Recipient],
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> list[ProviderDeliveryResult]:
        self.calls.append("deliver_bulk")
        return [
            ProviderDeliveryResult(
                success=True,
                channel=self.channel,
                provider=self.name,
                delivery_ref=f"{self.name}-bulk-{idx}",
            )
            for idx in range(len(recipients))
        ]


class FakePlugin(ProviderPlugin):
    """Plugin wrapper around a FakeProvider."""

    def __init__(
        self,
        plugin_id: str,
        provider: FakeProvider,
        fail_activation: bool = False,
    ) -> None:
        self.metadata = PluginMetadata(
            id=plugin_id,
            version="1.0.0",
            description="test plugin",
        )
        self._provider = provider
        self._fail_activation = fail_activation
        self.activation_count = 0
        self.deactivation_count = 0

    def create_provider(self) -> ChannelProvider:
        return self._provider

    def activate(self, context: dict[str, Any] | None = None) -> None:
        if self._fail_activation:
            raise RuntimeError("activation boom")
        self.activation_count += 1

    def deactivate(self) -> None:
        self.deactivation_count += 1


class DictPreferenceStore:
    """Recipient preference store built on a plain dict."""

    def __init__(self, prefs: dict[str, RecipientPreferences] | None = None) -> None:
        self._prefs = prefs or {}

    def preferences_for(self, recipient_address: str) -> RecipientPreferences:
        return self._prefs.get(recipient_address, RecipientPreferences.unrestricted())


class ExplodingProvider(ChannelProvider):
    """Provider whose ``deliver`` raises — the Core must not crash."""

    name = "exploding"
    channel = "email"

    def deliver(
        self,
        recipient: Recipient,
        message: OutboundMessage,
        options: ProviderOptions | None = None,
    ) -> ProviderDeliveryResult:
        raise RuntimeError("provider bug")


__all__ = [
    "AlertFakeProvider",
    "BulkFakeProvider",
    "DictPreferenceStore",
    "ExplodingProvider",
    "FakePlugin",
    "FakeProvider",
    "InMemoryDeliveryQueue",
    "InMemoryStateStore",
    "MediaFakeProvider",
    "RecordingAuditSink",
    "RichFakeProvider",
    "StatusFakeProvider",
]
