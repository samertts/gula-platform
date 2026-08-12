from __future__ import annotations

import time
import uuid
from dataclasses import dataclass


@dataclass
class Event:
    name: str
    data: dict
    version: int = 1
    id: str = ""
    timestamp: float = 0.0
    source: str = ""
    correlation_id: str = ""
    tenant_id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = time.time()
