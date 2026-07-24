from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Break_glassCommand:
    """break_glass command for healthcare_consent capability."""

    command_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: dict = field(default_factory=dict)
