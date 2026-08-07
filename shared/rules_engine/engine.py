from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from shared.rules_engine.domain.entities import (
    RuleCondition,
    RuleDefinition,
    RuleEvaluationResult,
)
from shared.rules_engine.domain.enums import Operator, RuleOutcome, RuleSeverity


@dataclass
class EvaluationResult:
    passed: bool
    details: list[str] = field(default_factory=list)
    error: str | None = None


class ExpressionEngine:
    def evaluate_rule(self, rule: RuleDefinition, context: dict[str, Any]) -> RuleEvaluationResult:
        start = datetime.now(UTC)
        all_passed = True
        details: list[str] = []

        for condition in rule.conditions:
            result = self._evaluate_condition(condition, context)
            if not result.passed:
                all_passed = False
            details.extend(result.details)
            if result.error:
                details.append(result.error)

        execution_time = (datetime.now(UTC) - start).total_seconds() * 1000.0

        if all_passed:
            outcome = RuleOutcome.PASS
            message = "All conditions satisfied"
        else:
            outcome = self._determine_failure_outcome(rule)
            message = "; ".join(details) if details else "Conditions not met"

        return RuleEvaluationResult(
            rule_id=rule.id,
            rule_name=rule.name,
            outcome=outcome,
            severity=rule.severity,
            message=message,
            execution_time_ms=execution_time,
        )

    def evaluate(self, expression: dict[str, Any], context: dict[str, Any]) -> EvaluationResult:
        op = expression.get("operator", "and")
        conditions = expression.get("conditions", [])
        if op == "and":
            return self._evaluate_and(conditions, context)
        if op == "or":
            return self._evaluate_or(conditions, context)
        if op == "not":
            if conditions:
                return self._evaluate_not(conditions[0], context)
            return EvaluationResult(
                passed=True, error="NOT operator requires exactly one condition",
            )
        return self._evaluate_single_condition(expression, context)

    def _evaluate_and(
        self, conditions: list[dict[str, Any]], context: dict[str, Any],
    ) -> EvaluationResult:
        details: list[str] = []
        for c in conditions:
            r = self.evaluate(c, context)
            details.extend(r.details)
            if not r.passed:
                return EvaluationResult(passed=False, details=details)
        return EvaluationResult(passed=True, details=details)

    def _evaluate_or(
        self, conditions: list[dict[str, Any]], context: dict[str, Any],
    ) -> EvaluationResult:
        details: list[str] = []
        for c in conditions:
            r = self.evaluate(c, context)
            details.extend(r.details)
            if r.passed:
                return EvaluationResult(passed=True, details=details)
        return EvaluationResult(passed=False, details=details)

    def _evaluate_not(self, condition: dict[str, Any], context: dict[str, Any]) -> EvaluationResult:
        r = self.evaluate(condition, context)
        return EvaluationResult(passed=not r.passed, details=r.details)

    def _evaluate_condition(
        self, condition: RuleCondition, context: dict[str, Any],
    ) -> EvaluationResult:
        field_value = self._resolve_field(condition.field, context)
        return self._evaluate_comparison(
            condition.field, field_value, condition.operator, condition.value,
        )

    def _evaluate_single_condition(
        self, expr: dict[str, Any], context: dict[str, Any],
    ) -> EvaluationResult:
        field = expr.get("field", "")
        op = expr.get("operator", "eq")
        value = expr.get("value")
        field_value = self._resolve_field(field, context)
        if isinstance(op, str):
            try:
                op = Operator(op)
            except ValueError:
                return EvaluationResult(passed=False, details=[f"Unknown operator: {op}"])
        return self._evaluate_comparison(field, field_value, op, value)

    def _resolve_field(self, field_path: str, context: dict[str, Any]) -> Any:
        parts = field_path.split(".")
        value: Any = context
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list) and part.isdigit():
                try:
                    value = value[int(part)]
                except (IndexError, ValueError):
                    return None
            else:
                try:
                    value = getattr(value, part, None)
                except (TypeError, AttributeError):
                    return None
            if value is None:
                return None
        return value

    def _evaluate_comparison(
        self, field: str, field_value: Any, operator: Operator, target_value: Any,
    ) -> EvaluationResult:
        if operator == Operator.EXISTS:
            return EvaluationResult(
                passed=field_value is not None,
                details=[f"{field} exists: {field_value is not None}"],
            )
        if operator == Operator.NOT_EXISTS:
            return EvaluationResult(
                passed=field_value is None,
                details=[f"{field} not exists: {field_value is None}"],
            )
        if field_value is None:
            return EvaluationResult(
                passed=False,
                details=[f"{field} is None, cannot apply {operator.value}"],
            )
        if operator == Operator.EQ:
            result = field_value == target_value
        elif operator == Operator.NEQ:
            result = field_value != target_value
        elif operator == Operator.GT:
            result = self._safe_compare(field_value, target_value, lambda a, b: a > b)
        elif operator == Operator.GTE:
            result = self._safe_compare(field_value, target_value, lambda a, b: a >= b)
        elif operator == Operator.LT:
            result = self._safe_compare(field_value, target_value, lambda a, b: a < b)
        elif operator == Operator.LTE:
            result = self._safe_compare(field_value, target_value, lambda a, b: a <= b)
        elif operator == Operator.IN:
            result = field_value in (
                target_value if isinstance(target_value, (list, tuple)) else [target_value]
            )
        elif operator == Operator.NOT_IN:
            result = field_value not in (
                target_value if isinstance(target_value, (list, tuple)) else [target_value]
            )
        elif operator == Operator.BETWEEN:
            if isinstance(target_value, (list, tuple)) and len(target_value) == 2:
                result = self._safe_compare(
                    field_value, target_value[0], lambda a, b: a >= b,
                ) and self._safe_compare(field_value, target_value[1], lambda a, b: a <= b)
            else:
                return EvaluationResult(
                    passed=False, details=[f"BETWEEN requires a list of 2 values for {field}"],
                )
        elif operator == Operator.CONTAINS:
            result = str(target_value) in str(field_value) if field_value is not None else False
        elif operator == Operator.NOT_CONTAINS:
            result = str(target_value) not in str(field_value) if field_value is not None else True
        elif operator == Operator.STARTS_WITH:
            result = (
                str(field_value).startswith(str(target_value)) if field_value is not None else False
            )
        elif operator == Operator.ENDS_WITH:
            result = (
                str(field_value).endswith(str(target_value)) if field_value is not None else False
            )
        elif operator == Operator.MATCHES:
            try:
                result = (
                    bool(re.search(str(target_value), str(field_value)))
                    if field_value is not None
                    else False
                )
            except re.error:
                return EvaluationResult(
                    passed=False, details=[f"Invalid regex pattern for {field}"],
                )
        else:
            return EvaluationResult(passed=False, details=[f"Unsupported operator: {operator}"])
        return EvaluationResult(
            passed=result,
            details=[f"{field} {operator.value} {target_value}: {result}"],
        )

    def _safe_compare(self, a: Any, b: Any, cmp) -> bool:
        try:
            if isinstance(a, str) and isinstance(b, str):
                return cmp(a, b)
            return cmp(
                float(a) if not isinstance(a, (int, float)) else a,
                float(b) if not isinstance(b, (int, float)) else b,
            )
        except (TypeError, ValueError):
            return False

    def _determine_failure_outcome(self, rule: RuleDefinition) -> RuleOutcome:
        if rule.severity == RuleSeverity.BLOCKER:
            return RuleOutcome.BLOCK
        if rule.severity == RuleSeverity.CRITICAL:
            return RuleOutcome.ERROR
        if rule.severity == RuleSeverity.WARNING:
            return RuleOutcome.WARNING
        return RuleOutcome.FAIL
