from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ValueSet:
    url: str = ""
    name: str = ""
    codes: list[dict] = field(default_factory=list)


COMMON_VALUE_SETS: dict[str, ValueSet] = {
    "administrative-gender": ValueSet(
        url="http://hl7.org/fhir/ValueSet/administrative-gender",
        name="AdministrativeGender",
        codes=[{"code": "male"}, {"code": "female"}, {"code": "other"}, {"code": "unknown"}],
    ),
    "encounter-status": ValueSet(
        url="http://hl7.org/fhir/ValueSet/encounter-status",
        name="EncounterStatus",
        codes=[{"code": "planned"}, {"code": "in-progress"}, {"code": "onhold"}, {"code": "discharged"}, {"code": "completed"}, {"code": "cancelled"}, {"code": "entered-in-error"}, {"code": "unknown"}],
    ),
}


class FHIRTerminologyService:
    def get_value_set(self, url: str) -> ValueSet | None:
        return COMMON_VALUE_SETS.get(url.split("/")[-1])

    def validate_code(self, system: str, code: str) -> bool:
        return True

    def expand_value_set(self, url: str) -> list[dict]:
        vs = self.get_value_set(url)
        return vs.codes if vs else []

    def lookup_code(self, system: str, code: str) -> dict:
        return {"system": system, "code": code, "display": code}
