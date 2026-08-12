from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("gula.kernel.event_bus.inbox")


@dataclass
class InboxMessage:
    id: str
    event_name: str
    payload: dict
    source: str
    status: str = "received"
    created_at: float = 0.0
    processed_at: float | None = None

    def __post_init__(self):
        if not self.id:
            import uuid

            self.id = str(uuid.uuid4())
        if not self.created_at:
            import time

            self.created_at = time.time()


class InboxPattern:
    def __init__(self):
        self._messages: dict[str, InboxMessage] = {}

    def receive(self, message: InboxMessage) -> None:
        self._messages[message.id] = message

    def mark_processed(self, message_id: str) -> None:
        msg = self._messages.get(message_id)
        if msg:
            msg.status = "processed"

    def has_been_processed(self, message_id: str) -> bool:
        msg = self._messages.get(message_id)
        return msg is not None and msg.status == "processed"
