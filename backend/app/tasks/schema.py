"""Task queue schema — shared data contracts.

All producers (API routes, edge scheduler) and consumers (TaskWorker) use
these models so the wire format is never ambiguous.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    DONE      = "done"
    FAILED    = "failed"   # retryable failure, still in flight
    DEAD      = "dead"     # exceeded max_retries → moved to DLQ


class TaskPayload(BaseModel):
    task_id:     str       = Field(default_factory=lambda: str(uuid.uuid4()))
    type:        str
    payload:     dict[str, Any] = Field(default_factory=dict)
    retry_count: int       = 0
    max_retries: int       = 3
    timeout_s:   int       = 60
    enqueued_at: datetime  = Field(default_factory=lambda: datetime.now(timezone.utc))

    def next_attempt(self) -> "TaskPayload":
        """Return a copy with retry_count incremented."""
        return self.model_copy(update={"retry_count": self.retry_count + 1})

    @property
    def exhausted(self) -> bool:
        return self.retry_count >= self.max_retries


class TaskResult(BaseModel):
    task_id:      str
    status:       TaskStatus
    result:       Optional[Any]  = None
    error:        Optional[str]  = None
    attempt:      int            = 0
    completed_at: datetime       = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms:  float          = 0.0
