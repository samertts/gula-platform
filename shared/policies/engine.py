from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger("gula.policies")


@dataclass
class PolicyRule:
    name: str
    condition: Callable[[dict[str, Any]], bool]
    action: str = "allow"
    priority: int = 0


@dataclass
class Policy:
    name: str
    description: str = ""
    rules: list[PolicyRule] = field(default_factory=list)
    default_action: str = "deny"


class PolicyEngine:
    def __init__(self):
        self._policies: dict[str, Policy] = {}

    def add_policy(self, policy: Policy) -> None:
        self._policies[policy.name] = policy

    def evaluate(self, policy_name: str, context: dict[str, Any]) -> str:
        policy = self._policies.get(policy_name)
        if not policy:
            logger.warning("Unknown policy: %s", policy_name)
            return "deny"
        sorted_rules = sorted(policy.rules, key=lambda r: r.priority, reverse=True)
        for rule in sorted_rules:
            try:
                if rule.condition(context):
                    logger.debug("Policy '%s' rule '%s' matched: %s", policy_name, rule.name, rule.action)
                    return rule.action
            except Exception as exc:
                logger.warning("Policy rule '%s' evaluation failed: %s", rule.name, exc)
        return policy.default_action

    def evaluate_all(self, context: dict[str, Any]) -> dict[str, str]:
        return {name: self.evaluate(name, context) for name in self._policies}
