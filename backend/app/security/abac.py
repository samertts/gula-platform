"""Attribute-based access control (ABAC) policy engine.

The engine is the canonical authorization foundation for the platform:

* **Fail-closed** — if no active rule matches, access is denied.
* **Explicit attributes** — decisions are computed from subject, resource and
  environment attributes only; never from ambient state.
* **Deterministic** — rules are evaluated in a stable order (priority
  ascending, then rule ``id``), so equal-priority rules cannot race.
* **Purpose-of-use dimension** — rules may be bound to one or more purposes;
  a purpose-bound rule never matches an unauthorized purpose.
* **Auditable decisions** — every ``decide`` result is recorded with the
  deciding rule and reason, and may be streamed to an audit hook.
* **No client-chosen actor** — the auditable ``ABACRequest`` API requires a
  server-derived ``subject_id``; use ``subject_from_principal`` to build a
  subject map from the authenticated principal.

The engine is attribute-based by design and is *not* a thin RBAC wrapper:
roles are one attribute among many (org, facility, department, purpose, ...).
"""

from __future__ import annotations

import logging
import re
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
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
    purposes: list[str] = field(default_factory=list)

    def evaluate(self, context: dict[str, Any]) -> bool:
        if not self.conditions:
            return True
        return all(c.evaluate(context) for c in self.conditions)


@dataclass
class ABACRequest:
    """A single access decision request.

    The ``subject`` attribute map MUST be derived from a server-verified
    principal (see ``subject_from_principal``) and MUST carry a non-empty
    ``subject_id``. Client-supplied subject attributes are never accepted.
    """

    resource: str
    action: str
    subject: dict[str, Any] | None = None
    resource_attrs: dict[str, Any] | None = None
    environment: dict[str, Any] | None = None
    purpose: str | None = None

    def __post_init__(self) -> None:
        if not self.resource:
            raise ValueError("ABACRequest.resource must be a non-empty string")
        if not self.action:
            raise ValueError("ABACRequest.action must be a non-empty string")
        if self.subject is not None:
            if not isinstance(self.subject, dict):
                raise ValueError("ABACRequest.subject must be a dict or None")
            if not self.subject.get("subject_id"):
                raise ValueError(
                    "ABACRequest.subject must carry a server-derived 'subject_id'; "
                    "subject attributes must come from the authenticated principal"
                )


@dataclass
class ABACDecision:
    """Auditable outcome of an ABAC access decision."""

    allowed: bool
    effect: Effect
    resource: str
    action: str
    purpose: str | None
    subject_id: str | None
    rule_id: str | None
    rule_name: str | None
    reason: str
    matched: dict[str, Any] = field(default_factory=dict)
    decided_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


def _rule_order(rule: ABACRule) -> tuple[int, str]:
    return rule.priority, rule.id or ""


class ABACEngine:
    """Attribute-based access control engine.

    Decision semantics:

    * Rules are evaluated in deterministic order (priority ascending, then
      rule ``id``); the first matching active rule decides.
    * An explicit DENY rule therefore overrides a lower-priority ALLOW rule
      (deny-overrides), and ALLOW rules never match outside their declared
      resource/action scope.
    * A rule carrying ``purposes`` only matches requests whose ``purpose`` is
      one of those purposes; empty ``purposes`` matches any purpose.
    * If no rule matches, access is DENIED (fail-closed).
    """

    def __init__(
        self,
        *,
        decision_log_maxlen: int = 1000,
        on_decision: Callable[[ABACDecision], None] | None = None,
    ) -> None:
        if decision_log_maxlen < 1:
            raise ValueError("decision_log_maxlen must be >= 1")
        self._rules: list[ABACRule] = []
        self._decision_log: deque[ABACDecision] = deque(maxlen=decision_log_maxlen)
        self._on_decision = on_decision

    def add_rule(self, rule: ABACRule) -> None:
        self._rules.append(rule)
        self._rules.sort(key=_rule_order)
        logger.debug("ABAC rule added: %s [%s/%s]", rule.name, rule.resource, rule.action)

    def remove_rule(self, rule_id: str) -> bool:
        for i, rule in enumerate(self._rules):
            if rule.id == rule_id:
                self._rules.pop(i)
                return True
        return False

    def check(
        self,
        resource: str,
        action: str,
        subject: dict[str, Any] | None = None,
        resource_attrs: dict[str, Any] | None = None,
        environment: dict[str, Any] | None = None,
        purpose: str | None = None,
    ) -> Effect:
        """Return the decision effect for a request without recording it.

        Backward-compatible with the original engine API. For an auditable
        decision record, use ``decide`` with an ``ABACRequest`` instead.
        """
        context = self._build_context(subject, resource_attrs, environment)
        for rule in self._matching_rules(resource, action):
            if not self._purpose_matches(rule, purpose):
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
        purpose: str | None = None,
    ) -> bool:
        return (
            self.check(resource, action, subject, resource_attrs, environment, purpose)
            == Effect.ALLOW
        )

    def decide(self, request: ABACRequest) -> ABACDecision:
        """Evaluate an ``ABACRequest`` and record an auditable decision."""
        context = self._build_context(request.subject, request.resource_attrs, request.environment)
        for rule in self._matching_rules(request.resource, request.action):
            if not self._purpose_matches(rule, request.purpose):
                continue
            if rule.evaluate(context):
                return self._record(
                    ABACDecision(
                        allowed=rule.effect is Effect.ALLOW,
                        effect=rule.effect,
                        resource=request.resource,
                        action=request.action,
                        purpose=request.purpose,
                        subject_id=(request.subject or {}).get("subject_id"),
                        rule_id=rule.id or None,
                        rule_name=rule.name or None,
                        reason=f"{rule.effect.value.upper()} matched rule '{rule.name or rule.id}'",
                        matched={c.attribute: context.get(c.attribute) for c in rule.conditions},
                    )
                )
        return self._record(
            ABACDecision(
                allowed=False,
                effect=Effect.DENY,
                resource=request.resource,
                action=request.action,
                purpose=request.purpose,
                subject_id=(request.subject or {}).get("subject_id"),
                rule_id=None,
                rule_name=None,
                reason="no matching rule; denied by default (fail-closed)",
                matched={},
            )
        )

    def recent_decisions(self, limit: int = 100) -> list[ABACDecision]:
        """Return the most recent recorded decisions, oldest first."""
        return list(self._decision_log)[-limit:]

    def clear_decisions(self) -> None:
        self._decision_log.clear()

    def list_rules(self, resource: str | None = None) -> list[ABACRule]:
        if resource:
            return [r for r in self._rules if r.resource == resource]
        return list(self._rules)

    def count(self) -> int:
        return len(self._rules)

    @staticmethod
    def _build_context(
        subject: dict[str, Any] | None,
        resource_attrs: dict[str, Any] | None,
        environment: dict[str, Any] | None,
    ) -> dict[str, Any]:
        context: dict[str, Any] = {}
        if subject:
            context.update({f"user.{k}": v for k, v in subject.items()})
        if resource_attrs:
            context.update({f"resource.{k}": v for k, v in resource_attrs.items()})
        if environment:
            context.update({f"env.{k}": v for k, v in environment.items()})
        return context

    @staticmethod
    def _purpose_matches(rule: ABACRule, purpose: str | None) -> bool:
        return not rule.purposes or (purpose is not None and purpose in rule.purposes)

    def _matching_rules(self, resource: str, action: str) -> list[ABACRule]:
        return sorted(
            (
                rule
                for rule in self._rules
                if rule.is_active
                and (rule.resource == "*" or rule.resource == resource)
                and (rule.action == "*" or rule.action == action)
            ),
            key=_rule_order,
        )

    def _record(self, decision: ABACDecision) -> ABACDecision:
        self._decision_log.append(decision)
        if self._on_decision is not None:
            self._on_decision(decision)
        return decision


def subject_from_principal(
    principal: Any,
    *,
    roles: list[str] | None = None,
) -> dict[str, Any]:
    """Build a trusted ABAC subject attribute map from an authenticated principal.

    Attributes are always derived from the server-side token-verified principal
    — never from a client payload. ``subject_id`` is guaranteed to be present so
    the result can be passed directly to ``ABACRequest.subject``.
    """
    if hasattr(principal, "uuid") and hasattr(principal, "identity_id"):
        subject: dict[str, Any] = {
            "subject_id": principal.uuid,
            "identity_id": principal.identity_id,
            "account_type": getattr(principal, "account_type", None),
            "status": getattr(principal, "status", None),
        }
    elif hasattr(principal, "id") and hasattr(principal, "lab_id"):
        subject = {
            "subject_id": f"lab-user:{principal.id}",
            "lab_id": principal.lab_id,
            "role": getattr(principal, "role", None),
        }
        if getattr(principal, "province_id", None) is not None:
            subject["province_id"] = principal.province_id
    else:
        raise TypeError(f"unsupported principal type: {type(principal).__name__}")
    if roles:
        subject["roles"] = [str(role) for role in roles]
    return subject
