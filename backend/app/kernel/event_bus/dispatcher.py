from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, List

from backend.app.kernel.event_bus.events import Event

logger = logging.getLogger("gula.kernel.event_bus.dispatcher")


class EventDispatcher:
    def dispatch(self, event: Event, handlers: list[Callable]) -> None:
        for handler in handlers:
            try:
                result = handler(event)
                if hasattr(result, "__await__"):
                    import asyncio
                    asyncio.ensure_future(result)
            except Exception as e:
                logger.error(
                    "Event handler failed",
                    extra={"event": event.name, "handler": handler.__name__, "error": str(e)},
                )
