from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WorkflowCompletedEvent:
    """WorkflowCompleted event for workflow_engine capability."""

    event_id: str = ""
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    data: dict = field(default_factory=dict)
    version: int = 1
