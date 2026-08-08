import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class Query:
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


QueryHandler = Callable[[Query], Any]


class QueryBus:
    def __init__(self):
        self._logger = logging.getLogger("gula.cqrs.query")
        self._handlers: dict[str, QueryHandler] = {}
        self._cache: dict[str, tuple[Any, float]] = {}

    def register(self, query_type: str, handler: QueryHandler) -> None:
        self._handlers[query_type] = handler
        self._logger.debug("Handler registered for query: %s", query_type)

    def unregister(self, query_type: str) -> None:
        self._handlers.pop(query_type, None)

    async def ask(self, query_type: str, query: Query | None = None) -> Any:
        handler = self._handlers.get(query_type)
        if handler is None:
            raise KeyError(f"No handler registered for query: {query_type}")
        result = handler(query or Query())
        if hasattr(result, "__await__"):
            result = await result
        return result

    def register_cache(self, query_type: str, ttl_seconds: float = 60.0) -> None:
        pass

    def invalidate_cache(self, query_type: str) -> None:
        self._cache.pop(query_type, None)

    def clear_cache(self) -> None:
        self._cache.clear()

    def handler_count(self) -> int:
        return len(self._handlers)

    def registered_queries(self) -> list[str]:
        return list(self._handlers.keys())
