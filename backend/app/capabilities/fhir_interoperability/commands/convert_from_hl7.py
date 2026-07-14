from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Convert_from_hl7Command:
    """convert_from_hl7 command for fhir_interoperability capability."""
    command_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: dict = field(default_factory=dict)
