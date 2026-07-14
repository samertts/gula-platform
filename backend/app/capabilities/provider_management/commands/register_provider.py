from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Register_providerCommand:
    """register_provider command for provider_management capability."""
    command_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: dict = field(default_factory=dict)
