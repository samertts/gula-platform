"""Task handler registry.

Producers enqueue a TaskPayload with a ``type`` string; the TaskWorker looks
up the matching async handler here and calls it.

Usage:

    # Define a handler (anywhere in the app, imported at worker startup):
    from app.tasks.registry import task_handler

    @task_handler("send_notification")
    async def handle_send_notification(payload: dict) -> dict:
        ...
        return {"sent": True}

    # Enqueue from an API route:
    from app.tasks.queue import task_queue
    from app.tasks.schema import TaskPayload

    await task_queue.enqueue(TaskPayload(type="send_notification",
                                         payload={"user_id": 42}))
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Coroutine

logger = logging.getLogger("gula.task_registry")

# type: task_type → async callable(payload: dict) → Any
_REGISTRY: dict[str, Callable[..., Coroutine[Any, Any, Any]]] = {}


def task_handler(task_type: str):
    """Register an async function as the handler for ``task_type``."""
    def decorator(fn: Callable) -> Callable:
        if task_type in _REGISTRY:
            logger.warning("task_handler: overwriting existing handler for %r", task_type)
        _REGISTRY[task_type] = fn
        logger.debug("Registered task handler: %r → %s", task_type, fn.__qualname__)
        return fn
    return decorator


def get_handler(task_type: str) -> Callable | None:
    """Return the registered handler or None if unknown."""
    return _REGISTRY.get(task_type)


def registered_types() -> list[str]:
    """Return all registered task type names (for diagnostics)."""
    return sorted(_REGISTRY)
