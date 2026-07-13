from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from backend.app.kernel.event_bus.events import Event

logger = logging.getLogger("gula.kernel.event_bus.dispatcher")


class EventDispatcher:
    def dispatch(self, event: Event, handlers: list[Callable]) -> None:
        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    task = asyncio.create_task(result)
                    task.add_done_callback(self._on_handler_complete)
            except Exception as e:
                logger.error(
                    "Event handler failed",
                    extra={"event": event.name, "handler": handler.__name__, "error": str(e)},
                )

    @staticmethod
    def _on_handler_complete(task: asyncio.Task) -> None:
        exc = task.exception()
        if exc:
            logger.error(
                "Async event handler raised an exception",
                extra={"error": str(exc)},
            )
