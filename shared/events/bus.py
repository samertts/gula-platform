from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("gula.events")


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[..., Any]]] = defaultdict(list)
        self._warned_unsubscribed: set[str] = set()

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
        if not handlers and event_name not in self._warned_unsubscribed:
            # Measured after importing every route module: this bus has zero
            # handlers, and `@events.on` appears nowhere in the repository
            # outside a docstring. Six production modules emit onto it. An
            # emission that reaches nobody used to be indistinguishable from one
            # that was acted upon, including `result.critical`. Warned once per
            # event name per process, so the gap is visible without flooding.
            # See IA-043.
            self._warned_unsubscribed.add(event_name)
            logger.warning(
                "Event '%s' was emitted with no subscriber: nothing downstream "
                "will act on it. This is the first such emission for this event "
                "name in this process.",
                event_name,
            )
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
