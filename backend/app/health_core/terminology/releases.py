"""Explicit, auditable release provenance for the curated terminology adapters.

Every version, URI, source and licence statement below was read from the offline
checkout; nothing was fetched from a network or inferred from an official
release. Where the checkout declares no version, the release record says
``UNDECLARED`` rather than inventing one.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from app.health_core.terminology.errors import TerminologyError, UnknownTerminologySystemError
from app.health_core.terminology.models import CoverageLevel, TerminologyRelease, TerminologySystem

CHECKOUT_HEAD = "2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0"
VERIFICATION_DATE = "2026-11-18"

ICD10_RELEASE = TerminologyRelease(
    system=TerminologySystem.ICD10.value,
    version="UNDECLARED",
    canonical_uri="http://hl7.org/fhir/sid/icd-10",
    source=(
        "offline checkout: backend/app/national/services/cds_engine.py:961,976,991 "
        "(ICD10-tagged codes); backend/app/health_core/clinical/validation.py:108 "
        "(documented code example); URI backend/app/integration/standards/terminology.py:31"
    ),
    verification_method=(
        "read-only AST/string inspection of the offline checkout at HEAD " + CHECKOUT_HEAD + "; "
        "structural pattern from backend/app/health_core/clinical/validation.py:22; "
        "no WHO release file present"
    ),
    license=(
        "content licence not verified offline; separate licence required "
        "(GLOSI/SECURITY_AND_LICENSE_POLICY.md:43; GLOSI/SOURCE_CATALOG.md:52)"
    ),
    verified_on=VERIFICATION_DATE,
    coverage=CoverageLevel.PARTIALLY_VERIFIED,
    notes=(
        "No ICD-10 release version or official dataset is declared in the checkout. "
        "A distinct ICD-11 value (2026) is declared at "
        "backend/app/routes/advanced_integrations.py:65 but belongs to a different "
        "code system and has no dataset here; it was not applied to this adapter."
    ),
)

LOINC_RELEASE = TerminologyRelease(
    system=TerminologySystem.LOINC.value,
    version="2.81",
    canonical_uri="http://loinc.org",
    source=(
        "offline checkout: backend/app/routes/advanced_integrations.py:64 (declared status "
        "version); backend/app/fhir/terminology.py:20-32 (controlled lab mappings); "
        "backend/app/health_core/clinical/validation.py:46-52 (observation code units); "
        "URI backend/app/fhir/_reference.py:48"
    ),
    verification_method=(
        "read-only inspection of curated code strings in the offline checkout at HEAD "
        + CHECKOUT_HEAD
        + "; version copied from a declared status response; no Regenstrief release "
        "file and no network access; official check-digit algorithm source and "
        "hand-verified vectors recorded in notes"
    ),
    license=(
        "LOINC licence required; content not redistributed "
        "(GLOSI/SOURCE_CATALOG.md:50; GLOSI/SECURITY_AND_LICENSE_POLICY.md:43)"
    ),
    verified_on=VERIFICATION_DATE,
    coverage=CoverageLevel.PARTIALLY_VERIFIED,
    notes=(
        "Version 2.81 is a declared runtime status value, not an independently verified "
        "official release artefact. The official numeric-code check-digit algorithm "
        "(LOINC Users' Guide Appendix C.1 'Calculating Mod 10 check digits', canonical "
        "URL https://loinc.org/check-digit, last updated 2026-09-30) was independently "
        "fetched and hand-verified before static transcription; verified vectors are "
        "12345->5, 718->7, 777->3, 4544->3, 2345->7. Curated codes with matching digits "
        "are VALID/VERIFIED and mismatches are rejected as INVALID. Letter-prefixed "
        "codes use Appendix C.2, which is NOT IMPLEMENTED and unverified. The licensed "
        "official LOINC release DATASET is still absent: licensed acquisition remains "
        "BLOCKED, coverage remains PARTIALLY_VERIFIED and full-release conformance is "
        "NOT claimed. The offline pattern at "
        "backend/app/health_core/clinical/validation.py:23 rejects 3-digit codes "
        "that the same checkout curates in backend/app/fhir/terminology.py; this "
        "adapter therefore uses a documented 3-6 digit structural pattern."
    ),
)

UCUM_RELEASE = TerminologyRelease(
    system=TerminologySystem.UCUM.value,
    version="UNDECLARED",
    canonical_uri="http://unitsofmeasure.org",
    source=(
        "offline checkout: backend/app/health_core/clinical/validation.py:25-43 "
        "(UCUM_UNITS allowlist); URIs backend/app/fhir/_reference.py:62 and "
        "backend/app/integration/standards/terminology.py:34"
    ),
    verification_method=(
        "read-only extraction of the 15 UCUM_UNITS literals from the offline checkout at "
        "HEAD " + CHECKOUT_HEAD + "; exact case-sensitive allowlist comparison only; "
        "full UCUM grammar not parsed"
    ),
    license="separate review required (GLOSI/SOURCE_CATALOG.md:53)",
    verified_on=VERIFICATION_DATE,
    coverage=CoverageLevel.PARTIALLY_VERIFIED,
    notes=(
        "No UCUM release version is declared in the checkout. Local lab fixture units "
        "are deliberately excluded. Unit conversion and full UCUM syntax validation "
        "are out of scope."
    ),
)

TERMINOLOGY_RELEASES: Mapping[str, TerminologyRelease] = MappingProxyType(
    {
        TerminologySystem.ICD10.value: ICD10_RELEASE,
        TerminologySystem.LOINC.value: LOINC_RELEASE,
        TerminologySystem.UCUM.value: UCUM_RELEASE,
    }
)


class ReleaseResolutionError(TerminologyError):
    """Base class for release-lineage resolution failures."""

    code = "RELEASE_RESOLUTION_ERROR"


class UnknownReleaseVersionError(ReleaseResolutionError):
    """No lineage record exists for the requested version."""

    code = "UNKNOWN_RELEASE_VERSION"


class AmbiguousReleaseVersionError(ReleaseResolutionError):
    """A version string maps to more than one code system and cannot be resolved."""

    code = "AMBIGUOUS_RELEASE_VERSION"


class NoPreviousReleaseError(ReleaseResolutionError):
    """No earlier recorded lineage entry exists to roll back to."""

    code = "NO_PREVIOUS_RELEASE"


@dataclass(frozen=True, slots=True)
class ReleaseLineageRecord:
    """One immutable, resolvable entry in the curated release lineage.

    ``official_artifact`` is always False in this offline checkout: none of the
    records below represents an official released artefact. A version string is
    an auditable claim, never proof of licensed content.
    """

    system: str
    version: str
    release: TerminologyRelease
    official_artifact: bool
    note: str


# Frozen, ordered linearly: earlier entries precede later ones for the same
# system. There is exactly one recorded version per system today, so a rollback
# fails closed with NoPreviousReleaseError rather than inventing a prior artefact.
RELEASE_LINEAGE: tuple[ReleaseLineageRecord, ...] = (
    ReleaseLineageRecord(
        TerminologySystem.ICD10.value,
        "UNDECLARED",
        ICD10_RELEASE,
        False,
        "no ICD-10 version declared offline; no official artefact to roll back to",
    ),
    ReleaseLineageRecord(
        TerminologySystem.LOINC.value,
        "2.81",
        LOINC_RELEASE,
        False,
        "declared runtime status value only; official licensed dataset BLOCKED",
    ),
    ReleaseLineageRecord(
        TerminologySystem.UCUM.value,
        "UNDECLARED",
        UCUM_RELEASE,
        False,
        "no UCUM version declared offline; no official artefact to roll back to",
    ),
)


VALID_SYSTEM_KEYS: tuple[str, ...] = tuple(system.value for system in TerminologySystem)


def _lineage_versions() -> tuple[str, ...]:
    return tuple(record.version for record in RELEASE_LINEAGE)


def resolve_release(version: str) -> ReleaseLineageRecord:
    """Resolve a version to exactly one lineage record, failing closed otherwise."""
    if not isinstance(version, str) or not version:
        raise UnknownReleaseVersionError("release version must be a non-empty string")
    matches = tuple(record for record in RELEASE_LINEAGE if record.version == version)
    if not matches:
        raise UnknownReleaseVersionError(
            f"no release lineage record for version {version!r}",
            details={"version": version, "available": _lineage_versions()},
        )
    if len(matches) > 1:
        raise AmbiguousReleaseVersionError(
            f"version {version!r} is ambiguous across code systems",
            details={"version": version, "systems": tuple(record.system for record in matches)},
        )
    return matches[0]


def previous_release(system: TerminologySystem | str, version: str) -> ReleaseLineageRecord:
    """Return the immediately earlier lineage record for a system's version.

    Fails closed on an unknown system, an unknown version, and when no earlier
    recorded version exists. It never fabricates a prior released artefact.
    """
    key = system.value if isinstance(system, TerminologySystem) else system
    if not isinstance(version, str) or not version:
        raise UnknownReleaseVersionError("release version must be a non-empty string")
    system_records = tuple(record for record in RELEASE_LINEAGE if record.system == key)
    if not system_records:
        raise UnknownTerminologySystemError(
            f"no curated terminology release lineage for {key!r}",
            details={"system": key, "available": tuple(VALID_SYSTEM_KEYS)},
        )
    index = next((i for i, record in enumerate(system_records) if record.version == version), None)
    if index is None:
        raise UnknownReleaseVersionError(
            f"no release lineage record for {key!r} version {version!r}",
            details={"system": key, "version": version, "available": tuple(record.version for record in system_records)},
        )
    if index == 0:
        raise NoPreviousReleaseError(
            f"no earlier recorded release for {key!r} before {version!r}",
            details={"system": key, "version": version},
        )
    return system_records[index - 1]


def get_release(system: TerminologySystem | str) -> TerminologyRelease:
    """Return the release record for a code system, failing closed if unknown."""
    key = system.value if isinstance(system, TerminologySystem) else system
    release = TERMINOLOGY_RELEASES.get(key)
    if release is None:
        raise UnknownTerminologySystemError(
            f"no curated terminology release for {key!r}",
            details={"system": key, "available": tuple(TERMINOLOGY_RELEASES)},
        )
    return release


def all_releases() -> tuple[TerminologyRelease, ...]:
    """Return every curated release record in a stable order."""
    return tuple(TERMINOLOGY_RELEASES[system.value] for system in TerminologySystem)


__all__ = [
    "CHECKOUT_HEAD",
    "ICD10_RELEASE",
    "LOINC_RELEASE",
    "RELEASE_LINEAGE",
    "TERMINOLOGY_RELEASES",
    "UCUM_RELEASE",
    "VALID_SYSTEM_KEYS",
    "VERIFICATION_DATE",
    "AmbiguousReleaseVersionError",
    "NoPreviousReleaseError",
    "ReleaseLineageRecord",
    "ReleaseResolutionError",
    "UnknownReleaseVersionError",
    "all_releases",
    "get_release",
    "previous_release",
    "resolve_release",
]
