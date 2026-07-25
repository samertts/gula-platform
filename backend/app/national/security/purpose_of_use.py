from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PurposeOfUse(Enum):
    TREATMENT = "TREATMENT"
    PAYMENT = "PAYMENT"
    OPERATIONS = "OPERATIONS"
    RESEARCH = "RESEARCH"
    PUBLIC_HEALTH = "PUBLIC_HEALTH"
    QUALITY_IMPROVEMENT = "QUALITY_IMPROVEMENT"
    EMERGENCY = "EMERGENCY"
    FRAUD_DETECTION = "FRAUD_DETECTION"
    DISCLOSURE = "DISCLOSURE"
    OTHER = "OTHER"


@dataclass
class PurposeOfUseValidation:
    purpose: PurposeOfUse
    is_valid: bool = True
    reason: str = ""
    requires_consent: bool = False
    requires_break_glass: bool = False
    allowed_roles: list[str] | None = None


class PurposeOfUseEngine:
    _PURPOSE_RULES = {
        PurposeOfUse.TREATMENT: {"requires_consent": False, "requires_break_glass": False},
        PurposeOfUse.EMERGENCY: {"requires_consent": False, "requires_break_glass": True},
        PurposeOfUse.PAYMENT: {"requires_consent": True, "requires_break_glass": False},
        PurposeOfUse.OPERATIONS: {"requires_consent": True, "requires_break_glass": False},
        PurposeOfUse.RESEARCH: {"requires_consent": True, "requires_break_glass": False},
        PurposeOfUse.PUBLIC_HEALTH: {"requires_consent": False, "requires_break_glass": False},
        PurposeOfUse.QUALITY_IMPROVEMENT: {"requires_consent": True, "requires_break_glass": False},
        PurposeOfUse.FRAUD_DETECTION: {"requires_consent": False, "requires_break_glass": False},
        PurposeOfUse.DISCLOSURE: {"requires_consent": True, "requires_break_glass": False},
    }

    def validate(self, purpose: PurposeOfUse) -> PurposeOfUseValidation:
        rules = self._PURPOSE_RULES.get(purpose)
        if not rules:
            return PurposeOfUseValidation(
                purpose=purpose, is_valid=False, reason="Unknown purpose of use",
            )
        return PurposeOfUseValidation(
            purpose=purpose,
            requires_consent=rules["requires_consent"],
            requires_break_glass=rules["requires_break_glass"],
        )

    def requires_consent(self, purpose: PurposeOfUse) -> bool:
        rules = self._PURPOSE_RULES.get(purpose, {})
        return rules.get("requires_consent", False)

    def requires_break_glass(self, purpose: PurposeOfUse) -> bool:
        rules = self._PURPOSE_RULES.get(purpose, {})
        return rules.get("requires_break_glass", False)
