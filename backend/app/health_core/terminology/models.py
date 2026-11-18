"""Value records for release-aware terminology validation.

Nothing in this package claims full official-release conformance. Every release
is explicitly PARTIALLY VERIFIED against curated material that was actually
inspected in the offline checkout. Validation results always carry the release
record used to produce them, so a consumer can audit the exact version and
provenance behind an accept/reject decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TerminologySystem(StrEnum):
    """The three code systems for which curated offline adapters exist."""

    ICD10 = "ICD-10"
    LOINC = "LOINC"
    UCUM = "UCUM"


class ValidationStatus(StrEnum):
    """Outcome of validating one code against one curated release."""

    VALID = "VALID"
    INVALID = "INVALID"
    UNVERIFIED = "UNVERIFIED"


class VerificationStage(StrEnum):
    """How far a code was checked. FULL_RELEASE_CONFORMANCE is never emitted here."""

    STRUCTURAL = "STRUCTURAL"
    CURATED_ALLOWLIST = "CURATED_ALLOWLIST"
    FULL_RELEASE_CONFORMANCE = "FULL_RELEASE_CONFORMANCE"


class CoverageLevel(StrEnum):
    """Documented coverage of a release record. FULL_RELEASE is never assigned here."""

    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    FULL_RELEASE = "FULL_RELEASE"


class CheckDigitStatus(StrEnum):
    """Whether a code's check digit was independently recomputed.

    ``VERIFIED`` and ``MISMATCH`` are only emitted for LOINC codes checked with
    the official, statically-transcribed Appendix C.1 Mod-10 algorithm. The
    three pre-existing members are preserved for backwards compatibility.
    """

    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_VERIFIED_OFFLINE = "NOT_VERIFIED_OFFLINE"
    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"


@dataclass(frozen=True, slots=True)
class CuratedCode:
    """One code or unit copied verbatim from an inspected offline source."""

    code: str
    source_ref: str
    display: str | None = None


@dataclass(frozen=True, slots=True)
class TerminologyRelease:
    """Explicit provenance for one curated terminology release.

    ``version`` may be ``UNDECLARED`` when the offline checkout declares no
    release version; that is an auditable fact, not a fabricated version.
    """

    system: str
    version: str
    canonical_uri: str
    source: str
    verification_method: str
    license: str
    verified_on: str
    coverage: CoverageLevel
    notes: str

    def to_dict(self) -> dict[str, object]:
        """Return a serialisable provenance record for audit consumers."""
        return {
            "system": self.system,
            "version": self.version,
            "canonical_uri": self.canonical_uri,
            "source": self.source,
            "verification_method": self.verification_method,
            "license": self.license,
            "verified_on": self.verified_on,
            "coverage": self.coverage.value,
            "notes": self.notes,
        }


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Structured validation outcome carrying the exact release used."""

    code: str
    normalized_code: str | None
    system: str
    status: ValidationStatus
    stage: VerificationStage
    reason: str
    release: TerminologyRelease
    source_ref: str | None
    check_digit: CheckDigitStatus

    @property
    def version(self) -> str:
        """The release version recorded on the result."""
        return self.release.version

    @property
    def accepted(self) -> bool:
        """True only for an explicit curated allowlist acceptance."""
        return self.status is ValidationStatus.VALID

    def to_dict(self) -> dict[str, object]:
        """Return an audit-friendly serialisation including full provenance."""
        return {
            "code": self.code,
            "normalized_code": self.normalized_code,
            "system": self.system,
            "status": self.status.value,
            "stage": self.stage.value,
            "reason": self.reason,
            "version": self.release.version,
            "source_ref": self.source_ref,
            "check_digit": self.check_digit.value,
            "provenance": self.release.to_dict(),
        }


__all__ = [
    "CheckDigitStatus",
    "CoverageLevel",
    "CuratedCode",
    "TerminologyRelease",
    "TerminologySystem",
    "ValidationResult",
    "ValidationStatus",
    "VerificationStage",
]
