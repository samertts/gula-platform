from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("gula.kernel.background.task_queue")


@dataclass
class Task:
    id: str
    name: str
    handler: Callable
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    priority: int = 0
    created_at: float = 0.0
    status: str = "pending"

    def __post_init__(self):
        if not self.id:
            import uuid
            self.id = str(uuid.uuid4())
        if not self.created_at:
            import time
            self.created_at = time.time()


class TaskQueue:
    def __init__(self):
        self._tasks: list[Task] = []

    def enqueue(self, task: Task) -> None:
        self._tasks.append(task)

    def dequeue(self) -> Task | None:
        if not self._tasks:
            return None
        self._tasks.sort(key=lambda t: t.priority, reverse=True)
        return self._tasks.pop(0)

    def list_pending(self) -> list[Task]:
        return [t for t in self._tasks if t.status == "pending"]

    def size(self) -> int:
        return len(self._tasks)
