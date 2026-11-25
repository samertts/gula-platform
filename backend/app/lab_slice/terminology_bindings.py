"""Fail-closed terminology bindings for synthetic laboratory results.

The module reuses the existing national laboratory catalog and the curated LOINC
helper. It never invents an official code and marks unknown tests as unmapped so
that downstream release policy can fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.fhir.terminology import normalize_lab_test_name, observation_code
from app.services.reference.national_lab_catalog import NationalLaboratoryCatalog

BINDING_MAPPED = "mapped"
BINDING_LOCAL = "local"
BINDING_UNMAPPED = "unmapped"
LOINC_SYSTEM = "http://loinc.org"
LOCAL_TEST_SYSTEM = "urn:gula:lab-test-name"


@dataclass(frozen=True, slots=True)
class TerminologyBinding:
    test_code: str
    status: str
    code_system: str
    code: str
    display: str
    unit: str

    def codeable_concept(self) -> dict[str, object]:
        return {
            "coding": [
                {
                    "system": self.code_system,
                    "code": self.code,
                    "display": self.display,
                },
            ],
            "text": self.display,
        }


def bind_test(
    catalog: NationalLaboratoryCatalog,
    test_code: str,
    unit: str | None = None,
) -> TerminologyBinding:
    """Bind a catalog test to an explicit code system and unit."""
    test = catalog.get_test(test_code)
    display = test.name if test is not None else f"Unmapped synthetic test {test_code}"
    concept = observation_code(display)
    coding = concept["coding"][0]
    code_system = str(coding["system"])
    code = str(coding["code"])
    catalog_unit = test.unit if test is not None else ""
    effective_unit = (catalog_unit if unit is None else unit).strip()

    status = BINDING_MAPPED if code_system == LOINC_SYSTEM else BINDING_LOCAL
    if test is None or not effective_unit:
        status = BINDING_UNMAPPED
        code_system = LOCAL_TEST_SYSTEM
        code = normalize_lab_test_name(test_code).replace(" ", "-")

    return TerminologyBinding(
        test_code=test_code,
        status=status,
        code_system=code_system,
        code=code,
        display=display,
        unit=effective_unit,
    )
