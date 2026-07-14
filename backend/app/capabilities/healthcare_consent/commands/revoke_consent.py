from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Revoke_consentCommand:
    """revoke_consent command for healthcare_consent capability."""
    command_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: dict = field(default_factory=dict)
