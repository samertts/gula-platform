"""Boundary validation for synthetic clinical development.

Every value entering the clinical package is checked here: synthetic-only
references, non-identifying labels, ICD/LOINC-style codes and UCUM-style units.
A value that resembles a real-world identifier is rejected before it can reach
any entity, repository or event.
"""

from __future__ import annotations

import math
import re
from datetime import UTC, datetime

from app.health_core.clinical.errors import ClinicalValidationError
from app.health_core.common import (
    InvalidSyntheticReferenceError,
    is_synthetic_id,
    reject_national_identifier,
)

ICD_CODE_RE = re.compile(r"^[A-TV-Z][0-9]{2}(?:\.[0-9A-Z]{1,4})?$")
LOINC_CODE_RE = re.compile(r"^[0-9]{4,6}-[0-9]$")

UCUM_UNITS = frozenset(
    {
        "/min",
        "bpm",
        "Cel",
        "degC",
        "mm[Hg]",
        "kg",
        "cm",
        "m",
        "%",
        "mmol/L",
        "mg/dL",
        "g/dL",
        "umol/L",
        "L",
        "mL",
    }
)

# Structure-only validation: the LOINC check digit is not recomputed.
CODE_UNITS: dict[str, frozenset[str]] = {
    "8867-4": frozenset({"/min", "bpm"}),
    "8310-5": frozenset({"Cel", "degC"}),
    "8480-6": frozenset({"mm[Hg]"}),
    "8462-4": frozenset({"mm[Hg]"}),
    "59408-5": frozenset({"%"}),
}

__all__ = [
    "CODE_UNITS",
    "ICD_CODE_RE",
    "LOINC_CODE_RE",
    "UCUM_UNITS",
    "require_finite_number",
    "require_icd_code",
    "require_label",
    "require_loinc_code",
    "require_synthetic_ref",
    "require_unit",
    "require_utc_timestamp",
    "utc_now_iso",
]


def require_synthetic_ref(value: str, *, field: str, prefix: str | None = None) -> str:
    """Accept only opaque ``SYN-`` references, optionally of a given kind."""
    reject_national_identifier(value, field=field)
    if not is_synthetic_id(value):
        raise InvalidSyntheticReferenceError(
            f"{field} must be a SYN- prefixed synthetic reference",
            details={"field": field},
        )
    if prefix is not None and not value.startswith(prefix):
        raise InvalidSyntheticReferenceError(
            f"{field} must use the {prefix} synthetic prefix",
            details={"field": field, "expected_prefix": prefix},
        )
    return value


def require_label(value: str, *, field: str, max_length: int = 120) -> str:
    """Accept a short, single-line synthetic label (never patient data)."""
    if not isinstance(value, str):
        raise ClinicalValidationError(
            f"{field} must be a string",
            details={"field": field},
        )
    cleaned = value.strip()
    if not cleaned or len(cleaned) > max_length:
        raise ClinicalValidationError(
            f"{field} must contain 1..{max_length} characters",
            details={"field": field, "max_length": max_length},
        )
    if any(character in cleaned for character in "\x00\r\n\t"):
        raise ClinicalValidationError(
            f"{field} must be a single line",
            details={"field": field},
        )
    return cleaned


def require_icd_code(value: str, *, field: str = "code") -> str:
    """Accept an ICD-style code (e.g. ``J18.9``) using structural validation."""
    candidate = require_label(value, field=field, max_length=16).upper()
    if not ICD_CODE_RE.fullmatch(candidate):
        raise ClinicalValidationError(
            f"{field} must be an ICD-style code (e.g. J18.9)",
            details={"field": field, "value": candidate},
        )
    return candidate


def require_loinc_code(value: str, *, field: str = "code") -> str:
    """Accept a LOINC-style code (e.g. ``8867-4``) using structural validation."""
    candidate = require_label(value, field=field, max_length=16).upper()
    if not LOINC_CODE_RE.fullmatch(candidate):
        raise ClinicalValidationError(
            f"{field} must be a LOINC-style code (e.g. 8867-4)",
            details={"field": field, "value": candidate},
        )
    return candidate


def require_unit(code: str, value: str, *, field: str = "unit") -> str:
    """Validate a UCUM-style unit and any code-specific unit constraint."""
    unit = require_label(value, field=field, max_length=24)
    if unit not in UCUM_UNITS:
        raise ClinicalValidationError(
            f"{field} is not a permitted UCUM-style unit",
            details={"field": field, "code": code, "unit": unit},
        )
    allowed = CODE_UNITS.get(code)
    if allowed is not None and unit not in allowed:
        raise ClinicalValidationError(
            f"{field} is not valid for observation code {code}",
            details={"field": field, "code": code, "unit": unit},
        )
    return unit


def require_finite_number(value: object, *, field: str) -> float:
    """Accept a finite real number and reject booleans, NaN and infinity."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ClinicalValidationError(
            f"{field} must be a finite number",
            details={"field": field},
        )
    number = float(value)
    if not math.isfinite(number):
        raise ClinicalValidationError(
            f"{field} must be a finite number",
            details={"field": field},
        )
    return number


def require_utc_timestamp(value: datetime, *, field: str) -> str:
    """Normalise a timezone-aware datetime to a UTC ISO-8601 string."""
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ClinicalValidationError(
            f"{field} must be a timezone-aware datetime",
            details={"field": field},
        )
    return value.astimezone(UTC).isoformat()


def utc_now_iso() -> str:
    """Return the current UTC instant as an ISO-8601 string."""
    return datetime.now(UTC).isoformat()
