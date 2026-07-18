from dataclasses import dataclass, field
from typing import Any


@dataclass
class CreatePatientCommand:
    lab_id: str = ""
    first_name: str = ""
    father_name: str = ""
    last_name: str = ""
    date_of_birth: str = ""
    gender: str = ""
    phone: str = ""
    national_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdatePatientCommand:
    patient_id: str = ""
    first_name: str = ""
    father_name: str = ""
    last_name: str = ""
    phone: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchPatientQuery:
    query: str = ""
    lab_id: str = ""
    limit: int = 20


@dataclass
class GetPatientQuery:
    patient_id: str = ""
