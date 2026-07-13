from __future__ import annotations

import heapq
import logging
from collections.abc import Callable
from dataclasses import dataclass

logger = logging.getLogger("gula.kernel.background.priority_queue")


@dataclass
class PriorityTask:
    priority: int
    created_at: float = 0.0
    id: str = ""
    name: str = ""
    handler: Callable | None = None

    def __post_init__(self):
        if not self.id:
            import uuid

            self.id = str(uuid.uuid4())
        if not self.created_at:
            import time

            self.created_at = time.time()

    def __lt__(self, other: PriorityTask) -> bool:
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.created_at < other.created_at


class PriorityQueue:
    def __init__(self):
        self._heap: list[PriorityTask] = []

    def push(self, task: PriorityTask) -> None:
        heapq.heappush(self._heap, task)

    def pop(self) -> PriorityTask | None:
        if not self._heap:
            return None
        return heapq.heappop(self._heap)

    def size(self) -> int:
        return len(self._heap)

    def peek(self) -> PriorityTask | None:
        if not self._heap:
            return None
        return self._heap[0]
