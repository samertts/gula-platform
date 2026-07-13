from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("gula.kernel.background.job_retry")


@dataclass
class RetryPolicy:
    max_retries: int = 3
    backoff_base: float = 1.0
    backoff_multiplier: float = 2.0


class JobRetry:
    def __init__(self):
        self._retry_counts: dict[str, int] = {}
        self._policy = RetryPolicy()

    def should_retry(self, task_id: str) -> bool:
        count = self._retry_counts.get(task_id, 0)
        return count < self._policy.max_retries

    def increment(self, task_id: str) -> int:
        count = self._retry_counts.get(task_id, 0) + 1
        self._retry_counts[task_id] = count
        return count

    def get_backoff(self, task_id: str) -> float:
        count = self._retry_counts.get(task_id, 0)
        return self._policy.backoff_base * (self._policy.backoff_multiplier**count)
