from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, Field

from security.modules.identity.models import AccessDecision, RiskLevel

logger = logging.getLogger("gula.security.modules.identity.abac")


class Effect(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


class CombinationAlgorithm(str, Enum):
    DENY_OVERRIDES = "deny_overrides"
    PERMIT_OVERRIDES = "permit_overrides"
    FIRST_APPLICABLE = "first_applicable"


class ConditionOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    MATCHES = "matches"
    AND = "and"
    OR = "or"
    NOT = "not"


class PolicyCondition(BaseModel):
    operator: ConditionOperator
    attribute: str = ""
    value: Any = None
    conditions: list[PolicyCondition] = Field(default_factory=list)


class Obligation(BaseModel):
    id: str = ""
    type: str = ""
    action: str = ""
    params: dict[str, Any] = Field(default_factory=dict)


class Policy(BaseModel):
    id: str = ""
    name: str = ""
    description: str = ""
    effect: Effect = Effect.DENY
    resource: str = ""
    action: str = ""
    subject_conditions: list[PolicyCondition] = Field(default_factory=list)
    resource_conditions: list[PolicyCondition] = Field(default_factory=list)
    environment_conditions: list[PolicyCondition] = Field(default_factory=list)
    action_conditions: list[PolicyCondition] = Field(default_factory=list)
    purpose_of_use: list[str] = Field(default_factory=list)
    obligations: list[Obligation] = Field(default_factory=list)
    priority: int = 100
    is_active: bool = True


class ABACEngine:
    def __init__(self, combination_algorithm: CombinationAlgorithm = CombinationAlgorithm.DENY_OVERRIDES):
        self._policies: list[Policy] = []
        self._policy_index: dict[str, list[Policy]] = {}
        self._cache: dict[str, tuple[AccessDecision, float]] = {}
        self._cache_ttl: int = 60
        self._cache_lock = threading.Lock()
        self._lock = threading.Lock()
        self._combination_algorithm = combination_algorithm
        self._backend_engine: Any = None

        try:
            from backend.app.security.abac import ABACEngine as BackendABAC
            self._backend_engine = BackendABAC()
        except ImportError:
            pass

    def set_combination_algorithm(self, algorithm: CombinationAlgorithm) -> None:
        self._combination_algorithm = algorithm

    def add_policy(self, policy: Policy) -> None:
        with self._lock:
            self._policies.append(policy)
            self._policies.sort(key=lambda p: p.priority)
            key = f"{policy.resource}:{policy.action}"
            self._policy_index.setdefault(key, []).append(policy)
            self._policy_index[key].sort(key=lambda p: p.priority)

        if self._backend_engine is not None:
            try:
                from backend.app.security.abac import ABACRule, AttributeCondition

                rule = ABACRule(
                    id=policy.id,
                    name=policy.name,
                    description=policy.description,
                    effect=getattr(__import__("backend.app.security.abac", fromlist=["Effect"]), "Effect").ALLOW
                    if policy.effect == Effect.ALLOW
                    else getattr(__import__("backend.app.security.abac", fromlist=["Effect"]), "Effect").DENY,
                    resource=policy.resource,
                    action=policy.action,
                    priority=policy.priority,
                    is_active=policy.is_active,
                )
                self._backend_engine.add_rule(rule)
            except Exception:
                pass

        self._clear_cache()
        logger.debug("ABAC policy added: %s [%s/%s]", policy.name, policy.resource, policy.action)

    def remove_policy(self, policy_id: str) -> bool:
        with self._lock:
            for i, policy in enumerate(self._policies):
                if policy.id == policy_id:
                    self._policies.pop(i)
                    key = f"{policy.resource}:{policy.action}"
                    if key in self._policy_index:
                        self._policy_index[key] = [p for p in self._policy_index[key] if p.id != policy_id]
                    self._clear_cache()
                    if self._backend_engine is not None:
                        try:
                            self._backend_engine.remove_rule(policy_id)
                        except Exception:
                            pass
                    return True
        return False

    def _evaluate_condition(self, condition: PolicyCondition, context: dict[str, Any]) -> bool:
        if condition.operator == ConditionOperator.AND:
            return all(self._evaluate_condition(c, context) for c in condition.conditions)
        if condition.operator == ConditionOperator.OR:
            return any(self._evaluate_condition(c, context) for c in condition.conditions)
        if condition.operator == ConditionOperator.NOT:
            return not any(self._evaluate_condition(c, context) for c in condition.conditions)

        actual = context.get(condition.attribute)
        if actual is None:
            return condition.operator == ConditionOperator.NOT_EQUALS

        if condition.operator == ConditionOperator.EQUALS:
            return actual == condition.value
        if condition.operator == ConditionOperator.NOT_EQUALS:
            return actual != condition.value
        if condition.operator == ConditionOperator.IN:
            return actual in (condition.value if isinstance(condition.value, list) else [condition.value])
        if condition.operator == ConditionOperator.NOT_IN:
            return actual not in (condition.value if isinstance(condition.value, list) else [condition.value])
        if condition.operator == ConditionOperator.GREATER_THAN:
            try:
                return float(actual) > float(condition.value)
            except (TypeError, ValueError):
                return False
        if condition.operator == ConditionOperator.LESS_THAN:
            try:
                return float(actual) < float(condition.value)
            except (TypeError, ValueError):
                return False
        if condition.operator == ConditionOperator.CONTAINS:
            if isinstance(actual, str) and isinstance(condition.value, str):
                return condition.value in actual
            if isinstance(actual, list):
                return condition.value in actual
            return False
        if condition.operator == ConditionOperator.MATCHES:
            import re
            try:
                return bool(re.match(str(condition.value), str(actual)))
            except re.error:
                return False
        return False

    def _evaluate_policy(self, policy: Policy, context: dict[str, Any]) -> bool:
        if not policy.is_active:
            return False

        subject_ok = all(self._evaluate_condition(c, context) for c in policy.subject_conditions) if policy.subject_conditions else True
        resource_ok = all(self._evaluate_condition(c, context) for c in policy.resource_conditions) if policy.resource_conditions else True
        env_ok = all(self._evaluate_condition(c, context) for c in policy.environment_conditions) if policy.environment_conditions else True
        action_ok = all(self._evaluate_condition(c, context) for c in policy.action_conditions) if policy.action_conditions else True

        purpose = context.get("purpose_of_use", "")
        purpose_ok = True
        if policy.purpose_of_use and purpose:
            purpose_ok = purpose in policy.purpose_of_use

        return subject_ok and resource_ok and env_ok and action_ok and purpose_ok

    def _build_cache_key(
        self,
        resource: str,
        action: str,
        subject: dict[str, Any] | None,
        resource_attrs: dict[str, Any] | None,
        environment: dict[str, Any] | None,
    ) -> str:
        raw = json.dumps({
            "resource": resource,
            "action": action,
            "subject": subject or {},
            "resource_attrs": resource_attrs or {},
            "environment": environment or {},
        }, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def _clear_cache(self) -> None:
        with self._cache_lock:
            self._cache.clear()

    def evaluate(
        self,
        resource: str,
        action: str,
        subject: dict[str, Any] | None = None,
        resource_attrs: dict[str, Any] | None = None,
        environment: dict[str, Any] | None = None,
    ) -> AccessDecision:
        if self._backend_engine is not None:
            try:
                backend_effect = self._backend_engine.check(
                    resource=resource,
                    action=action,
                    subject=subject,
                    resource_attrs=resource_attrs,
                    environment=environment,
                )
                from backend.app.security.abac import Effect as BackendEffect
                if backend_effect == BackendEffect.DENY:
                    return AccessDecision(
                        permitted=False,
                        reason=f"Backend ABAC denied access to {resource}:{action}",
                    )
            except Exception:
                pass

        cache_key = self._build_cache_key(resource, action, subject, resource_attrs, environment)
        with self._cache_lock:
            cached = self._cache.get(cache_key)
            if cached is not None:
                decision, expiry = cached
                if time.monotonic() < expiry:
                    return decision

        context = {}
        if subject:
            context.update({f"subject.{k}": v for k, v in subject.items()})
        if resource_attrs:
            context.update({f"resource.{k}": v for k, v in resource_attrs.items()})
        if environment:
            context.update({f"env.{k}": v for k, v in environment.items()})
        context.update({
            "resource": resource,
            "action": action,
        })

        key = f"{resource}:{action}"
        policies = self._policy_index.get(key, [])
        if not policies:
            policies = [p for p in self._policies if p.resource == "*" or p.resource == resource]

        matching_policies: list[tuple[Policy, bool]] = []
        for policy in policies:
            if policy.action != "*" and policy.action != action:
                continue
            match = self._evaluate_policy(policy, context)
            if match:
                matching_policies.append((policy, match))
            elif self._combination_algorithm == CombinationAlgorithm.FIRST_APPLICABLE:
                break

        if not matching_policies:
            decision = AccessDecision(
                permitted=False,
                reason=f"No matching ABAC policy for {resource}:{action}",
            )
        elif self._combination_algorithm == CombinationAlgorithm.DENY_OVERRIDES:
            denied = any(p.effect == Effect.DENY for p, _ in matching_policies)
            if denied:
                deny_policies = [p for p, _ in matching_policies if p.effect == Effect.DENY]
                decision = AccessDecision(
                    permitted=False,
                    reason=f"Denied by policy: {deny_policies[0].name}",
                    obligations=[o.id for p in deny_policies for o in p.obligations],
                )
            else:
                allow_policy = matching_policies[0][0]
                decision = AccessDecision(
                    permitted=True,
                    reason=f"Allowed by policy: {allow_policy.name}",
                    obligations=[o.id for o in allow_policy.obligations],
                )
        elif self._combination_algorithm == CombinationAlgorithm.PERMIT_OVERRIDES:
            allowed = any(p.effect == Effect.ALLOW for p, _ in matching_policies)
            if allowed:
                allow_policies = [p for p, _ in matching_policies if p.effect == Effect.ALLOW]
                decision = AccessDecision(
                    permitted=True,
                    reason=f"Allowed by policy: {allow_policies[0].name}",
                    obligations=[o.id for p in allow_policies for o in p.obligations],
                )
            else:
                decision = AccessDecision(
                    permitted=False,
                    reason="No allow policy matched",
                )
        else:
            first = matching_policies[0][0]
            decision = AccessDecision(
                permitted=first.effect == Effect.ALLOW,
                reason=f"{'Allowed' if first.effect == Effect.ALLOW else 'Denied'} by first-applicable policy: {first.name}",
                obligations=[o.id for o in first.obligations],
            )

        with self._cache_lock:
            self._cache[cache_key] = (decision, time.monotonic() + self._cache_ttl)

        logger.debug(
            "ABAC decision: %s for %s/%s (algorithm=%s)",
            "ALLOW" if decision.permitted else "DENY",
            action, resource,
            self._combination_algorithm.value,
        )
        return decision

    def set_cache_ttl(self, ttl_seconds: int) -> None:
        self._cache_ttl = ttl_seconds

    def list_policies(self, resource: str | None = None) -> list[Policy]:
        if resource:
            return [p for p in self._policies if p.resource == resource]
        return list(self._policies)

    def enable_policy(self, policy_id: str) -> bool:
        for policy in self._policies:
            if policy.id == policy_id:
                policy.is_active = True
                self._clear_cache()
                return True
        return False

    def disable_policy(self, policy_id: str) -> bool:
        for policy in self._policies:
            if policy.id == policy_id:
                policy.is_active = False
                self._clear_cache()
                return True
        return False

    def get_obligations(
        self,
        resource: str,
        action: str,
        subject: dict[str, Any] | None = None,
        resource_attrs: dict[str, Any] | None = None,
        environment: dict[str, Any] | None = None,
    ) -> list[Obligation]:
        decision = self.evaluate(resource, action, subject, resource_attrs, environment)
        return decision.obligations
