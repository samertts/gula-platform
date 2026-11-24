"""Synthetic test-code catalogue used by the lab workflow.

The codes below are local fixtures. They are deliberately not LOINC codes and
carry no linkage to any real national identity or terminology service.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.health_core.lab.errors import UnknownTestCodeError


@dataclass(frozen=True, slots=True)
class TestDefinition:
    """A synthetic test definition with a locally defined reference range."""

    code: str
    display_name: str
    unit: str
    reference_low: float
    reference_high: float
    critical_low: float | None = None
    critical_high: float | None = None

    def __post_init__(self) -> None:
        if self.reference_low >= self.reference_high:
            raise ValueError("reference_low must be smaller than reference_high")
        if (
            self.critical_low is not None
            and self.critical_high is not None
            and self.critical_low >= self.critical_high
        ):
            raise ValueError("critical_low must be smaller than critical_high")
        if not self.code or not self.unit:
            raise ValueError("test code and unit must not be empty")


TEST_CATALOGUE: dict[str, TestDefinition] = {
    definition.code: definition
    for definition in (
        TestDefinition("GLU", "Glucose", "mg/dL", 70.0, 99.0, 40.0, 400.0),
        TestDefinition("HBA1C", "Glycated haemoglobin", "%", 4.0, 5.6, None, 10.0),
        TestDefinition("WBC", "White blood cells", "10^3/uL", 4.0, 11.0, 1.0, 30.0),
        TestDefinition("CRP", "C-reactive protein", "mg/L", 0.0, 5.0, None, 100.0),
        TestDefinition("ALT", "Alanine aminotransferase", "U/L", 7.0, 35.0, None, 500.0),
        TestDefinition("AST", "Aspartate aminotransferase", "U/L", 8.0, 33.0, None, 500.0),
    )
}


def catalogue_codes() -> tuple[str, ...]:
    """Return the sorted tuple of known synthetic test codes."""
    return tuple(sorted(TEST_CATALOGUE))


def is_known_test_code(code: str) -> bool:
    """Return True when the code exists in the synthetic catalogue."""
    return code.strip().upper() in TEST_CATALOGUE


def get_test_definition(code: str) -> TestDefinition:
    """Return a catalogue definition, failing closed for unknown codes."""
    key = code.strip().upper()
    definition = TEST_CATALOGUE.get(key)
    if definition is None:
        raise UnknownTestCodeError(
            f"unknown synthetic test code: {code!r}",
            details={"test_code": code, "available": catalogue_codes()},
        )
    return definition
