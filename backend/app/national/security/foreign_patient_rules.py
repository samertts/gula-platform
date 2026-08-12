from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ForeignPatientRule:
    requires_passport: bool = True
    requires_visa: bool = True
    requires_sponsor: bool = True
    requires_biometrics: bool = True
    max_validity_days: int = 365
    restricted_services: list[str] | None = None


class ForeignPatientRulesService:
    def get_rules(self, passport_country: str, visa_type: str | None = None) -> ForeignPatientRule:
        rules = ForeignPatientRule()
        if passport_country in {"GCC", "SA", "AE", "QA", "KW", "BH", "OM"}:
            rules.requires_visa = False
            rules.max_validity_days = 180
        if visa_type == "diplomatic":
            rules.requires_sponsor = False
            rules.requires_biometrics = False
            rules.max_validity_days = 730
        elif visa_type == "tourist":
            rules.requires_sponsor = False
            rules.restricted_services = ["elective_surgery", "chronic_care"]
        return rules

    def requires_emergency_health_number(self, has_insurance: bool) -> bool:
        return not has_insurance
