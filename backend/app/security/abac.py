from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("gula.security.abac")


class Effect(Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass
class AttributeCondition:
    attribute: str = ""
    operator: str = "equals"
    value: Any = None

    def evaluate(self, context: dict[str, Any]) -> bool:
        actual = context.get(self.attribute)
        if actual is None:
            return False

        if self.operator == "equals":
            return actual == self.value
        if self.operator == "not_equals":
            return actual != self.value
        if self.operator == "in":
            return actual in (self.value or [])
        if self.operator == "not_in":
            return actual not in (self.value or [])
        if self.operator == "greater_than":
            return actual > self.value
        if self.operator == "less_than":
            return actual < self.value
        if self.operator == "contains":
            return self.value in actual if isinstance(actual, str) else False
        if self.operator == "matches":
            return bool(re.match(str(self.value), str(actual)))
        return False


@dataclass
class ABACRule:
    id: str = ""
    name: str = ""
    description: str = ""
    effect: Effect = Effect.DENY
    resource: str = ""
    action: str = ""
    conditions: list[AttributeCondition] = field(default_factory=list)
    priority: int = 100
    is_active: bool = True

    def evaluate(self, context: dict[str, Any]) -> bool:
        if not self.conditions:
            return True
        return all(c.evaluate(context) for c in self.conditions)


class ABACEngine:
    def __init__(self):
        self._rules: list[ABACRule] = []
        self._rule_index: dict[str, list[ABACRule]] = {}

    def add_rule(self, rule: ABACRule) -> None:
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority)
        key = f"{rule.resource}:{rule.action}"
        self._rule_index.setdefault(key, []).append(rule)
        self._rule_index[key].sort(key=lambda r: r.priority)
        logger.debug("ABAC rule added: %s [%s/%s]", rule.name, rule.resource, rule.action)

    def remove_rule(self, rule_id: str) -> bool:
        for i, rule in enumerate(self._rules):
            if rule.id == rule_id:
                self._rules.pop(i)
                key = f"{rule.resource}:{rule.action}"
                if key in self._rule_index:
                    self._rule_index[key] = [r for r in self._rule_index[key] if r.id != rule_id]
                return True
        return False

    def check(
        self,
        resource: str,
        action: str,
        subject: dict[str, Any] | None = None,
        resource_attrs: dict[str, Any] | None = None,
        environment: dict[str, Any] | None = None,
    ) -> Effect:
        context = {}
        if subject:
            context.update({f"user.{k}": v for k, v in subject.items()})
        if resource_attrs:
            context.update({f"resource.{k}": v for k, v in resource_attrs.items()})
        if environment:
            context.update({f"env.{k}": v for k, v in environment.items()})

        key = f"{resource}:{action}"
        rules = self._rule_index.get(key, [])

        if not rules:
            rules = [r for r in self._rules if r.resource == "*" or r.resource == resource]

        for rule in rules:
            if not rule.is_active:
                continue
            if rule.action != "*" and rule.action != action:
                continue
            if rule.evaluate(context):
                logger.debug(
                    "ABAC %s: %s on %s/%s (rule: %s)",
                    rule.effect.value.upper(),
                    action,
                    resource,
                    context,
                    rule.name,
                )
                return rule.effect

        return Effect.DENY

    def can_access(
        self,
        resource: str,
        action: str,
        subject: dict[str, Any] | None = None,
        resource_attrs: dict[str, Any] | None = None,
        environment: dict[str, Any] | None = None,
    ) -> bool:
        return self.check(resource, action, subject, resource_attrs, environment) == Effect.ALLOW

    def list_rules(self, resource: str | None = None) -> list[ABACRule]:
        if resource:
            return [r for r in self._rules if r.resource == resource]
        return list(self._rules)

    def count(self) -> int:
        return len(self._rules)
