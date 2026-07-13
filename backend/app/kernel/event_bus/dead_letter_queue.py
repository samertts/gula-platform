from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.app.kernel.event_bus.events import Event

logger = logging.getLogger("gula.kernel.event_bus.dlq")


@dataclass
class DeadLetterEntry:
    event: Event
    reason: str
    failed_at: float = 0.0
    retry_count: int = 0

    def __post_init__(self):
        if not self.failed_at:
            import time
            self.failed_at = time.time()


class DeadLetterQueue:
    def __init__(self):
        self._entries: list[DeadLetterEntry] = []

    def send(self, entry: DeadLetterEntry) -> None:
        self._entries.append(entry)

    def list_all(self) -> list[DeadLetterEntry]:
        return list(self._entries)

    def replay(self, event_id: str) -> DeadLetterEntry | None:
        for entry in self._entries:
            if entry.event.id == event_id:
                self._entries.remove(entry)
                return entry
        return None
