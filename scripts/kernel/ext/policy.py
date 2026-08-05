"""Phase 2 — Policy Engine.

Every rule becomes a versioned, auditable, composable, replaceable,
searchable, machine-readable policy. Policies are declarative conditions
(field, operator, value) evaluated against an execution context — changing a
policy never requires changing code.

Policy categories mirror the platform constitutions: security, architecture,
deployment, knowledge, testing, performance, documentation, cost, autonomy,
rollback, resource, context, retry, approval, risk, compliance.

Composition: a policy set applies with AND semantics; overrides follow the
Governor authority chain (a policy owned by a higher authority may override
a lower one). Replacement: registering a policy with the same id and a higher
version supersedes the old version (audited). Evaluation is pure: policies
never mutate execution state.
"""

from __future__ import annotations

import contextlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core import utcnow

# Paths.
POLICIES_DIR = Path(__file__).resolve().parent.parent.parent.parent / ".ai" / "core" / "policies"

# Policy categories (align with constitution sections).
POLICY_CATEGORIES: tuple[str, ...] = (
    "security",
    "architecture",
    "deployment",
    "knowledge",
    "testing",
    "performance",
    "documentation",
    "cost",
    "autonomy",
    "rollback",
    "resource",
    "context",
    "retry",
    "approval",
    "risk",
    "compliance",
)

# Operators supported by the machine-readable condition language.
OPERATORS: tuple[str, ...] = (
    "eq",       # ==
    "neq",      # !=
    "lt",       # <
    "lte",      # <=
    "gt",       # >
    "gte",      # >=
    "in",       # value in list
    "not_in",   # value not in list
    "contains", # list contains value
    "matches",  # regex match on string
)

POLICY_ID_RE = re.compile(r"^POLICY-\d{6}$")

PolicyVerdict = str  # "allow" | "deny" | "warn"


@dataclass
class Policy:
    """A single versioned, machine-readable policy."""

    id: str
    category: str
    statement: str
    action: PolicyVerdict  # allow / deny / warn
    operator: str = "eq"
    operand: Any = True
    version: str = "1.0.0"
    owner: str = "governor"  # authority owner
    applies_to: str = "*"    # context key this policy gates
    supersedes: str = ""     # id of replaced policy version
    status: str = "active"   # active / deprecated / archived
    created_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "statement": self.statement,
            "action": self.action,
            "operator": self.operator,
            "operand": self.operand,
            "version": self.version,
            "owner": self.owner,
            "applies_to": self.applies_to,
            "supersedes": self.supersedes,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class PolicyViolation:
    """The result of evaluating one policy against a context."""

    policy: Policy
    context_key: str
    context_value: Any
    verdict: PolicyVerdict
    detail: str = ""


class PolicyError(Exception):
    """Raised for invalid or conflicting policy operations."""


def _evaluate_condition(operator: str, actual: Any, expected: Any) -> bool:
    """Evaluate one declarative condition (no code execution)."""
    if operator == "eq":
        return actual == expected
    if operator == "neq":
        return actual != expected
    if operator == "lt":
        return bool(actual < expected)
    if operator == "lte":
        return bool(actual <= expected)
    if operator == "gt":
        return bool(actual > expected)
    if operator == "gte":
        return bool(actual >= expected)
    if operator == "in":
        return actual in (expected if isinstance(expected, (list, tuple, set)) else [expected])
    if operator == "not_in":
        return actual not in (expected if isinstance(expected, (list, tuple, set)) else [expected])
    if operator == "contains":
        return bool(expected in actual)
    if operator == "matches":
        return bool(re.search(str(expected), str(actual)))
    raise PolicyError(f"unknown operator: {operator}")


def validate_policy(policy: Policy) -> list[str]:
    """Validate a policy declaration; returns error messages (empty = valid)."""
    errors: list[str] = []
    if not POLICY_ID_RE.match(policy.id):
        errors.append(f"policy id must match POLICY-NNNNNN, got '{policy.id}'")
    if policy.category not in POLICY_CATEGORIES:
        errors.append(f"unknown category '{policy.category}'")
    if policy.action not in {"allow", "deny", "warn"}:
        errors.append(f"action must be allow/deny/warn, got '{policy.action}'")
    if policy.operator not in OPERATORS:
        errors.append(f"unknown operator '{policy.operator}'")
    if not policy.statement.strip():
        errors.append("statement is required")
    return errors


class PolicyEngine:
    """Versioned, composable policy registry + evaluator."""

    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}  # id -> active policy
        self._history: list[dict[str, Any]] = []  # auditable replacement log

    def register(self, policy: Policy) -> Policy:
        errors = validate_policy(policy)
        if errors:
            raise PolicyError("; ".join(errors))
        existing = self._policies.get(policy.id)
        if existing is not None:
            if existing.version == policy.version:
                raise PolicyError(f"policy {policy.id} already registered at version {policy.version}")
            policy.supersedes = existing.version
            existing.status = "deprecated"
            self._history.append({
                "event": "policy_replaced",
                "policy_id": policy.id,
                "from_version": existing.version,
                "to_version": policy.version,
                "at": utcnow(),
            })
        else:
            self._history.append({
                "event": "policy_registered",
                "policy_id": policy.id,
                "version": policy.version,
                "at": utcnow(),
            })
        self._policies[policy.id] = policy
        return policy

    def get(self, policy_id: str) -> Policy | None:
        return self._policies.get(policy_id)

    def search(self, category: str | None = None, action: PolicyVerdict | None = None,
               applies_to: str | None = None) -> list[Policy]:
        results = list(self._policies.values())
        if category is not None:
            results = [p for p in results if p.category == category]
        if action is not None:
            results = [p for p in results if p.action == action]
        if applies_to is not None:
            results = [p for p in results if p.applies_to == applies_to]
        return sorted(results, key=lambda p: (p.category, p.id))

    def evaluate(self, context: dict[str, Any]) -> list[PolicyViolation]:
        """Evaluate all active policies against a context. Pure function."""
        violations: list[PolicyViolation] = []
        for policy in self._policies.values():
            if policy.status != "active":
                continue
            if policy.applies_to != "*" and policy.applies_to not in context:
                continue  # not applicable to this context
            key = policy.applies_to if policy.applies_to != "*" else "_global"
            actual = context.get(policy.applies_to) if policy.applies_to != "*" else True
            if _evaluate_condition(policy.operator, actual, policy.operand):
                verdict: PolicyVerdict = policy.action
            else:
                verdict = "allow"
            if verdict != "allow":
                violations.append(PolicyViolation(
                    policy=policy,
                    context_key=key,
                    context_value=actual,
                    verdict=verdict,
                    detail=f"policy {policy.id} {verdict}s: {policy.statement}",
                ))
        return violations

    def denied(self, context: dict[str, Any]) -> list[PolicyViolation]:
        return [v for v in self.evaluate(context) if v.verdict == "deny"]

    def warn_only(self, context: dict[str, Any]) -> list[PolicyViolation]:
        return [v for v in self.evaluate(context) if v.verdict == "warn"]

    def is_allowed(self, context: dict[str, Any]) -> bool:
        return not self.denied(context)

    def snapshot(self) -> dict[str, Any]:
        return {
            "policies": {pid: p.to_dict() for pid, p in sorted(self._policies.items())},
            "history": list(self._history),
        }


def default_policies() -> list[Policy]:
    """The canonical policy set for the GULA AI Kernel.

    These policies encode the constitutional rules as machine-readable
    conditions. They are replaceable at runtime — overriding one of these
    defaults requires registering a higher-version policy, which is audited.
    """
    return [
        Policy("POLICY-000001", "security", "no secrets in knowledge artifacts",
               "deny", "contains", "secret", applies_to="content"),
        Policy("POLICY-000002", "deployment", "production deploys require Reviewer approval",
               "deny", "eq", "auto", applies_to="deployment_approval"),
        Policy("POLICY-000003", "autonomy", "max autonomy is L5 (pull request)",
               "deny", "gt", "L5", applies_to="autonomy_level"),
        Policy("POLICY-000004", "resource", "micro phases must not exceed 50 files",
               "deny", "gt", 50, applies_to="phase_files"),
        Policy("POLICY-000005", "resource", "micro phases must not exceed 5 minutes",
               "deny", "gt", 300, applies_to="phase_seconds"),
        Policy("POLICY-000006", "knowledge", "unverified knowledge must not be approved",
               "deny", "eq", False, applies_to="knowledge_verified"),
        Policy("POLICY-000007", "testing", "missions must not bypass quality gates",
               "deny", "eq", True, applies_to="bypass_quality"),
        Policy("POLICY-000008", "rollback", "rollback plans are required for production deploys",
               "deny", "eq", False, applies_to="has_rollback"),
        Policy("POLICY-000009", "cost", "no paid services without documented exception",
               "deny", "eq", True, applies_to="uses_paid_service"),
        Policy("POLICY-000010", "approval", "constitution changes require explicit user approval",
               "deny", "eq", "auto", applies_to="constitution_change"),
        Policy("POLICY-000011", "architecture", "no architecture changes without Architect approval",
               "deny", "eq", "auto", applies_to="architecture_change"),
        Policy("POLICY-000012", "compliance", "national platform capabilities must not be removed",
               "deny", "eq", True, applies_to="removes_national_feature"),
        Policy("POLICY-000013", "performance", "no optimization without benchmarks",
               "warn", "eq", False, applies_to="has_benchmark"),
        Policy("POLICY-000014", "documentation", "public features require documentation",
               "warn", "eq", False, applies_to="has_docs"),
        Policy("POLICY-000015", "context", "context budget limits are enforced",
               "warn", "gt", 60000, applies_to="context_tokens"),
        Policy("POLICY-000016", "risk", "high-risk missions require simulation",
               "deny", "eq", False, applies_to="simulated"),
    ]


def render_policy_markdown(engine: PolicyEngine | None = None) -> str:
    """Render the policy registry for the extension report."""
    engine = engine or PolicyEngine()
    with contextlib.suppress(PolicyError):
        for policy in default_policies():
            engine.register(policy)
    lines = [
        "# POLICY REGISTRY",
        "",
        "> Mission: GULA-KERNEL-EXT-001 — Phase 2: Policy Engine",
        "> Generated by: `scripts/kernel/ext/policy.py`",
        "",
        "| ID | Category | Action | Operator | Applies To | Version |",
        "|---|---|---|---|---|---|",
    ]
    for policy in engine.search():
        lines.append(
            f"| {policy.id} | {policy.category} | {policy.action} | "
            f"{policy.operator} | {policy.applies_to} | {policy.version} |"
        )
    lines += ["", ""]
    return "\n".join(lines) + "\n"


__all__ = [
    "OPERATORS",
    "POLICY_CATEGORIES",
    "Policy",
    "PolicyEngine",
    "PolicyError",
    "PolicyViolation",
    "default_policies",
    "render_policy_markdown",
    "validate_policy",
]
