from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class RegisterDeathCommand:
    citizen_id: str = ""
    date_of_death: datetime | None = None
    cause_of_death: str | None = None
    icd10_code: str | None = None
    death_certificate_number: str = ""
    attending_practitioner_id: str | None = None
    is_natural_cause: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}
