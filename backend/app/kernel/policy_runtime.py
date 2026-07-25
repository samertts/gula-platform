from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

from app._compat import StrEnum
from app.core.policy_engine import (
    ActionType as CoreActionType,
)
from app.core.policy_engine import (
    evaluate_policy as core_evaluate_policy,
)
from app.core.policy_engine import (
    policy_engine as core_policy_engine,
)

logger = logging.getLogger("gula.kernel.policy_runtime")


class PolicyDecisionValue(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass
class PolicyContext:
    action: str = ""
    resource_type: str = ""
    resource_id: str = ""
    user_id: str = ""
    tenant_id: str = ""
    environment: str = ""
    action_details: dict[str, Any] = field(default_factory=dict)
    request_id: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class PolicyMatch:
    policy_name: str
    policy_version: str = "1.0.0"
    rule: str = ""
    decision: PolicyDecisionValue = PolicyDecisionValue.DENY
    reason: str = ""
    risk: str = "medium"
    severity: str = "info"


@dataclass
class PolicyResult:
    decision: PolicyDecisionValue
    allowed: bool = False
    matches: list[PolicyMatch] = field(default_factory=list)
    matched_policies: list[str] = field(default_factory=list)
    explanation: str = ""
    risk_level: str = "low"
    requires_approval: bool = False
    execution_time_ms: float = 0.0
    context: dict[str, Any] = field(default_factory=dict)

    @property
    def is_allowed(self) -> bool:
        return self.allowed


class PolicyRuntime:
    def __init__(self):
        self._evaluation_count: int = 0
        self._custom_policies: dict[str, dict[str, Any]] = {}

    def evaluate(
        self,
        context: PolicyContext,
        policies: list[str] | None = None,
    ) -> PolicyResult:
        start = time.monotonic()
        self._evaluation_count += 1
        env = context.environment or os.getenv("ENV", "production")

        matched_policies: list[str] = []
        matches: list[PolicyMatch] = []

        core_action = self._map_to_core_action(context.action)
        if core_action:
            core_decision = core_evaluate_policy(
                core_action,
                context={
                    "env": env,
                    "reason": context.action_details.get("reason", "runtime evaluation"),
                    **context.action_details,
                },
            )
            decision_value = (
                PolicyDecisionValue.ALLOW if core_decision.allowed else PolicyDecisionValue.DENY
            )
            match = PolicyMatch(
                policy_name="core_policy_engine",
                policy_version="2.1.0",
                rule=core_action.value if hasattr(core_action, "value") else str(core_action),
                decision=decision_value,
                reason=core_decision.reason,
                risk=core_decision.risk.value
                if hasattr(core_decision.risk, "value")
                else str(core_decision.risk),
            )
            matches.append(match)
            matched_policies.append("core_policy_engine")

        if policies:
            for policy_name in policies:
                policy_def = self._custom_policies.get(policy_name)
                if not policy_def:
                    continue
                result = self._evaluate_custom_policy(policy_name, policy_def, context)
                matches.extend(result["matches"])
                matched_policies.append(policy_name)

        allowed = all(m.decision == PolicyDecisionValue.ALLOW for m in matches)
        requires_approval = any(m.decision == PolicyDecisionValue.REQUIRE_APPROVAL for m in matches)

        if not matches:
            allowed = False

        explanation = "; ".join(f"{m.policy_name}: {m.reason}" for m in matches)
        risk_levels = [m.risk for m in matches if m.decision != PolicyDecisionValue.ALLOW]
        risk_level = max(risk_levels) if risk_levels else "low"

        if allowed and requires_approval:
            decision = PolicyDecisionValue.REQUIRE_APPROVAL
        elif allowed:
            decision = PolicyDecisionValue.ALLOW
        else:
            decision = PolicyDecisionValue.DENY

        duration_ms = (time.monotonic() - start) * 1000
        return PolicyResult(
            decision=decision,
            allowed=allowed and not requires_approval,
            matches=matches,
            matched_policies=matched_policies,
            explanation=explanation,
            risk_level=risk_level,
            requires_approval=requires_approval,
            execution_time_ms=duration_ms,
            context={"action": context.action, "environment": env},
        )

    def register_policy(self, name: str, policy_def: dict[str, Any]) -> None:
        self._custom_policies[name] = policy_def
        logger.info("Custom policy registered", extra={"policy": name})

    def _evaluate_custom_policy(
        self,
        name: str,
        policy_def: dict[str, Any],
        context: PolicyContext,
    ) -> dict[str, Any]:
        matches: list[PolicyMatch] = []
        rules = policy_def.get("rules", [])

        for rule in rules:
            condition = rule.get("condition", {})
            field = condition.get("field", "")
            expected = condition.get("value")
            field_value = getattr(context, field, None) or context.action_details.get(field)
            match_result = field_value == expected if expected is not None else True

            if match_result:
                decision_str = rule.get("decision", "deny")
                decision = (
                    PolicyDecisionValue(decision_str)
                    if decision_str in ("allow", "deny", "require_approval")
                    else PolicyDecisionValue.DENY
                )
                match = PolicyMatch(
                    policy_name=name,
                    rule=rule.get("name", "unnamed"),
                    decision=decision,
                    reason=rule.get("reason", "custom policy rule matched"),
                    risk=rule.get("risk", "medium"),
                )
                matches.append(match)

        return {"matches": matches}

    def _map_to_core_action(self, action: str) -> CoreActionType | None:
        mapping = {
            "code_change": CoreActionType.CODE_CHANGE,
            "config_change": CoreActionType.CONFIG_CHANGE,
            "deploy": CoreActionType.DEPLOY,
            "db_schema": CoreActionType.DB_SCHEMA,
            "db_write": CoreActionType.DB_WRITE,
            "db_pool_recycle": CoreActionType.DB_POOL_RECYCLE,
            "auto_repair": CoreActionType.AUTO_REPAIR,
            "scaling": CoreActionType.SCALING,
            "circuit_reset": CoreActionType.CIRCUIT_RESET,
            "cache_flush": CoreActionType.CACHE_FLUSH,
            "queue_purge": CoreActionType.QUEUE_PURGE,
            "ai_auto_fix": CoreActionType.AI_AUTO_FIX,
            "ai_commit": CoreActionType.AI_COMMIT,
            "ai_decision": CoreActionType.AI_DECISION,
            "secret_rotation": CoreActionType.SECRET_ROTATION,
            "audit_delete": CoreActionType.AUDIT_DELETE,
        }
        mapped = mapping.get(action)
        if not mapped:
            for member in CoreActionType:
                if member.value == action:
                    return member
        return mapped

    def get_stats(self) -> dict[str, Any]:
        core_stats = core_policy_engine.stats() if core_policy_engine else {}
        return {
            "evaluation_count": self._evaluation_count,
            "custom_policies": len(self._custom_policies),
            "core_engine": core_stats,
        }
