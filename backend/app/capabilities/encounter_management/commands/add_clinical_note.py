from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Add_clinical_noteCommand:
    """add_clinical_note command for encounter_management capability."""

    command_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    data: dict = field(default_factory=dict)
