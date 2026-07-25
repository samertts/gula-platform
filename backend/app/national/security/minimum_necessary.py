from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DataCategory(Enum):
    DEMOGRAPHICS = "demographics"
    CONTACT = "contact"
    CLINICAL = "clinical"
    FINANCIAL = "financial"
    IDENTIFYING = "identifying"
    SENSITIVE = "sensitive"
    ALL = "all"


@dataclass
class DataField:
    name: str
    category: DataCategory
    sensitive: bool = False


MINIMUM_NECESSARY_FIELDS: dict[str, list[str]] = {
    "treatment": [
        "name",
        "date_of_birth",
        "gender",
        "blood_group",
        "allergies",
        "diagnoses",
        "medications",
    ],
    "registration": ["name", "date_of_birth", "gender", "phone", "address", "nationality"],
    "billing": ["name", "health_number", "coverage_info", "service_codes"],
    "research": ["age_group", "gender", "diagnosis_code", "outcome"],
    "emergency": ["name", "blood_group", "allergies", "emergency_contact", "diagnoses"],
    "public_health": ["age_group", "gender", "governorate", "diagnosis_code"],
}


class MinimumNecessaryEngine:
    def get_allowed_fields(self, purpose: str) -> list[str]:
        return MINIMUM_NECESSARY_FIELDS.get(purpose, MINIMUM_NECESSARY_FIELDS["treatment"])

    def filter_data(self, data: dict[str, Any], purpose: str) -> dict[str, Any]:
        allowed = self.get_allowed_fields(purpose)
        return {k: v for k, v in data.items() if k in allowed}

    def is_field_allowed(self, field_name: str, purpose: str) -> bool:
        allowed = self.get_allowed_fields(purpose)
        return field_name in allowed
