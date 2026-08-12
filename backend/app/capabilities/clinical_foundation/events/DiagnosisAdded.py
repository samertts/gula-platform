from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DiagnosisAddedEvent:
    """DiagnosisAdded event for clinical_foundation capability."""

    event_id: str = ""
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    data: dict = field(default_factory=dict)
    version: int = 1
