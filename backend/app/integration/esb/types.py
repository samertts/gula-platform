from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ESBMessage:
    id: str = ""
    event_name: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    destination: str = ""
    priority: int = 5
    correlation_id: str = ""
    tenant_id: str = ""
    timestamp: float = 0.0
    ttl_seconds: int = 3600

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = time.time()
