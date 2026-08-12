from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable

logger = logging.getLogger("gula.kernel.shutdown")


class ShutdownHandler:
    def __init__(self, name: str, handler: Callable, priority: int = 100, timeout: float = 30.0):
        self.name = name
        self.handler = handler
        self.priority = priority
        self.timeout = timeout


class ShutdownManager:
    def __init__(self):
        self._handlers: list[ShutdownHandler] = []
        self._shutdown_in_progress = False

    def register(self, handler: ShutdownHandler) -> None:
        self._handlers.append(handler)
        self._handlers.sort(key=lambda h: h.priority)

    async def shutdown_all(self) -> list[dict]:
        self._shutdown_in_progress = True
        results = []
        for handler in self._handlers:
            start = time.monotonic()
            try:
                result = handler.handler()
                if hasattr(result, "__await__"):
                    await asyncio.wait_for(result, timeout=handler.timeout)
                results.append(
                    {
                        "name": handler.name,
                        "success": True,
                        "duration_ms": round((time.monotonic() - start) * 1000),
                    },
                )
            except Exception as e:
                results.append(
                    {
                        "name": handler.name,
                        "success": False,
                        "error": str(e),
                        "duration_ms": round((time.monotonic() - start) * 1000),
                    },
                )
                logger.error(
                    "Shutdown handler failed",
                    extra={"handler": handler.name, "error": str(e)},
                )
        return results
