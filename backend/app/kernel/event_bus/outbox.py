from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("gula.kernel.event_bus.outbox")


@dataclass
class OutboxMessage:
    id: str
    event_name: str
    payload: dict
    status: str = "pending"
    created_at: float = 0.0
    processed_at: float | None = None
    retry_count: int = 0

    def __post_init__(self):
        if not self.id:
            import uuid

            self.id = str(uuid.uuid4())
        if not self.created_at:
            import time

            self.created_at = time.time()


class OutboxPattern:
    def __init__(self):
        self._messages: list[OutboxMessage] = []

    def enqueue(self, message: OutboxMessage) -> None:
        self._messages.append(message)

    def dequeue(self) -> OutboxMessage | None:
        for msg in self._messages:
            if msg.status == "pending":
                msg.status = "processing"
                return msg
        return None

    def mark_completed(self, message_id: str) -> None:
        for msg in self._messages:
            if msg.id == message_id:
                msg.status = "completed"
                break

    def mark_failed(self, message_id: str) -> None:
        for msg in self._messages:
            if msg.id == message_id:
                msg.status = "failed"
                break

    def list_pending(self) -> list[OutboxMessage]:
        return [m for m in self._messages if m.status == "pending"]
