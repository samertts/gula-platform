from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Export_reportCommand:
    """export_report command for reporting_service capability."""

    command_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    data: dict = field(default_factory=dict)
