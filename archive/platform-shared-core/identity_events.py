from typing import Any


class IdentityEventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[callable]] = {}

    def subscribe(self, event_type: str, handler: callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            handler(payload or {})


event_bus = IdentityEventBus()


def on_person_created(handler: callable) -> callable:
    event_bus.subscribe("person.created", handler)
    return handler


def on_account_created(handler: callable) -> callable:
    event_bus.subscribe("account.created", handler)
    return handler


def on_identity_verified(handler: callable) -> callable:
    event_bus.subscribe("identity.verified", handler)
    return handler
