"""Lightweight in-process event bus.

Usage:
    # Subscribe a handler
    @events.on("order.validated")
    def my_handler(payload: dict) -> None:
        ...

    # Emit an event (fire-and-forget; errors are caught and logged)
    events.emit("order.validated", {"order_id": 42, "patient_id": 7})

Design decisions:
- Synchronous / in-process:  avoids a hard dependency on Redis/RQ for
  features that don't strictly need async (audit, in-app alerts).
  Heavy I/O (PDF generation, SMS) should be enqueued to Redis via
  a separate background worker — not done inside an event handler.
- Error isolation:  a failing handler never aborts the caller.
- No wildcard subscriptions to keep the mental model simple.
"""
import logging
from collections import defaultdict
from typing import Callable

logger = logging.getLogger("gula.events")

# ── Event name constants ──────────────────────────────────────────────────────
ORDER_CREATED   = "order.created"
ORDER_VALIDATED = "order.validated"
ORDER_CANCELLED = "order.cancelled"
RESULT_CRITICAL = "result.critical"   # emitted for each critical result value
SAMPLE_REJECTED = "sample.rejected"


class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    # ── Registration ──────────────────────────────────────────────────────────

    def on(self, event_name: str):
        """Decorator: @events.on("order.validated")"""
        def decorator(fn: Callable) -> Callable:
            self._handlers[event_name].append(fn)
            return fn
        return decorator

    def subscribe(self, event_name: str, handler: Callable) -> None:
        """Imperative registration: events.subscribe("order.validated", fn)"""
        self._handlers[event_name].append(handler)

    # ── Dispatch ──────────────────────────────────────────────────────────────

    def emit(self, event_name: str, payload: dict | None = None) -> int:
        """Fire all handlers for *event_name*.

        Returns the number of handlers that ran successfully.
        """
        payload = payload or {}
        handlers = self._handlers.get(event_name, [])
        ok = 0
        for handler in handlers:
            try:
                handler(payload)
                ok += 1
            except Exception:
                logger.exception(
                    "Event handler %s failed for event '%s' with payload %s",
                    handler.__qualname__,
                    event_name,
                    payload,
                )
        return ok


# Singleton — import this everywhere
events = EventBus()
