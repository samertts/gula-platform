from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass
class RegisterCitizenCommand:
    first_name: str = ""
    father_name: str | None = None
    last_name: str = ""
    mother_name: str | None = None
    date_of_birth: date | None = None
    gender: str = "unknown"
    phone: str | None = None
    email: str | None = None
    governorate: str | None = None
    nationality: str = "Iraqi"
    identity_type: str = "iraqi_citizen"

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}
