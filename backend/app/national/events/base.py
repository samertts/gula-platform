from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC


@dataclass
class NationalDomainEvent:
    event_type: str = ""
    aggregate_id: str = ""
    aggregate_type: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    request_id: str = ""
    user_id: str | None = None
    lab_id: int | None = None
    org_id: str | None = None
    correlation_id: str = ""
    causation_id: str = ""
    version: int = 1

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()
        if not self.correlation_id and self.aggregate_id:
            self.correlation_id = self.aggregate_id
