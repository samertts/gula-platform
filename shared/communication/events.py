"""Event integration for the GULA Communication Platform Core.

The Communication Platform consumes platform events (UserRegistered,
PasswordResetRequested, ResultReleased, BackupFailed, CriticalAlert, …)
through declarative ``event → policy`` bindings. The Core never calls a
provider directly from an event — it resolves the bound policy and dispatches
through the Communication Center.

Binding to a concrete event bus is done at the composition root with
:meth:`EventBridge.bind`.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

logger = logging.getLogger("gula.communication.events")


class CommunicationEventHandler(Protocol):
    """Handler signature the Center exposes to the event bridge."""

    def handle_communication_event(self, event_name: str, payload: dict[str, Any]) -> Any: ...


class EventPolicyRegistry:
    """Maps event names to policy ids and resolves recipient + payload keys.

    ``recipient_key`` selects which payload field holds the destination
    address; ``metadata_keys`` are forwarded to audit/telemetry context.
    """

    def __init__(self) -> None:
        self._bindings: dict[str, tuple[str, str, tuple[str, ...]]] = {}

    def bind(
        self,
        event_name: str,
        policy_id: str,
        recipient_key: str = "recipient",
        metadata_keys: tuple[str, ...] = (),
    ) -> None:
        if not event_name or not policy_id or not recipient_key:
            raise ValueError("event, policy and recipient_key are required")
        self._bindings[event_name] = (policy_id, recipient_key, metadata_keys)

    def unbind(self, event_name: str) -> bool:
        return self._bindings.pop(event_name, None) is not None

    def resolve(self, event_name: str) -> tuple[str, str, tuple[str, ...]] | None:
        return self._bindings.get(event_name)

    def binding(self, event_name: str) -> dict[str, Any] | None:
        resolved = self._bindings.get(event_name)
        if resolved is None:
            return None
        policy_id, recipient_key, metadata_keys = resolved
        return {
            "event_name": event_name,
            "policy_id": policy_id,
            "recipient_key": recipient_key,
            "metadata_keys": list(metadata_keys),
        }

    def bindings(self) -> list[dict[str, Any]]:
        return [self.binding(name) for name in sorted(self._bindings)]


class EventBridge:
    """Binds the Center to a platform event bus.

    This module depends only on a minimal ``subscribe`` protocol; the real
    bus (``shared.events``) is injected by the composition root, keeping the
    Core independent of any event infrastructure.
    """

    def __init__(
        self,
        center: CommunicationEventHandler,
        registry: EventPolicyRegistry,
    ) -> None:
        self._center = center
        self._registry = registry
        self._bound_event_names: set[str] = set()

    def bind(self, bus: Any) -> None:
        """Subscribe centre handler for every registered event binding.

        ``bus`` must expose ``subscribe(event_name, handler)``. Idempotent.
        """
        for event_name in self._registry.bindings():
            name = event_name["event_name"]
            if name in self._bound_event_names:
                continue
            try:
                bus.subscribe(name, _partial_handler(self._center, name))
                self._bound_event_names.add(name)
            except Exception:
                logger.exception("communication_event_bind_failed event=%s", name)

    def bound_event_names(self) -> list[str]:
        return sorted(self._bound_event_names)

    def handle(self, event_name: str, payload: dict[str, Any]) -> None:
        """Synchronous handle used by tests and non-bus callers."""
        self._center.handle_communication_event(event_name, payload)


def _partial_handler(center: CommunicationEventHandler, event_name: str):
    """A handler closure since the platform bus only passes ``payload``."""

    def handler(payload: dict[str, Any]) -> None:
        center.handle_communication_event(event_name, payload or {})

    return handler


__all__ = [
    "CommunicationEventHandler",
    "EventBridge",
    "EventPolicyRegistry",
]