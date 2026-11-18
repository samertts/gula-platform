"""Release-aware terminology validation for the isolated Health Core slice.

This package provides interfaces, adapters and explicit provenance records for
ICD-10, LOINC and UCUM. It is synthetic development code only: coverage is
PARTIALLY VERIFIED against a small offline allowlist, it is not production
activated, and it does not lift the governing HOLD decision.
"""

from __future__ import annotations

from app.health_core.terminology.checkdigit import (
    CHECK_DIGIT_ALGORITHM_SOURCE,
    CHECK_DIGIT_CANONICAL_URL,
    CheckDigitOutcome,
    CheckDigitResult,
    InvalidLoincBodyError,
    compute_loinc_check_digit,
    validate_loinc_check_digit,
)
from app.health_core.terminology.curated import ICD10_CODES, LOINC_CODES, UCUM_UNITS
from app.health_core.terminology.errors import TerminologyError, UnknownTerminologySystemError
from app.health_core.terminology.models import (
    CheckDigitStatus,
    CoverageLevel,
    CuratedCode,
    TerminologyRelease,
    TerminologySystem,
    ValidationResult,
    ValidationStatus,
    VerificationStage,
)
from app.health_core.terminology.ports import TerminologyValidator
from app.health_core.terminology.registry import (
    VALIDATORS,
    all_validator_releases,
    get_validator,
    validator_systems,
)
from app.health_core.terminology.releases import (
    CHECKOUT_HEAD,
    ICD10_RELEASE,
    LOINC_RELEASE,
    RELEASE_LINEAGE,
    TERMINOLOGY_RELEASES,
    UCUM_RELEASE,
    VERIFICATION_DATE,
    AmbiguousReleaseVersionError,
    NoPreviousReleaseError,
    ReleaseLineageRecord,
    ReleaseResolutionError,
    UnknownReleaseVersionError,
    all_releases,
    get_release,
    previous_release,
    resolve_release,
)
from app.health_core.terminology.validators import IcdValidator, LoincValidator, UcumValidator

__all__ = [
    "CHECKOUT_HEAD",
    "CHECK_DIGIT_ALGORITHM_SOURCE",
    "CHECK_DIGIT_CANONICAL_URL",
    "ICD10_CODES",
    "ICD10_RELEASE",
    "LOINC_CODES",
    "LOINC_RELEASE",
    "RELEASE_LINEAGE",
    "TERMINOLOGY_RELEASES",
    "UCUM_RELEASE",
    "UCUM_UNITS",
    "VALIDATORS",
    "VERIFICATION_DATE",
    "AmbiguousReleaseVersionError",
    "CheckDigitOutcome",
    "CheckDigitResult",
    "CheckDigitStatus",
    "CoverageLevel",
    "CuratedCode",
    "IcdValidator",
    "InvalidLoincBodyError",
    "LoincValidator",
    "NoPreviousReleaseError",
    "ReleaseLineageRecord",
    "ReleaseResolutionError",
    "TerminologyError",
    "TerminologyRelease",
    "TerminologySystem",
    "TerminologyValidator",
    "UcumValidator",
    "UnknownReleaseVersionError",
    "UnknownTerminologySystemError",
    "ValidationResult",
    "ValidationStatus",
    "VerificationStage",
    "all_releases",
    "all_validator_releases",
    "compute_loinc_check_digit",
    "get_release",
    "get_validator",
    "previous_release",
    "resolve_release",
    "validate_loinc_check_digit",
    "validator_systems",
]
