from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


@dataclass
class Provider_management:
    id: str = field(default_factory=lambda: str(uuid4()))
    provider_id: str
    provider_type: str
    license: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
