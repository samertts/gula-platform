"""In-process event bus — canonical shared.events.

Re-exports the singleton EventBus from the shared library so all backend
code uses the same canonical implementation.

Usage:
    from ..core.events import events, ORDER_CREATED

    @events.on("order.validated")
    def my_handler(payload: dict) -> None:
        ...

    events.emit("order.validated", {"order_id": 42})
"""

from shared.events import EventBus, events
from shared.events.constants import (
    ORDER_CREATED,
    ORDER_VALIDATED,
    ORDER_CANCELLED,
    RESULT_CRITICAL,
    SAMPLE_REJECTED,
)

__all__ = [
    "EventBus",
    "events",
    "ORDER_CREATED",
    "ORDER_VALIDATED",
    "ORDER_CANCELLED",
    "RESULT_CRITICAL",
    "SAMPLE_REJECTED",
]
