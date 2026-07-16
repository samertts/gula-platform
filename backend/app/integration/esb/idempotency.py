from __future__ import annotations

import logging
import time

logger = logging.getLogger("gula.integration.esb.idempotency")


class IdempotencyService:
    def __init__(self, ttl_seconds: int = 3600):
        self._processed: dict[str, float] = {}
        self._ttl = ttl_seconds

    def is_duplicate(self, message_id: str) -> bool:
        if message_id in self._processed:
            age = time.time() - self._processed[message_id]
            if age < self._ttl:
                return True
            del self._processed[message_id]
        return False

    def mark_processed(self, message_id: str) -> None:
        self._processed[message_id] = time.time()

    def clear_expired(self) -> int:
        now = time.time()
        expired = [mid for mid, ts in self._processed.items() if now - ts >= self._ttl]
        for mid in expired:
            del self._processed[mid]
        if expired:
            logger.info("Cleared %d expired idempotency keys", len(expired))
        return len(expired)

    def clear_all(self) -> int:
        count = len(self._processed)
        self._processed.clear()
        logger.info("Cleared all idempotency keys: %d", count)
        return count

    def count(self) -> int:
        return len(self._processed)

    def set_ttl(self, ttl_seconds: int) -> None:
        self._ttl = ttl_seconds

    def get_ttl(self) -> int:
        return self._ttl
