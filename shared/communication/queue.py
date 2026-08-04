"""Queue integration interfaces for the GULA Communication Platform Core.

Interfaces only — no queue provider implementation ships with the Core.
A queue provider (Redis, PostgreSQL, outbox, …) is plugged by the platform
composition root. The Core serialises a ``DeliveryJob`` and delegates.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Protocol

from .model import OutboundMessage, Priority


@dataclass(frozen=True)
class DeliveryJob:
    """One unit of queued work: deliver a message to a recipient."""

    job_id: str
    delivery_id: str
    recipient: str
    channel: str
    message: OutboundMessage
    priority: Priority = Priority.NORMAL
    max_retries: int = 2
    attempts: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "delivery_id": self.delivery_id,
            "recipient": self.recipient,
            "channel": self.channel,
            "message": {
                "content": self.message.content,
                "format": self.message.format.value,
                "subject": self.message.subject,
                "locale": self.message.locale,
                "template_id": self.message.template_id,
                "template_version": self.message.template_version,
            },
            "priority": self.priority.value,
            "max_retries": self.max_retries,
            "attempts": self.attempts,
        }


class DeliveryQueue(Protocol):
    """Queue provider contract (enqueue → dequeue → ack/requeue/dead-letter).

    Implementations are queue providers (Redis, PostgreSQL outbox, …) and
    are plugged outside the Core.
    """

    async def enqueue(self, job: DeliveryJob) -> None: ...

    async def dequeue(self, timeout: int = 5) -> DeliveryJob | None: ...

    async def ack(self, job_id: str) -> None: ...

    async def requeue(self, job_id: str, error: str) -> None: ...

    async def dead_letter(self, job_id: str, error: str) -> None: ...

    async def depth(self) -> int: ...


class QueueRegistry:
    """Named queue bindings: ``queue_name → DeliveryQueue``."""

    def __init__(self) -> None:
        self._queues: dict[str, DeliveryQueue] = {}
        self._lock = threading.Lock()

    def bind(self, name: str, queue: DeliveryQueue) -> None:
        if not name:
            raise ValueError("queue name is required")
        with self._lock:
            self._queues[name] = queue

    def unbind(self, name: str) -> bool:
        with self._lock:
            return self._queues.pop(name, None) is not None

    def get(self, name: str) -> DeliveryQueue | None:
        with self._lock:
            return self._queues.get(name)

    def names(self) -> list[str]:
        with self._lock:
            return sorted(self._queues)


__all__ = [
    "DeliveryJob",
    "DeliveryQueue",
    "QueueRegistry",
]
