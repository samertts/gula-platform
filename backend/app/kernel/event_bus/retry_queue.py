from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from app.kernel.event_bus.events import Event

logger = logging.getLogger("gula.kernel.event_bus.retry")


@dataclass
class RetryEntry:
    event: Event
    retry_count: int = 0
    max_retries: int = 3
    last_error: str = ""
    next_retry_at: float = 0.0


class RetryQueue:
    def __init__(self):
        self._entries: list[RetryEntry] = []
        self._max_retries = 3
        self._backoff_base = 1.0

    def enqueue(self, entry: RetryEntry) -> None:
        entry.next_retry_at = time.time() + (self._backoff_base * (2**entry.retry_count))
        self._entries.append(entry)

    def dequeue_ready(self) -> list[RetryEntry]:
        now = time.time()
        ready = [e for e in self._entries if e.next_retry_at <= now]
        self._entries = [e for e in self._entries if e.next_retry_at > now]
        return ready

    def retry_count(self, event_id: str) -> int:
        for e in self._entries:
            if e.event.id == event_id:
                return e.retry_count
        return 0
