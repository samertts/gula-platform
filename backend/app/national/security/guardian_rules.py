from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GuardianRule:
    can_consent: bool = True
    can_access_records: bool = True
    can_make_appointments: bool = True
    can_receive_results: bool = True
    can_authorize_treatment: bool = True
    restrictions: list[str] | None = None


class GuardianRulesService:
    def get_guardian_rules(self, guardian_type: str, minor_age: int) -> GuardianRule:
        rules = GuardianRule()
        if guardian_type == "legal_guardian":
            pass
        elif guardian_type == "parent":
            pass
        elif guardian_type == "grandparent":
            rules.can_receive_results = False
        elif guardian_type == "sibling":
            if minor_age >= 16:
                rules.can_authorize_treatment = False
        else:
            rules.can_consent = False
            rules.can_authorize_treatment = False
        return rules

    def validate_guardian_action(self, guardian_type: str, minor_age: int, action: str) -> bool:
        rules = self.get_guardian_rules(guardian_type, minor_age)
        action_map = {
            "consent": rules.can_consent,
            "access_records": rules.can_access_records,
            "appointments": rules.can_make_appointments,
            "receive_results": rules.can_receive_results,
            "authorize_treatment": rules.can_authorize_treatment,
        }
        return action_map.get(action, False)
