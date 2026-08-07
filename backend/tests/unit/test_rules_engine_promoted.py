from __future__ import annotations

import os

os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

from shared.rules_engine.domain.entities import RuleDefinition
from shared.rules_engine.domain.enums import Operator, RuleSeverity
from shared.rules_engine.engine import ExpressionEngine

from app.national.rules_engine import ExpressionEngine as PackageExpressionEngine


def _condition(field: str, operator: Operator, value: object) -> object:
    from shared.rules_engine.domain.entities import RuleCondition

    return RuleCondition(field=field, operator=operator, value=value)


def test_rule_all_conditions_pass() -> None:
    engine = ExpressionEngine()
    rule = RuleDefinition(
        id="r1",
        name="Reject negative result",
        severity=RuleSeverity.BLOCKER,
        conditions=[
            _condition("result", Operator.GTE, 0),
            _condition("status", Operator.EQ, "active"),
        ],
    )
    result = engine.evaluate_rule(rule, {"result": 10, "status": "active"})
    assert result.outcome.value == "pass"
    assert result.message == "All conditions satisfied"
    assert result.rule_id == "r1"


def test_rule_failure_outcome_maps_severity() -> None:
    engine = ExpressionEngine()
    rule = RuleDefinition(
        id="r2",
        name="Critical result",
        severity=RuleSeverity.CRITICAL,
        conditions=[_condition("result", Operator.GT, 100)],
    )
    result = engine.evaluate_rule(rule, {"result": 50})
    assert result.outcome.value == "error"
    assert "not satisfied" not in result.message


def test_rule_blocker_failure_blocks() -> None:
    engine = ExpressionEngine()
    rule = RuleDefinition(
        id="r3",
        name="Blocker",
        severity=RuleSeverity.BLOCKER,
        conditions=[_condition("safe", Operator.EQ, True)],
    )
    result = engine.evaluate_rule(rule, {"safe": False})
    assert result.outcome.value == "block"


def test_rule_warning_failure_warns() -> None:
    engine = ExpressionEngine()
    rule = RuleDefinition(
        id="r4",
        name="Warning",
        severity=RuleSeverity.WARNING,
        conditions=[_condition("level", Operator.LT, 5)],
    )
    result = engine.evaluate_rule(rule, {"level": 9})
    assert result.outcome.value == "warning"


def test_rule_with_missing_field_fails() -> None:
    engine = ExpressionEngine()
    rule = RuleDefinition(
        id="r5",
        name="Missing field",
        severity=RuleSeverity.INFO,
        conditions=[_condition("nested.value", Operator.EQ, 1)],
    )
    result = engine.evaluate_rule(rule, {"other": 2})
    assert result.outcome.value == "fail"


def test_expression_and_short_circuit() -> None:
    engine = ExpressionEngine()
    result = engine.evaluate(
        {"operator": "and", "conditions": [{"field": "a", "operator": "eq", "value": 1},
                                           {"field": "b", "operator": "eq", "value": 2}]},
        {"a": 1, "b": 3},
    )
    assert result.passed is False


def test_expression_or_pass() -> None:
    engine = ExpressionEngine()
    result = engine.evaluate(
        {"operator": "or", "conditions": [{"field": "a", "operator": "eq", "value": 1},
                                          {"field": "b", "operator": "eq", "value": 2}]},
        {"a": 5, "b": 2},
    )
    assert result.passed is True


def test_expression_single_condition() -> None:
    engine = ExpressionEngine()
    result = engine.evaluate({"field": "score", "operator": "gte", "value": 80}, {"score": 90})
    assert result.passed is True


def test_expression_unknown_operator() -> None:
    engine = ExpressionEngine()
    result = engine.evaluate({"field": "score", "operator": "bogus", "value": 1}, {"score": 90})
    assert result.passed is False
    assert result.details and "Unknown operator" in result.details[0]


def test_expression_contains_and_matches() -> None:
    engine = ExpressionEngine()
    assert engine.evaluate(
        {"field": "name", "operator": "contains", "value": "ra"}, {"name": "Arabic"},
    ).passed is True
    assert engine.evaluate(
        {"field": "code", "operator": "matches", "value": "^[A-Z]{3}$"}, {"code": "LAB"},
    ).passed is True
    assert engine.evaluate(
        {"field": "code", "operator": "matches", "value": "["}, {"code": "LAB"},
    ).passed is False


def test_expression_between() -> None:
    engine = ExpressionEngine()
    result = engine.evaluate(
        {"field": "age", "operator": "between", "value": [18, 65]}, {"age": 40},
    )
    assert result.passed is True
    result = engine.evaluate(
        {"field": "age", "operator": "between", "value": [18, 65]}, {"age": 70},
    )
    assert result.passed is False


def test_expression_exists_operators() -> None:
    engine = ExpressionEngine()
    assert engine.evaluate({"field": "x", "operator": "exists", "value": None}, {"x": 1}).passed
    assert engine.evaluate({"field": "x", "operator": "not_exists", "value": None}, {}).passed


def test_package_reexport_is_canonical_engine() -> None:
    assert PackageExpressionEngine is ExpressionEngine


def test_resolve_nested_dict_and_list_paths() -> None:
    engine = ExpressionEngine()
    assert engine.evaluate(
        {"field": "patient.details.age", "operator": "gt", "value": 17}, {"patient": {"details": {"age": 30}}},
    ).passed is True
    assert engine.evaluate(
        {"field": "items.0.name", "operator": "eq", "value": "x"}, {"items": [{"name": "x"}]},
    ).passed is True
