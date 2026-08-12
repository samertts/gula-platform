from __future__ import annotations

from enum import Enum


class Healthcare_consentPermission(Enum):
    READ = "healthcare_consent:consent.read"
    WRITE = "healthcare_consent:consent.write"
    BREAK_GLASS = "healthcare_consent:consent.break_glass"
    ADMIN = "healthcare_consent:consent.admin"

    def describe(self) -> str:
        descriptions = {        "healthcare_consent:consent.read": "Consent.Read",
                "healthcare_consent:consent.write": "Consent.Write",
                "healthcare_consent:consent.break_glass": "Consent.Break Glass",
                "healthcare_consent:consent.admin": "Consent.Admin"}
        return descriptions.get(self, self.value)
