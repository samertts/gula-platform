from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from app.integration.esb.types import ESBMessage

logger = logging.getLogger("gula.integration.esb.dead_letter")


@dataclass
class DeadLetterRecord:
    message: ESBMessage = field(default_factory=ESBMessage)
    error: str = ""
    failed_at: float = 0.0
    retry_count: int = 0

    def __post_init__(self):
        if not self.failed_at:
            self.failed_at = time.time()


class DeadLetterService:
    def __init__(self, max_retries: int = 3):
        self._records: list[DeadLetterRecord] = []
        self._max_retries = max_retries

    def send(self, message: ESBMessage, error: str) -> DeadLetterRecord:
        record = DeadLetterRecord(message=message, error=error)
        self._records.append(record)
        logger.warning("Message sent to dead letter queue: %s - %s", message.id, error)
        return record

    def replay(self, message_id: str) -> ESBMessage | None:
        for record in self._records:
            if record.message.id == message_id and record.retry_count < self._max_retries:
                record.retry_count += 1
                self._records.remove(record)
                logger.info("Message replayed from dead letter queue: %s", message_id)
                return record.message
        return None

    def replay_all(self) -> list[ESBMessage]:
        replayable = [r for r in self._records if r.retry_count < self._max_retries]
        self._records = [r for r in self._records if r.retry_count >= self._max_retries]
        for r in replayable:
            r.retry_count += 1
        logger.info("Replayed %d messages from dead letter queue", len(replayable))
        return [r.message for r in replayable]

    def list_all(self) -> list[DeadLetterRecord]:
        return list(self._records)

    def count(self) -> int:
        return len(self._records)

    def purge(self) -> int:
        count = len(self._records)
        self._records.clear()
        logger.info("Dead letter queue purged: %d messages", count)
        return count

    def get_max_retries(self) -> int:
        return self._max_retries

    def set_max_retries(self, max_retries: int) -> None:
        self._max_retries = max_retries
