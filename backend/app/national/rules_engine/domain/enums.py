"""Rule-engine enums — authoritative definition lives in Shared Core.

Backward-compatible re-export of
``shared.rules_engine.domain.enums`` (PROGRAM-STABLE-002). The national
rules engine consumes the Shared Core definitions; this module exists so
existing ``app.national.rules_engine.domain.enums`` imports keep working.
"""
from __future__ import annotations

from shared.rules_engine.domain.enums import (
    Operator,
    RuleCategory,
    RuleExecutionMode,
    RuleOutcome,
    RuleSeverity,
    RuleStatus,
    RuleTrigger,
)

__all__ = [
    "Operator",
    "RuleCategory",
    "RuleExecutionMode",
    "RuleOutcome",
    "RuleSeverity",
    "RuleStatus",
    "RuleTrigger",
]
