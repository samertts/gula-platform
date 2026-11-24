from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.kernel import Kernel
from app.national.rules_engine.domain.entities import (
    RuleDefinition,
)
from app.national.rules_engine.domain.enums import (
    Operator,
    RuleOutcome,
    RuleSeverity,
    RuleStatus,
)

logger = logging.getLogger("gula.kernel.rules_runtime")


class RuleExecutionStatus(str):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class RuleExecutionEvidence:
    rule_name: str
    condition_evaluations: list[dict[str, Any]] = field(default_factory=list)
    matched_values: list[Any] = field(default_factory=list)
    explanation: str = ""
    duration_ms: float = 0.0


@dataclass
class RuleExecutionResult:
    rule_id: str
    rule_name: str
    status: str = RuleExecutionStatus.PASSED
    outcome: RuleOutcome = RuleOutcome.PASS
    severity: RuleSeverity = RuleSeverity.INFO
    confidence: float = 1.0
    evidence: list[RuleExecutionEvidence] = field(default_factory=list)
    message: str = ""
    actions_taken: list[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    triggered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_evidence(self, ev: RuleExecutionEvidence) -> None:
        self.evidence.append(ev)


@dataclass
class RuleSetResult:
    ruleset_id: str
    ruleset_name: str
    results: list[RuleExecutionResult] = field(default_factory=list)
    total_rules: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    total_duration_ms: float = 0.0

    @property
    def all_passed(self) -> bool:
        return self.failed == 0 and self.errors == 0


class RuleSet:
    def __init__(
        self,
        ruleset_id: str,
        name: str,
        rules: list[RuleDefinition] | None = None,
        strategy: str = "ALL",
        metadata: dict[str, Any] | None = None,
    ):
        self.id = ruleset_id
        self.name = name
        self._rules: dict[str, RuleDefinition] = {}
        self.strategy = strategy
        self.metadata = metadata or {}
        self.version: int = 1
        self.created_at: float = time.time()
        self.updated_at: float = time.time()
        self.enabled: bool = True
        if rules:
            for r in rules:
                self._rules[r.id] = r

    def add_rule(self, rule: RuleDefinition) -> None:
        self._rules[rule.id] = rule
        self.updated_at = time.time()

    def remove_rule(self, rule_id: str) -> bool:
        if rule_id in self._rules:
            del self._rules[rule_id]
            self.updated_at = time.time()
            return True
        return False

    def get_rule(self, rule_id: str) -> RuleDefinition | None:
        return self._rules.get(rule_id)

    def list_rules(self) -> list[RuleDefinition]:
        return list(self._rules.values())

    def count(self) -> int:
        return len(self._rules)

    def effective_rules(self) -> list[RuleDefinition]:
        return [r for r in self._rules.values() if r.is_active and r.status == RuleStatus.ACTIVE]

    def to_ruleset_result(self, results: list[RuleExecutionResult]) -> RuleSetResult:
        passed = sum(1 for r in results if r.status == RuleExecutionStatus.PASSED)
        failed = sum(1 for r in results if r.status == RuleExecutionStatus.FAILED)
        errors = sum(1 for r in results if r.status == RuleExecutionStatus.ERROR)
        total_ms = sum(r.execution_time_ms for r in results)
        return RuleSetResult(
            ruleset_id=self.id,
            ruleset_name=self.name,
            results=results,
            total_rules=len(results),
            passed=passed,
            failed=failed,
            errors=errors,
            total_duration_ms=total_ms,
        )


class RulesRuntime:
    def __init__(self, kernel: Kernel | None = None):
        self._kernel = kernel
        self._rulesets: dict[str, RuleSet] = {}
        self._execution_count: int = 0
        self._timeout_default: float = 30.0

    def register_ruleset(self, ruleset: RuleSet) -> None:
        self._rulesets[ruleset.id] = ruleset
        logger.info("Ruleset registered", extra={"ruleset": ruleset.name, "id": ruleset.id})

    def get_ruleset(self, ruleset_id: str) -> RuleSet | None:
        return self._rulesets.get(ruleset_id)

    def remove_ruleset(self, ruleset_id: str) -> bool:
        if ruleset_id in self._rulesets:
            del self._rulesets[ruleset_id]
            return True
        return False

    def list_rulesets(self) -> list[RuleSet]:
        return list(self._rulesets.values())

    def execute_ruleset(
        self,
        ruleset_id: str,
        context: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> RuleSetResult | None:
        ruleset = self._rulesets.get(ruleset_id)
        if not ruleset:
            logger.error("Ruleset not found", extra={"ruleset_id": ruleset_id})
            return None

        effective = ruleset.effective_rules()
        if not effective:
            logger.info("No effective rules in ruleset", extra={"ruleset": ruleset.name})
            return ruleset.to_ruleset_result([])

        results: list[RuleExecutionResult] = []
        for rule in effective:
            result = self._execute_rule(rule, context, timeout)
            results.append(result)
            self._execution_count += 1

        return ruleset.to_ruleset_result(results)

    def execute_rule(
        self,
        rule_id: str,
        ruleset_id: str,
        context: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> RuleExecutionResult | None:
        ruleset = self._rulesets.get(ruleset_id)
        if not ruleset:
            return None
        rule = ruleset.get_rule(rule_id)
        if not rule:
            return None
        return self._execute_rule(rule, context, timeout)

    def _execute_rule(
        self,
        rule: RuleDefinition,
        context: dict[str, Any] | None,
        timeout: float | None,
    ) -> RuleExecutionResult:
        start = time.monotonic()
        ctx = context or {}

        try:
            evaluated = []
            all_match = True
            for cond in rule.conditions:
                field_value = ctx.get(cond.field)
                match = self._evaluate_condition(field_value, cond.operator, cond.value)
                evaluated.append({
                    "field": cond.field,
                    "operator": cond.operator.value if hasattr(cond.operator, "value") else str(cond.operator),
                    "expected": cond.value,
                    "actual": field_value,
                    "match": match,
                })
                if not match:
                    all_match = False

            if all_match and rule.conditions:
                outcome = RuleOutcome.PASS
                status = RuleExecutionStatus.PASSED
                message = f"All {len(rule.conditions)} conditions matched"
            else:
                outcome = RuleOutcome.FAIL
                status = RuleExecutionStatus.FAILED
                message = f"Rule conditions not satisfied ({sum(1 for e in evaluated if e['match'])}/{len(evaluated)} matched)"

            duration_ms = (time.monotonic() - start) * 1000
            ev = RuleExecutionEvidence(
                rule_name=rule.name,
                condition_evaluations=evaluated,
                explanation=rule.description,
                duration_ms=duration_ms,
            )
            result = RuleExecutionResult(
                rule_id=rule.id,
                rule_name=rule.name,
                status=status,
                outcome=outcome,
                severity=rule.severity,
                evidence=[ev],
                message=message,
                execution_time_ms=duration_ms,
            )
            logger.info(
                "Rule executed",
                extra={"rule": rule.name, "status": status, "duration_ms": round(duration_ms, 1)},
            )
            return result

        except Exception as exc:
            duration_ms = (time.monotonic() - start) * 1000
            logger.error("Rule execution error", extra={"rule": rule.name, "error": str(exc)})
            return RuleExecutionResult(
                rule_id=rule.id,
                rule_name=rule.name,
                status=RuleExecutionStatus.ERROR,
                outcome=RuleOutcome.ERROR,
                message=str(exc),
                execution_time_ms=duration_ms,
            )

    def _evaluate_condition(self, field_value: Any, operator: Any, expected: Any) -> bool:
        """Evaluate one condition, fail-safe on missing/unparseable data.

        F-077 fix: the previous implementation compared ``op_str`` to enum
        members that do not exist on the canonical ``Operator`` enum
        (``EQUAL``/``NOT_EQUAL``/``GREATER_THAN``/... vs ``EQ``/``NEQ``/``GT``/...).
        Because Python evaluates the ``or`` right-hand side whenever the string
        check is false, 15 of 16 operators raised ``AttributeError`` and every
        non-``eq`` rule silently returned ERROR. Using the operator's string
        value only (the canonical source) removes that crash.

        F-078 fix (conservative/clinical fail-safe): a missing field must not
        be coerced to 0 — that made a missing numeric value satisfy e.g.
        ``gte -1`` ("false normal"). Missing data yields ``False`` (condition
        not satisfied) and is logged, never a fake pass. Emergency care is
        unaffected: this withholds a rule result, it does not block anything.
        """
        import re

        op_str = operator.value if hasattr(operator, "value") else str(operator)

        # Operators that treat absence explicitly (not a comparison failure).
        if op_str == "exists":
            return field_value is not None
        if op_str == "not_exists":
            return field_value is None

        # FAIL-SAFE: for every value-based operator, missing data cannot match.
        if field_value is None:
            logger.warning(
                "rules_condition_indeterminate reason=missing_field operator=%s expected=%r",
                op_str, expected,
            )
            return False

        if op_str == "eq":
            return field_value == expected
        if op_str == "neq":
            return field_value != expected
        if op_str in {"gt", "gte", "lt", "lte"}:
            try:
                left = float(field_value) if not isinstance(field_value, (int, float)) else field_value
                right = float(expected) if not isinstance(expected, (int, float)) else expected
            except (TypeError, ValueError):
                logger.warning(
                    "rules_condition_indeterminate reason=unparseable operator=%s field=%r expected=%r",
                    op_str, field_value, expected,
                )
                return False
            if op_str == "gt":
                return left > right
            if op_str == "gte":
                return left >= right
            if op_str == "lt":
                return left < right
            return left <= right
        if op_str in {"in", "not_in"}:
            present = field_value in (expected if isinstance(expected, (list, tuple, set)) else [expected])
            return present if op_str == "in" else not present
        if op_str in {"contains", "not_contains"}:
            present = str(expected) in str(field_value)
            return present if op_str == "contains" else not present
        if op_str == "starts_with":
            return str(field_value).startswith(str(expected))
        if op_str == "ends_with":
            return str(field_value).endswith(str(expected))
        if op_str == "matches":
            try:
                return bool(re.search(str(expected), str(field_value)))
            except re.error:
                logger.warning("rules_condition_indeterminate reason=invalid_regex pattern=%r", expected)
                return False
        if op_str == "between":
            if isinstance(expected, (list, tuple)) and len(expected) == 2:
                try:
                    v = float(field_value)
                    return float(expected[0]) <= v <= float(expected[1])
                except (TypeError, ValueError):
                    return False
            return False
        logger.warning("rules_condition_indeterminate reason=unknown_operator operator=%r", op_str)
        return False

    def get_stats(self) -> dict[str, Any]:
        return {
            "rulesets": len(self._rulesets),
            "total_rules": sum(rs.count() for rs in self._rulesets.values()),
            "execution_count": self._execution_count,
        }
