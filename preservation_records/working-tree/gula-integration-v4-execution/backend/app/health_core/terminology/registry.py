"""Registry of the three curated terminology validators.

The registry is immutable and fails closed: requesting an uncurated code system
raises rather than returning a permissive validator.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from app.health_core.terminology.errors import UnknownTerminologySystemError
from app.health_core.terminology.models import TerminologyRelease, TerminologySystem
from app.health_core.terminology.ports import TerminologyValidator
from app.health_core.terminology.validators import IcdValidator, LoincValidator, UcumValidator

VALIDATORS: Mapping[str, TerminologyValidator] = MappingProxyType(
    {
        TerminologySystem.ICD10.value: IcdValidator(),
        TerminologySystem.LOINC.value: LoincValidator(),
        TerminologySystem.UCUM.value: UcumValidator(),
    }
)


def get_validator(system: TerminologySystem | str) -> TerminologyValidator:
    """Return the validator for a code system, failing closed if unknown."""
    key = system.value if isinstance(system, TerminologySystem) else system
    validator = VALIDATORS.get(key)
    if validator is None:
        raise UnknownTerminologySystemError(
            f"no curated validator for {key!r}",
            details={"system": key, "available": validator_systems()},
        )
    return validator


def validator_systems() -> tuple[str, ...]:
    """Return the stable tuple of registered code-system identities."""
    return tuple(VALIDATORS)


def all_validator_releases() -> tuple[TerminologyRelease, ...]:
    """Return one release record per registered validator."""
    return tuple(validator.provenance() for validator in VALIDATORS.values())


__all__ = ["VALIDATORS", "all_validator_releases", "get_validator", "validator_systems"]
