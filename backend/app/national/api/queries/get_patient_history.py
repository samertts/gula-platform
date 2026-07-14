from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class GetPatientHistoryQuery:
    patient_id: str = ""
    from_date: date | None = None
    to_date: date | None = None
    include_encounters: bool = True
    include_results: bool = True
    include_visits: bool = True
