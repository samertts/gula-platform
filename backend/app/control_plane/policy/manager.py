from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC, StrEnum
from app.core.policy_engine import ActionType
from app.core.policy_engine import evaluate_policy as core_evaluate_policy

logger = logging.getLogger("gula.control_plane.policy.manager")


class PolicyDomain(StrEnum):
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    CLINICAL = "clinical"
    PRIVACY = "privacy"
    DATA = "data"
    AI = "ai"
    COMPLIANCE = "compliance"
    RELEASE = "release"


class PolicySeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class PolicyEffect(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"
    AUDIT = "audit"


@dataclass
class Policy:
    name: str
    domain: PolicyDomain
    description: str = ""
    effect: PolicyEffect = PolicyEffect.DENY
    severity: PolicySeverity = PolicySeverity.MEDIUM
    conditions: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class PolicyManager:
    def __init__(self):
        self._policies: dict[str, Policy] = {}

    def register(self, policy: Policy) -> None:
        self._policies[policy.name] = policy
        logger.info("Policy registered: %s [%s]", policy.name, policy.domain.value)

    def unregister(self, name: str) -> None:
        self._policies.pop(name, None)

    def get(self, name: str) -> Policy | None:
        return self._policies.get(name)

    def list(self, domain: PolicyDomain | None = None) -> list[Policy]:
        if domain:
            return [p for p in self._policies.values() if p.domain == domain]
        return list(self._policies.values())

    def enable(self, name: str) -> None:
        policy = self._policies.get(name)
        if policy:
            policy.enabled = True

    def disable(self, name: str) -> None:
        policy = self._policies.get(name)
        if policy:
            policy.enabled = False

    def evaluate(self, action: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        matching = [p for p in self._policies.values() if p.enabled]
        results: list[dict[str, Any]] = []
        final_effect = PolicyEffect.ALLOW

        for policy in matching:
            violation = self._check_policy(policy, action, context or {})
            if violation:
                results.append(violation)
                if policy.effect == PolicyEffect.DENY:
                    final_effect = PolicyEffect.DENY
                elif policy.effect == PolicyEffect.WARN and final_effect != PolicyEffect.DENY:
                    final_effect = PolicyEffect.WARN

        try:
            core_action = ActionType(action)
        except ValueError:
            core_action = ActionType.CONFIG_CHANGE
        core_result = core_evaluate_policy(
            action=core_action,
            context=context or {},
        )

        return {
            "action": action,
            "effect": final_effect.value,
            "allowed": final_effect == PolicyEffect.ALLOW,
            "core_policy": core_result.to_dict() if hasattr(core_result, "to_dict") else str(core_result),
            "violations": results,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _check_policy(self, policy: Policy, action: str, context: dict[str, Any]) -> dict[str, Any] | None:
        conditions = policy.conditions
        for key, expected in conditions.items():
            actual = context.get(key)
            if actual is not None and actual != expected:
                return {
                    "policy": policy.name,
                    "domain": policy.domain.value,
                    "severity": policy.severity.value,
                    "reason": f"Condition '{key}' expected '{expected}', got '{actual}'",
                    "effect": policy.effect.value,
                }
        return None

    def evaluate_bulk(self, evaluations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.evaluate(e.get("action", ""), e.get("context")) for e in evaluations]
