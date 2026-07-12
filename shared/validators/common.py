from __future__ import annotations

import re
from typing import Any

_IRAQI_NID_PATTERN = re.compile(r"^\d{10,14}$")
_IRAQI_PHONE_PATTERN = re.compile(r"^(?:\+964|0)(?:7[0-9]{8}|[1-6][0-9]{7})$")
_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

_VALID_SAMPLE_TYPES = {
    "blood", "serum", "plasma", "urine", "stool", "sputum",
    "cerebrospinal", "synovial", "amniotic", "tissue", "swab",
}


def validate_iraqi_national_id(value: str) -> tuple[bool, str]:
    if not _IRAQI_NID_PATTERN.match(value):
        return False, "Invalid Iraqi National ID format (must be 10-14 digits)"
    return True, ""


def validate_iraqi_phone(value: str) -> tuple[bool, str]:
    if not _IRAQI_PHONE_PATTERN.match(value):
        return False, "Invalid Iraqi phone number format"
    return True, ""


def validate_email(value: str) -> tuple[bool, str]:
    if not _EMAIL_PATTERN.match(value):
        return False, "Invalid email format"
    return True, ""


def validate_sample_type(value: str) -> tuple[bool, str]:
    if value.lower() not in _VALID_SAMPLE_TYPES:
        return False, f"Invalid sample type: {value}. Must be one of: {', '.join(sorted(_VALID_SAMPLE_TYPES))}"
    return True, ""


def validate_result_range(value: float, min_val: float | None, max_val: float | None) -> tuple[bool, str]:
    if min_val is not None and value < min_val:
        return False, f"Value {value} is below minimum {min_val}"
    if max_val is not None and value > max_val:
        return False, f"Value {value} exceeds maximum {max_val}"
    return True, ""


def validate_test_panel(test_names: list[str], valid_panels: set[str]) -> tuple[bool, str]:
    unknown = [t for t in test_names if t not in valid_panels]
    if unknown:
        return False, f"Unknown tests: {', '.join(unknown)}"
    return True, ""
