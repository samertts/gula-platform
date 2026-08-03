"""Rule-engine entities — authoritative definition lives in Shared Core.

Backward-compatible re-export of
``shared.rules_engine.domain.entities`` (PROGRAM-STABLE-002). The national
rules engine consumes the Shared Core definitions; this module exists so
existing ``app.national.rules_engine.domain.entities`` imports keep working.
"""
from __future__ import annotations

from shared.rules_engine.domain.entities import (
    RuleAction,
    RuleCondition,
    RuleDefinition,
    RuleEvaluationContext,
    RuleEvaluationResult,
    RuleSet,
)

__all__ = [
    "RuleAction",
    "RuleCondition",
    "RuleDefinition",
    "RuleEvaluationContext",
    "RuleEvaluationResult",
    "RuleSet",
]
