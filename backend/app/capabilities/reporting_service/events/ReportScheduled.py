from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ReportScheduledEvent:
    """ReportScheduled event for reporting_service capability."""

    event_id: str = ""
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    data: dict = field(default_factory=dict)
    version: int = 1
