from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class MedicationPrescribedEvent:
    """MedicationPrescribed event for clinical_foundation capability."""

    event_id: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    data: dict = field(default_factory=dict)
    version: int = 1
