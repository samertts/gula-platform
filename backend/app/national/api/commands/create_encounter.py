from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class CreateEncounterCommand:
    patient_id: str = ""
    encounter_type: str = "outpatient"
    facility_id: str | None = None
    practitioner_id: str | None = None
    reason: str | None = None
    period_start: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}
