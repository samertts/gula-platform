"""Shared rule-engine domain types (PROGRAM-STABLE-002 Shared Core).

The rule engine is a platform-wide, domain-agnostic capability. Its domain
types (enums + entities) live in Shared Core so that the platform kernel
(app.kernel.rules_runtime) and the national rules engine both consume the
same authoritative definitions without a kernel -> domain dependency.

The canonical engine implementation (``ExpressionEngine``) lives here too
(PROGRAM-01 ADR-035 promotion): ``shared.rules_engine.engine`` is the single
authoritative ``evaluate_rule`` in the platform.
"""

from shared.rules_engine.engine import EvaluationResult, ExpressionEngine

__all__ = ["EvaluationResult", "ExpressionEngine"]
