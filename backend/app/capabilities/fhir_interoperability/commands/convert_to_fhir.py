from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Convert_to_fhirCommand:
    """convert_to_fhir command for fhir_interoperability capability."""
    command_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: dict = field(default_factory=dict)
