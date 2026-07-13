"""
GULA Platform — Decision Guard
================================
Enforcement layer that wraps every autonomous action.

Usage:
    from app.core.decision_guard import guard, ActionType

    # Will raise PolicyViolation if blocked
    guard(ActionType.AUTO_REPAIR, context={"reason": "DB latency high"})

    # Non-raising variant
    from app.core.decision_guard import check
    if check(ActionType.SCALING, context={"env": "production"}):
        do_scale()

All blocks are logged and counted toward policy metrics.
"""

from __future__ import annotations

import logging

from app.core.policy_engine import ActionType, PolicyDecision, evaluate_policy

logger = logging.getLogger("gula.guard")


class PolicyViolation(Exception):
    """Raised when an autonomous action is blocked by policy."""

    def __init__(self, decision: PolicyDecision):
        self.decision = decision
        super().__init__(
            f"PolicyViolation: {decision.action.value} blocked — {decision.reason} "
            f"(risk={decision.risk.value}, env={decision.env})"
        )


def guard(action: ActionType, context: dict | None = None) -> PolicyDecision:
    """
    Enforce policy for an autonomous action.
    Raises PolicyViolation if blocked.
    Returns the PolicyDecision if allowed.
    """
    decision = evaluate_policy(action, context)
    if not decision.allowed:
        raise PolicyViolation(decision)
    return decision


def check(action: ActionType, context: dict | None = None) -> bool:
    """
    Check policy without raising. Returns True if allowed, False if blocked.
    All evaluations are still logged.
    """
    return evaluate_policy(action, context).allowed


def guard_repair(repair_name: str, context: dict | None = None) -> PolicyDecision:
    """Convenience wrapper for auto_repair actions."""
    ctx = {"reason": f"auto_repair: {repair_name}", **(context or {})}
    return guard(ActionType.AUTO_REPAIR, ctx)


def guard_ai_fix(file_path: str, context: dict | None = None) -> PolicyDecision:
    """Convenience wrapper for AI-generated code fixes."""
    ctx = {"reason": f"ai_auto_fix: {file_path}", "affects_data": False, **(context or {})}
    return guard(ActionType.AI_AUTO_FIX, ctx)


def guard_ai_commit(description: str) -> PolicyDecision:
    """Convenience wrapper for AI commits."""
    return guard(ActionType.AI_COMMIT, {"reason": description})


def guard_scaling(replicas: int) -> PolicyDecision:
    """Convenience wrapper for scaling actions."""
    return guard(ActionType.SCALING, {"reason": f"scale to {replicas} replicas"})
