from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("gula.events")


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[..., Any]]] = defaultdict(list)

    def on(self, event_name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self._handlers[event_name].append(fn)
            return fn
        return decorator

    def subscribe(self, event_name: str, handler: Callable[..., Any]) -> None:
        self._handlers[event_name].append(handler)

    def emit(self, event_name: str, payload: dict[str, Any] | None = None) -> int:
        payload = payload or {}
        handlers = self._handlers.get(event_name, [])
        ok = 0
        for handler in handlers:
            try:
                handler(payload)
                ok += 1
            except Exception:
                logger.exception(
                    "Event handler %s failed for event '%s'",
                    handler.__qualname__,
                    event_name,
                )
        return ok


events = EventBus()
