from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GetEncounterQuery:
    encounter_id: str = ""
    patient_id: str | None = None
