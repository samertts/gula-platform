"""Domain model for the GULA Communication Platform Core.

Provider-independent value objects and result types shared by the whole
communication stack. This module imports nothing outside the standard
library — it is the dependency-free heart of the platform.
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from typing import Any


class ContentFormat(enum.StrEnum):
    """Rendered content formats a template or message can carry."""

    PLAIN = "plain"
    HTML = "html"
    MARKDOWN = "markdown"

    @classmethod
    def _missing_(cls, value: object) -> ContentFormat:
        return cls.PLAIN


class Priority(enum.StrEnum):
    """Delivery priorities, lowest to highest."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    MANDATORY = "mandatory"


@dataclass(frozen=True)
class Recipient:
    """A delivery target.

    ``address`` is provider-chosen (email address, chat id, phone number,
    device token, webhook URL). The Core never interprets it.
    """

    address: str
    display_name: str = ""

    def __str__(self) -> str:
        return self.display_name or self.address


@dataclass(frozen=True)
class OutboundMessage:
    """The message payload handed to a provider.

    ``content`` is always plain text unless ``format`` says otherwise.
    ``metadata`` carries app-owned context (patient id, order id, tenant) —
    the Core forwards it verbatim to audit and telemetry.
    """

    content: str
    format: ContentFormat = ContentFormat.PLAIN
    subject: str = ""
    locale: str = ""
    template_id: str = ""
    template_version: str = ""
    attachments: tuple[Attachment, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Attachment:
    """Attachments are references (path / URL / file id) — never inline data."""

    reference: str
    name: str = ""
    mime_type: str = ""
    kind: str = "document"


@dataclass(frozen=True)
class ProviderDeliveryResult:
    """Result of one provider delivery attempt."""

    success: bool
    channel: str
    provider: str
    delivery_ref: str = ""
    error: str | None = None
    retryable: bool = False
    latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "channel": self.channel,
            "provider": self.provider,
            "delivery_ref": self.delivery_ref,
            "error": self.error,
            "retryable": self.retryable,
            "latency_ms": round(self.latency_ms, 3),
        }


@dataclass(frozen=True)
class ChannelAttempt:
    """One planned channel attempt inside a delivery plan."""

    channel: str
    priority: Priority = Priority.NORMAL
    is_required: bool = False
    is_fallback: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "channel": self.channel,
            "priority": self.priority.value,
            "is_required": self.is_required,
            "is_fallback": self.is_fallback,
        }


@dataclass(frozen=True)
class DeliveryReceipt:
    """End-to-end outcome of a dispatch for one recipient."""

    delivery_id: str
    recipient: str
    state: str
    attempts: tuple[ProviderDeliveryResult, ...] = ()
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "delivery_id": self.delivery_id,
            "recipient": self.recipient,
            "state": self.state,
            "attempts": [a.to_dict() for a in self.attempts],
            "error": self.error,
        }


def new_delivery_id() -> str:
    """Short unique delivery identifier (UUID hex)."""
    return uuid.uuid4().hex


__all__ = [
    "Attachment",
    "ChannelAttempt",
    "ContentFormat",
    "DeliveryReceipt",
    "OutboundMessage",
    "Priority",
    "ProviderDeliveryResult",
    "Recipient",
    "new_delivery_id",
]
