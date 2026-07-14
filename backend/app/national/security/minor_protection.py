from __future__ import annotations

from datetime import date
from enum import Enum


class MinorProtectionLevel(Enum):
    FULL = "full"
    LIMITED = "limited"
    EMERGENCY_ONLY = "emergency_only"


class MinorProtectionService:
    MINOR_AGE = 18
    EMANCIPATED_AGE = 16

    def is_minor(self, date_of_birth: date) -> bool:
        if not date_of_birth:
            return True
        today = date.today()
        age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
        return age < self.MINOR_AGE

    def get_protection_level(self, date_of_birth: date, is_emancipated: bool = False) -> MinorProtectionLevel:
        if is_emancipated:
            return MinorProtectionLevel.LIMITED
        if self.is_minor(date_of_birth):
            return MinorProtectionLevel.FULL
        return MinorProtectionLevel.LIMITED

    def requires_guardian(self, date_of_birth: date, is_emancipated: bool = False) -> bool:
        return self.get_protection_level(date_of_birth, is_emancipated) == MinorProtectionLevel.FULL
