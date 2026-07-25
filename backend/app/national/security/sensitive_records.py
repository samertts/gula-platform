from __future__ import annotations

from enum import Enum


class SensitivityLevel(Enum):
    NORMAL = "normal"
    SENSITIVE = "sensitive"
    HIGHLY_SENSITIVE = "highly_sensitive"
    RESTRICTED = "restricted"


SENSITIVE_CONDITIONS = {
    "HIV": SensitivityLevel.HIGHLY_SENSITIVE,
    "MENTAL_HEALTH": SensitivityLevel.HIGHLY_SENSITIVE,
    "GENETIC": SensitivityLevel.HIGHLY_SENSITIVE,
    "SEXUAL_HEALTH": SensitivityLevel.SENSITIVE,
    "SUBSTANCE_ABUSE": SensitivityLevel.SENSITIVE,
    "CANCER": SensitivityLevel.SENSITIVE,
    "DOMESTIC_VIOLENCE": SensitivityLevel.RESTRICTED,
}

VIP_TITLES = {"president", "prime_minister", "minister", "judge", "mp", "general"}


class SensitiveRecordService:
    def get_sensitivity(self, condition: str) -> SensitivityLevel:
        return SENSITIVE_CONDITIONS.get(condition.upper(), SensitivityLevel.NORMAL)

    def is_sensitive(self, condition: str) -> bool:
        return self.get_sensitivity(condition) != SensitivityLevel.NORMAL

    def is_vip(self, occupation: str | None) -> bool:
        if not occupation:
            return False
        return occupation.lower() in VIP_TITLES

    def requires_break_glass(self, condition: str, user_role: str) -> bool:
        sensitivity = self.get_sensitivity(condition)
        if sensitivity == SensitivityLevel.RESTRICTED:
            return True
        return bool(
            sensitivity == SensitivityLevel.HIGHLY_SENSITIVE
            and user_role not in {"system_admin", "national_admin"},
        )
