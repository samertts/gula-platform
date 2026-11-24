"""Delivery state model for the GULA Communication Platform Core.

Created → Queued → Sending → Delivered | Failed
Delivered → Read → Archived
Failed → Queued (retry) | Archived

The state machine is pure; persistence is delegated to a ``StateStore``
interface implemented outside the Core (PostgreSQL, Redis, in-memory …).
"""

from __future__ import annotations

import enum
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.communication.state")


class DeliveryState(enum.StrEnum):
    CREATED = "created"
    QUEUED = "queued"
    SENDING = "sending"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"
    ARCHIVED = "archived"

    @classmethod
    def _missing_(cls, value: object) -> DeliveryState:
        return cls.CREATED


_ALLOWED_TRANSITIONS: dict[DeliveryState, frozenset[DeliveryState]] = {
    DeliveryState.CREATED: frozenset({DeliveryState.QUEUED, DeliveryState.SENDING, DeliveryState.FAILED}),
    DeliveryState.QUEUED: frozenset({DeliveryState.SENDING, DeliveryState.FAILED, DeliveryState.ARCHIVED}),
    DeliveryState.SENDING: frozenset({DeliveryState.DELIVERED, DeliveryState.FAILED}),
    DeliveryState.DELIVERED: frozenset({DeliveryState.READ, DeliveryState.ARCHIVED}),
    DeliveryState.FAILED: frozenset({DeliveryState.QUEUED, DeliveryState.ARCHIVED}),
    DeliveryState.READ: frozenset({DeliveryState.ARCHIVED}),
    DeliveryState.ARCHIVED: frozenset(),
}


class DeliveryStateMachine:
    """Validates and applies delivery state transitions."""

    @staticmethod
    def can_transition(current: DeliveryState, target: DeliveryState) -> bool:
        return target in _ALLOWED_TRANSITIONS[current]

    @staticmethod
    def transitions_from(current: DeliveryState) -> list[str]:
        return sorted(s.value for s in _ALLOWED_TRANSITIONS[current])

    @staticmethod
    def transition(
        current: DeliveryState,
        target: DeliveryState,
    ) -> DeliveryState:
        if not DeliveryStateMachine.can_transition(current, target):
            raise ValueError(
                f"invalid delivery state transition: {current.value} → {target.value}",
            )
        return target


@dataclass
class DeliveryRecord:
    """A persisted delivery entry the StateStore operates on."""

    delivery_id: str
    recipient: str
    state: DeliveryState = DeliveryState.CREATED
    channel_results: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    updated_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "delivery_id": self.delivery_id,
            "recipient": self.recipient,
            "state": self.state.value,
            "channel_results": list(self.channel_results),
            "error": self.error,
        }


class StateStore(ABC):
    """Persistence boundary for delivery records (interface only)."""

    @abstractmethod
    def save(self, record: DeliveryRecord) -> None: ...

    @abstractmethod
    def get(self, delivery_id: str) -> DeliveryRecord | None: ...

    @abstractmethod
    def update_state(
        self,
        delivery_id: str,
        state: DeliveryState,
        error: str | None = None,
    ) -> bool: ...


__all__ = [
    "DeliveryRecord",
    "DeliveryState",
    "DeliveryStateMachine",
    "StateStore",
]
