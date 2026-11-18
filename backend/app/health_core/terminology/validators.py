"""Three curated adapters: ICD-10, LOINC and UCUM.

Validation is layered and never silently accepts a code:

1. input/structural validation (format only);
2. curated-allowlist verification against code strings actually present in the
   offline checkout;
3. full official-release conformance -- NOT available offline and therefore
   never claimed by these adapters.

A structurally well-formed code outside the curated set is UNVERIFIED, not
VALID. A malformed code, a case-mismatched UCUM unit, a synthetic fixture
reference or a real-identifier-shaped value is INVALID.
"""

from __future__ import annotations

import re
from typing import ClassVar

from app.health_core.terminology.checkdigit import (
    CHECK_DIGIT_PREFIX_ALGORITHM_NOT_IMPLEMENTED,
    validate_loinc_check_digit,
)
from app.health_core.terminology.curated import ICD10_CODES, LOINC_CODES, UCUM_UNITS
from app.health_core.terminology.models import (
    CheckDigitStatus,
    CuratedCode,
    TerminologyRelease,
    TerminologySystem,
    ValidationResult,
    ValidationStatus,
    VerificationStage,
)
from app.health_core.terminology.releases import get_release

_ICD10_PATTERN = re.compile(r"^[A-TV-Z][0-9]{2}(?:\.[0-9A-Z]{1,4})?$")
# The pattern at clinical/validation.py:23 demands 4-6 digits before the hyphen,
# but the same checkout curates 3-digit LOINC codes (718-7, 777-3) in
# fhir/terminology.py. This adapter accepts 3-6 digits so its own curated set is
# self-consistent; the discrepancy is recorded in LOINC_RELEASE.notes.
_LOINC_PATTERN = re.compile(r"^[0-9]{3,6}-[0-9]$")
_UCUM_FORMAT_PATTERN = re.compile(r"^[/A-Za-z0-9%][A-Za-z0-9%/.^\[\]-]*$")
_LONG_DIGITS = re.compile(r"^\d{5,}$")
_LONG_UPPER_ALNUM = re.compile(r"^[A-Z0-9]{9,}$")

_UNVERIFIED_REASON = (
    "well-formed but not present in the curated offline allowlist; no full official "
    "release dataset is available, so the code cannot be verified"
)


def _is_real_identifier_shaped(value: str) -> bool:
    """Conservatively detect values that resemble a real-world identifier."""
    return bool(_LONG_DIGITS.fullmatch(value) or _LONG_UPPER_ALNUM.fullmatch(value))


class _CuratedValidator:
    """Shared mechanics for a structural-stage plus curated-allowlist adapter."""

    _system: ClassVar[str]
    _pattern: ClassVar[re.Pattern[str]]
    _entries: ClassVar[tuple[CuratedCode, ...]]
    _check_digit: ClassVar[CheckDigitStatus] = CheckDigitStatus.NOT_APPLICABLE
    _check_note: ClassVar[str] = "no check-digit verification performed for this system"

    def __init__(self) -> None:
        by_code: dict[str, CuratedCode] = {}
        folded: dict[str, CuratedCode] = {}
        for entry in self._entries:
            if not entry.code or entry.code in by_code:
                raise ValueError(f"invalid or duplicate curated code for {self._system}: {entry.code!r}")
            if not entry.source_ref:
                raise ValueError(f"curated code without source reference: {entry.code!r}")
            by_code[entry.code] = entry
            folded.setdefault(entry.code.casefold(), entry)
        self._by_code: dict[str, CuratedCode] = by_code
        self._folded: dict[str, CuratedCode] = folded

    @property
    def system(self) -> str:
        """Stable code-system identity."""
        return self._system

    @property
    def release(self) -> TerminologyRelease:
        """Release record backing this validator."""
        return get_release(self._system)

    def provenance(self) -> TerminologyRelease:
        """Expose the release record for registry and audit consumers."""
        return self.release

    def _make(
        self,
        code: str,
        normalized: str | None,
        status: ValidationStatus,
        stage: VerificationStage,
        reason: str,
        entry: CuratedCode | None = None,
        check_digit: CheckDigitStatus | None = None,
    ) -> ValidationResult:
        release: TerminologyRelease = get_release(self._system)
        return ValidationResult(
            code=code,
            normalized_code=normalized,
            system=self._system,
            status=status,
            stage=stage,
            reason=reason,
            release=release,
            source_ref=entry.source_ref if entry is not None else None,
            check_digit=self._check_digit if check_digit is None else check_digit,
        )

    def _reject_string(self, value: str) -> ValidationResult | None:
        """Return an INVALID result for inputs that cannot be codes at all."""
        if not value:
            return self._make(value, None, ValidationStatus.INVALID, VerificationStage.STRUCTURAL, "code must not be empty")
        if value.strip() != value:
            return self._make(
                value,
                None,
                ValidationStatus.INVALID,
                VerificationStage.STRUCTURAL,
                "code must not have leading or trailing whitespace",
            )
        if any(character in value for character in "\x00\r\n\t"):
            return self._make(
                value,
                None,
                ValidationStatus.INVALID,
                VerificationStage.STRUCTURAL,
                "code must be a single line without control characters",
            )
        if value.startswith("SYN-"):
            return self._make(
                value,
                None,
                ValidationStatus.INVALID,
                VerificationStage.STRUCTURAL,
                "synthetic fixture references are not terminology codes",
            )
        if _is_real_identifier_shaped(value):
            return self._make(
                value,
                None,
                ValidationStatus.INVALID,
                VerificationStage.STRUCTURAL,
                "value resembles a real-world identifier and is not a terminology code",
            )
        return None

    def _reject_non_string(self, value: object) -> ValidationResult:
        return self._make(
            repr(value),
            None,
            ValidationStatus.INVALID,
            VerificationStage.STRUCTURAL,
            "code must be a string",
        )

    def _structural_failure(self, code: str, candidate: str) -> ValidationResult:
        return self._make(
            code,
            None,
            ValidationStatus.INVALID,
            VerificationStage.STRUCTURAL,
            f"{candidate!r} does not match the {self._system} structure recorded offline",
        )

    def _unverified(self, code: str, candidate: str) -> ValidationResult:
        return self._make(
            code,
            candidate,
            ValidationStatus.UNVERIFIED,
            VerificationStage.STRUCTURAL,
            f"{_UNVERIFIED_REASON}; {self._check_note}",
        )

    def _curated(
        self,
        code: str,
        candidate: str,
        entry: CuratedCode,
        check_digit: CheckDigitStatus | None = None,
    ) -> ValidationResult:
        return self._make(
            code,
            candidate,
            ValidationStatus.VALID,
            VerificationStage.CURATED_ALLOWLIST,
            f"curated allowlist match at {entry.source_ref}; {self._check_note}",
            entry,
            check_digit=check_digit,
        )


class IcdValidator(_CuratedValidator):
    """ICD-10: offline structural pattern, then a four-code curated allowlist."""

    _system = TerminologySystem.ICD10.value
    _pattern = _ICD10_PATTERN
    _entries = ICD10_CODES
    _check_note = "structural pattern and curated allowlist only; official release conformance not verified"

    def validate(self, code: object) -> ValidationResult:
        """Accept only ICD-10-shaped codes present in the curated allowlist."""
        if not isinstance(code, str):
            return self._reject_non_string(code)
        rejection = self._reject_string(code)
        if rejection is not None:
            return rejection
        candidate = code.strip().upper()
        if not self._pattern.fullmatch(candidate):
            return self._structural_failure(code, candidate)
        entry = self._by_code.get(candidate)
        if entry is None:
            return self._unverified(code, candidate)
        return self._curated(code, candidate, entry)


class LoincValidator(_CuratedValidator):
    """LOINC: structural pattern, curated allowlist, official Mod-10 check digit.

    Numeric codes are checked with the official Appendix C.1 Mod-10 algorithm
    transcribed statically in ``checkdigit.py`` from the authoritative canonical
    URL https://loinc.org/check-digit (independently fetched and hand-verified
    before implementation). A curated code with a matching check digit is
    VALID/VERIFIED; a curated code with a mismatching digit is INVALID. Letter-
    prefixed codes (LP/LL/LA/LG, ...) use the different Appendix C.2 algorithm,
    which is NOT implemented and is rejected. A well-formed code outside the
    curated allowlist stays UNVERIFIED. Full official-release conformance is
    still NOT claimed because the licensed release dataset is absent.
    """

    _system = TerminologySystem.LOINC.value
    _pattern = _LOINC_PATTERN
    _entries = LOINC_CODES
    _check_digit = CheckDigitStatus.NOT_VERIFIED_OFFLINE
    _check_note = (
        "official LOINC Mod-10 check digit recomputed from https://loinc.org/check-digit "
        "(Appendix C.1) and VERIFIED for curated codes; full official-release conformance not claimed"
    )

    def validate(self, code: object) -> ValidationResult:
        """Accept only curated LOINC codes with a matching official check digit."""
        if not isinstance(code, str):
            return self._reject_non_string(code)
        rejection = self._reject_string(code)
        if rejection is not None:
            return rejection
        candidate = code.strip().upper()

        # Letter-prefixed LOINC codes use Appendix C.2, which is not implemented
        # or verified. Fail closed before any curated-acceptance path is reached.
        first_segment = candidate.split("-", 1)[0]
        if any(character.isalpha() for character in first_segment):
            return self._make(
                code,
                None,
                ValidationStatus.INVALID,
                VerificationStage.STRUCTURAL,
                CHECK_DIGIT_PREFIX_ALGORITHM_NOT_IMPLEMENTED,
            )

        if not self._pattern.fullmatch(candidate):
            # LOINC diagnostics must not echo the inspected value (I-2). The
            # shared ICD/UCUM structural reason is left untouched.
            return self._make(
                code,
                None,
                ValidationStatus.INVALID,
                VerificationStage.STRUCTURAL,
                "value does not match the LOINC structure recorded offline; check digit not evaluated",
            )
        entry = self._by_code.get(candidate)
        if entry is None:
            # Never compute or disclose a checksum verdict for an uncurated code:
            # it remains UNVERIFIED and is never promoted to VALID.
            return self._unverified(code, candidate)

        verdict = validate_loinc_check_digit(candidate)
        if not verdict.valid:
            return self._make(
                code,
                None,
                ValidationStatus.INVALID,
                VerificationStage.CURATED_ALLOWLIST,
                f"official LOINC check-digit verification failed: {verdict.reason}; code rejected",
                check_digit=CheckDigitStatus.MISMATCH,
            )
        return self._curated(code, candidate, entry, check_digit=CheckDigitStatus.VERIFIED)


class UcumValidator(_CuratedValidator):
    """UCUM: exact, case-sensitive match against the 15 offline allowlist units."""

    _system = TerminologySystem.UCUM.value
    _pattern = _UCUM_FORMAT_PATTERN
    _entries = UCUM_UNITS
    _check_note = "exact case-sensitive allowlist only; full UCUM grammar not parsed"

    def validate(self, code: object) -> ValidationResult:
        """Accept only exact curated UCUM unit strings."""
        if not isinstance(code, str):
            return self._reject_non_string(code)
        rejection = self._reject_string(code)
        if rejection is not None:
            return rejection
        candidate = code
        if not self._pattern.fullmatch(candidate):
            return self._structural_failure(code, candidate)
        entry = self._by_code.get(candidate)
        if entry is None:
            folded = self._folded.get(candidate.casefold())
            if folded is not None:
                return self._make(
                    code,
                    None,
                    ValidationStatus.INVALID,
                    VerificationStage.STRUCTURAL,
                    f"UCUM units are case-sensitive; {candidate!r} differs from curated {folded.code!r}",
                )
            return self._unverified(code, candidate)
        return self._curated(code, candidate, entry)


__all__ = ["IcdValidator", "LoincValidator", "UcumValidator"]
