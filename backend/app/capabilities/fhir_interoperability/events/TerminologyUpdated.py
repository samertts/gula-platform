from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class TerminologyUpdatedEvent:
    """TerminologyUpdated event for fhir_interoperability capability."""

    event_id: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    data: dict = field(default_factory=dict)
    version: int = 1
