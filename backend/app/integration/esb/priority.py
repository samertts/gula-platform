from __future__ import annotations

import heapq
import logging
from dataclasses import dataclass, field

from backend.app.integration.esb.types import ESBMessage

logger = logging.getLogger("gula.integration.esb.priority")


@dataclass(order=True)
class PriorityEntry:
    priority: int
    timestamp: float
    message: ESBMessage = field(compare=False)


class PriorityService:
    def __init__(self):
        self._queue: list[PriorityEntry] = []
        self._priority_levels = {"critical": 1, "high": 2, "medium": 5, "low": 8, "background": 10}

    def enqueue(self, message: ESBMessage) -> None:
        entry = PriorityEntry(
            priority=message.priority, timestamp=message.timestamp, message=message
        )
        heapq.heappush(self._queue, entry)
        logger.debug("Message queued with priority %d: %s", message.priority, message.id)

    def dequeue(self) -> ESBMessage | None:
        if not self._queue:
            return None
        entry = heapq.heappop(self._queue)
        return entry.message

    def peek(self) -> ESBMessage | None:
        if not self._queue:
            return None
        return self._queue[0].message

    def size(self) -> int:
        return len(self._queue)

    def clear(self) -> None:
        self._queue.clear()
        logger.info("Priority queue cleared")

    def resolve_priority(self, level: str) -> int:
        return self._priority_levels.get(level.lower(), 5)

    def list_priority_levels(self) -> dict[str, int]:
        return dict(self._priority_levels)

    def messages_by_priority(self) -> dict[int, int]:
        counts: dict[int, int] = {}
        for entry in self._queue:
            counts[entry.priority] = counts.get(entry.priority, 0) + 1
        return counts
