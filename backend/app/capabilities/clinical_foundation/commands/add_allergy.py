from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Add_allergyCommand:
    """add_allergy command for clinical_foundation capability."""

    command_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    data: dict = field(default_factory=dict)
