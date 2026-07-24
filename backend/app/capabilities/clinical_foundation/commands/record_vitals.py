from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Record_vitalsCommand:
    """record_vitals command for clinical_foundation capability."""

    command_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: dict = field(default_factory=dict)
