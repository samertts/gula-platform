from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Add_clinical_noteCommand:
    """add_clinical_note command for encounter_management capability."""
    command_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: dict = field(default_factory=dict)
