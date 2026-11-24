"""The terminology validator interface.

Consumers depend on this Protocol, never on a concrete adapter. Every validator
must expose its code-system identity, its release record and a structured
validation result; a result is never a bare boolean, so UNVERIFIED is distinct
from INVALID and from a curated acceptance.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.health_core.terminology.models import TerminologyRelease, ValidationResult


@runtime_checkable
class TerminologyValidator(Protocol):
    """Read-only validator for one curated terminology release."""

    @property
    def system(self) -> str:
        """Stable code-system identity, e.g. ``LOINC``."""
        ...

    @property
    def release(self) -> TerminologyRelease:
        """The release record that governs this validator."""
        ...

    def validate(self, code: object) -> ValidationResult:
        """Return a structured result; never silently accept an unknown code."""
        ...

    def provenance(self) -> TerminologyRelease:
        """Return the same release record exposed for registry/audit access."""
        ...


__all__ = ["TerminologyValidator"]
