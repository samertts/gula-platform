from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from datetime import UTC


@dataclass
class DomainEvent:
    event_type: str = ""
    aggregate_id: str = ""
    aggregate_type: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    request_id: str = ""
    user_id: int | None = None
    lab_id: int | None = None

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()


@dataclass
class OrderCreated(DomainEvent):
    event_type: str = "order.created"


@dataclass
class OrderValidated(DomainEvent):
    event_type: str = "order.validated"


@dataclass
class ResultUpdated(DomainEvent):
    event_type: str = "result.updated"


@dataclass
class ResultCritical(DomainEvent):
    event_type: str = "result.critical"


@dataclass
class SampleCollected(DomainEvent):
    event_type: str = "sample.collected"


@dataclass
class PatientCreated(DomainEvent):
    event_type: str = "patient.created"


@dataclass
class AlertTriggered(DomainEvent):
    event_type: str = "alert.triggered"


__all__ = [
    "AlertTriggered",
    "DomainEvent",
    "OrderCreated",
    "OrderValidated",
    "PatientCreated",
    "ResultCritical",
    "ResultUpdated",
    "SampleCollected",
]
