from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Retrieve_fileCommand:
    """retrieve_file command for storage_service capability."""

    command_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: dict = field(default_factory=dict)
