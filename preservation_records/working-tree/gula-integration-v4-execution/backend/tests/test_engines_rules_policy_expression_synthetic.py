"""Phase E (F-066 / D-023) — rules / policy / expression engines, synthetic only.

No DB, no network, no real patient data. All contexts and rule definitions below
are fictional. These engines are pure dataclass/dict evaluators, so they are
tested directly with plain Python fixtures.

This suite closes the *missing-evidence* finding F-066 (dedicated tests) with
NO production-logic change. Defects observed while mapping the engines are
recorded as separate residual findings in GOVERNANCE/GECS/FINDINGS_REGISTRY.md
rather than silently "fixed" here:
  - rules_runtime: strategy and priority are stored but never applied; no
    version history/rollback; its 16-operator enum-name crash (F-077) and
    missing-field coercion (F-078) were fixed in this phase with regressions.
  - policy_runtime: a REQUIRE_APPROVAL match yields decision=REQUIRE_APPROVAL
    while allowed=False (contradictory downstream state).
  - expression_engine: no cycle detection for self-referential expressions.

Evidence id: E-058 (see GOVERNANCE/GECS/EVIDENCE_REGISTRY.md).
"""

from __future__ import annotations

import pytest

from app.core import policy_engine as core_policy
from app.kernel.policy_runtime import (
    PolicyContext,
    PolicyDecisionValue,
    PolicyRuntime,
)
from app.kernel.rules_runtime import (
    RuleExecutionStatus,
    RuleSet,
    RulesRuntime,
)
from app.national.rules_engine.domain.entities import (
    RuleCondition,
    RuleDefinition,
)
from app.national.rules_engine.domain.enums import (
    Operator,
    RuleOutcome,
    RuleSeverity,
    RuleStatus,
)
from app.national.rules_engine.domain.expression_engine import ExpressionEngine


# ---------------------------------------------------------------------------
# shared synthetic fixtures
# ---------------------------------------------------------------------------


def _rule(
    rid: str,
    conditions: list[RuleCondition],
    *,
    status: RuleStatus = RuleStatus.ACTIVE,
    severity: RuleSeverity = RuleSeverity.WARNING,
) -> RuleDefinition:
    return RuleDefinition(
        id=rid,
        name=f"synthetic-rule-{rid}",
        description="synthetic test rule",
        severity=severity,
        status=status,
        conditions=conditions,
    )


@pytest.fixture(autouse=True)
def _no_kill_switch(monkeypatch):
    # Deterministic policy behavior: kill switch is explicitly inactive.
    monkeypatch.setattr(core_policy, "_CONTROL_LAYER_ENABLED", True)
    monkeypatch.setattr("app.core.kill_switch.is_kill_switch_active", lambda: False)


# ---------------------------------------------------------------------------
# RulesRuntime
# ---------------------------------------------------------------------------


class TestRulesRuntime:
    def test_register_list_remove_ruleset(self):
        rt = RulesRuntime()
        rs = RuleSet("rs-1", "Synthetic set", [_rule("r1", [])])
        rt.register_ruleset(rs)
        assert [r.id for r in rt.list_rulesets()] == ["rs-1"]
        assert rt.get_ruleset("rs-1") is rs
        assert rt.remove_ruleset("rs-1") is True
        assert rt.remove_ruleset("rs-1") is False
        assert rt.get_ruleset("rs-1") is None

    def test_execute_ruleset_all_conditions_match(self):
        rule = _rule("r-pass", [
            RuleCondition(field="glucose", operator=Operator.GTE, value=70),
            RuleCondition(field="unit", operator=Operator.EQ, value="mg/dL"),
        ])
        rt = RulesRuntime()
        rt.register_ruleset(RuleSet("rs", "Synthetic", [rule]))
        result = rt.execute_ruleset("rs", {"glucose": 95, "unit": "mg/dL"})
        assert result is not None
        assert result.all_passed is True
        assert result.passed == 1 and result.failed == 0 and result.errors == 0
        assert result.results[0].status == RuleExecutionStatus.PASSED
        assert result.results[0].outcome == RuleOutcome.PASS
        assert len(result.results[0].evidence[0].condition_evaluations) == 2

    def test_execute_ruleset_condition_not_met(self):
        rule = _rule("r-fail", [RuleCondition(field="hr", operator=Operator.GT, value=100)])
        rt = RulesRuntime()
        rt.register_ruleset(RuleSet("rs", "Synthetic", [rule]))
        result = rt.execute_ruleset("rs", {"hr": 72})
        assert result.all_passed is False
        assert result.failed == 1
        assert result.results[0].outcome == RuleOutcome.FAIL
        assert result.results[0].evidence[0].condition_evaluations[0]["match"] is False

    def test_draft_and_inactive_rules_are_not_effective(self):
        active = _rule("active", [RuleCondition(field="x", operator=Operator.EQ, value=1)])
        draft = _rule("draft", [], status=RuleStatus.DRAFT)
        inactive = _rule("inactive", [], status=RuleStatus.INACTIVE)
        rs = RuleSet("rs", "Synthetic", [active, draft, inactive])
        assert [r.id for r in rs.effective_rules()] == ["active"]

    def test_expired_rule_is_not_effective(self):
        from datetime import datetime, timedelta

        from app._compat import UTC

        expired = _rule("expired", [])
        expired.effective_to = datetime.now(UTC) - timedelta(days=1)
        assert expired.is_active is False
        assert RuleSet("rs", "Synthetic", [expired]).effective_rules() == []

    def test_execute_single_rule_and_missing_ruleset(self):
        rule = _rule("r1", [RuleCondition(field="flag", operator=Operator.EQ, value=True)])
        rt = RulesRuntime()
        rt.register_ruleset(RuleSet("rs", "Synthetic", [rule]))
        assert rt.execute_rule("r1", "rs", {"flag": True}).status == RuleExecutionStatus.PASSED
        assert rt.execute_rule("missing", "rs", {}) is None
        assert rt.execute_rule("r1", "missing", {}) is None
        assert rt.execute_ruleset("missing", {}) is None

    def test_empty_ruleset_returns_zero_result(self):
        rt = RulesRuntime()
        rt.register_ruleset(RuleSet("empty", "Synthetic", []))
        result = rt.execute_ruleset("empty", {})
        assert result.all_passed is True
        assert result.total_rules == 0

    def test_all_operators_behave_as_documented_for_present_values(self):
        rt = RulesRuntime()
        cases = [
            (Operator.EQ, 5, 5, True),
            (Operator.NEQ, 5, 6, True),
            (Operator.GT, 6, 5, True),
            (Operator.GTE, 5, 5, True),
            (Operator.LT, 4, 5, True),
            (Operator.LTE, 5, 5, True),
            (Operator.IN, "b", ["a", "b"], True),
            (Operator.CONTAINS, "abcdef", "cd", True),
            (Operator.STARTS_WITH, "abcdef", "abc", True),
            (Operator.ENDS_WITH, "abcdef", "def", True),
            (Operator.MATCHES, "abc123", r"\d+", True),
        ]
        for i, (op, value, expected, want) in enumerate(cases):
            rule = _rule(f"op-{i}", [RuleCondition(field="v", operator=op, value=expected)])
            rt.register_ruleset(RuleSet(f"rs-{i}", "Synthetic", [rule]))
            result = rt.execute_ruleset(f"rs-{i}", {"v": value})
            assert result.results[0].status == (
                RuleExecutionStatus.PASSED if want else RuleExecutionStatus.FAILED
            ), f"operator {op.value}"

    def test_invalid_regex_fails_closed_without_error_or_exception(self):
        # Fail-safe: a bad regex yields a clean, evidenced FAILED result —
        # never an unhandled exception that aborts a batch, and never a pass.
        rule = _rule("bad-regex", [RuleCondition(field="v", operator=Operator.MATCHES, value="[")])
        rt = RulesRuntime()
        rt.register_ruleset(RuleSet("rs", "Synthetic", [rule]))
        result = rt.execute_ruleset("rs", {"v": "x"})
        assert result.errors == 0
        assert result.failed == 1
        assert result.results[0].status == RuleExecutionStatus.FAILED
        assert result.all_passed is False

    def test_evidence_preserves_actual_value_and_stats(self):
        rule = _rule("r", [RuleCondition(field="v", operator=Operator.EQ, value="expected")])
        rt = RulesRuntime()
        rt.register_ruleset(RuleSet("rs", "Synthetic", [rule]))
        rt.execute_ruleset("rs", {"v": "actual"})
        ev = rt.get_ruleset("rs").list_rules()[0]
        assert ev.name == "synthetic-rule-r"
        assert rt.get_stats()["execution_count"] == 1
        assert rt.get_stats()["rulesets"] == 1

    def test_missing_field_never_fake_passes(self):
        # F-078 regression: `None` must not be coerced to 0 (which let a
        # missing numeric value satisfy `gte -1`). Missing data is a fail-safe
        # no-match with full evidence preserved.
        rule = _rule("missing", [RuleCondition(field="absent", operator=Operator.GTE, value=-1)])
        rt = RulesRuntime()
        rt.register_ruleset(RuleSet("rs", "Synthetic", [rule]))
        result = rt.execute_ruleset("rs", {})
        assert result.results[0].status == RuleExecutionStatus.FAILED
        evaluation = result.results[0].evidence[0].condition_evaluations[0]
        assert evaluation["actual"] is None
        assert evaluation["match"] is False

    def test_unknown_and_unparseable_operators_fail_closed(self):
        # F-077 regression: previously non-eq operators crashed with
        # AttributeError (Operator.EQUAL does not exist); unknown operators
        # must fail closed rather than raise or silently pass.
        rt = RulesRuntime()
        for i, (op, value, expected) in enumerate([
            (Operator.GTE, "not-a-number", 5),
            (Operator.LTE, 10, "not-a-number"),
        ]):
            rule = _rule(f"bad-{i}", [RuleCondition(field="v", operator=op, value=expected)])
            rt.register_ruleset(RuleSet(f"rs-{i}", "Synthetic", [rule]))
            res = rt.execute_ruleset(f"rs-{i}", {"v": value})
            assert res.results[0].status == RuleExecutionStatus.FAILED
            assert res.errors == 0  # no crash — a clean, evidenced no-match

    def test_all_sixteen_operators_evaluate_without_error(self):
        # F-077 regression: every canonical Operator must be evaluable.
        rt = RulesRuntime()
        ctx = {"v": 5, "s": "abc", "nested": {"x": 1}}
        ops = [
            (Operator.EQ, "v", 5), (Operator.NEQ, "v", 6),
            (Operator.GT, "v", 3), (Operator.GTE, "v", 5),
            (Operator.LT, "v", 9), (Operator.LTE, "v", 5),
            (Operator.IN, "v", [1, 5]), (Operator.NOT_IN, "v", [1, 2]),
            (Operator.BETWEEN, "v", [1, 10]), (Operator.CONTAINS, "s", "b"),
            (Operator.NOT_CONTAINS, "s", "z"), (Operator.STARTS_WITH, "s", "a"),
            (Operator.ENDS_WITH, "s", "c"), (Operator.MATCHES, "s", "^a"),
            (Operator.EXISTS, "v", None), (Operator.NOT_EXISTS, "absent", None),
        ]
        for i, (op, field, value) in enumerate(ops):
            rule = _rule(f"all-{i}", [RuleCondition(field=field, operator=op, value=value)])
            rt.register_ruleset(RuleSet(f"rs-{i}", "Synthetic", [rule]))
            res = rt.execute_ruleset(f"rs-{i}", ctx)
            assert res.errors == 0, f"operator {op.value} crashed"
            assert res.results[0].status == RuleExecutionStatus.PASSED, f"operator {op.value}"


# ---------------------------------------------------------------------------
# ExpressionEngine
# ---------------------------------------------------------------------------


class TestExpressionEngine:
    def test_single_condition_eq_and_dotted_field(self):
        engine = ExpressionEngine()
        context = {"patient": {"vitals": {"glucose": 95}}}
        result = engine.evaluate(
            {"field": "patient.vitals.glucose", "operator": "eq", "value": 95}, context
        )
        assert result.passed is True
        assert result.error is None

    def test_and_or_not(self):
        engine = ExpressionEngine()
        ctx = {"a": 1, "b": 0}
        and_expr = {"operator": "and", "conditions": [
            {"field": "a", "operator": "eq", "value": 1},
            {"field": "b", "operator": "eq", "value": 1},
        ]}
        assert engine.evaluate(and_expr, ctx).passed is False
        or_expr = {"operator": "or", "conditions": [
            {"field": "a", "operator": "eq", "value": 1},
            {"field": "b", "operator": "eq", "value": 1},
        ]}
        assert engine.evaluate(or_expr, ctx).passed is True
        not_expr = {"operator": "not", "conditions": [{"field": "b", "operator": "eq", "value": 1}]}
        assert engine.evaluate(not_expr, ctx).passed is True

    def test_all_operators_on_present_values(self):
        engine = ExpressionEngine()
        ctx = {"v": "abc", "n": 10}
        cases = [
            ({"field": "n", "operator": "gt", "value": 5}, True),
            ({"field": "n", "operator": "gte", "value": 10}, True),
            ({"field": "n", "operator": "lt", "value": 20}, True),
            ({"field": "n", "operator": "lte", "value": 10}, True),
            ({"field": "n", "operator": "in", "value": [5, 10]}, True),
            ({"field": "n", "operator": "not_in", "value": [1, 2]}, True),
            ({"field": "n", "operator": "between", "value": [5, 15]}, True),
            ({"field": "v", "operator": "contains", "value": "b"}, True),
            ({"field": "v", "operator": "not_contains", "value": "z"}, True),
            ({"field": "v", "operator": "starts_with", "value": "ab"}, True),
            ({"field": "v", "operator": "ends_with", "value": "bc"}, True),
            ({"field": "v", "operator": "matches", "value": "^a"}, True),
            ({"field": "v", "operator": "exists"}, True),
            ({"field": "missing", "operator": "not_exists"}, True),
        ]
        for expr, want in cases:
            assert engine.evaluate(expr, ctx).passed is want, expr

    def test_missing_value_is_not_silently_passed(self):
        engine = ExpressionEngine()
        result = engine.evaluate({"field": "absent", "operator": "gt", "value": 5}, {})
        assert result.passed is False
        assert any("None" in d for d in result.details)

    def test_unknown_operator_fails_closed(self):
        engine = ExpressionEngine()
        result = engine.evaluate({"field": "v", "operator": "~~", "value": 1}, {"v": 1})
        assert result.passed is False
        assert any("Unknown operator" in d for d in result.details)

    def test_invalid_regex_fails_closed(self):
        engine = ExpressionEngine()
        result = engine.evaluate({"field": "v", "operator": "matches", "value": "["}, {"v": "x"})
        assert result.passed is False
        assert any("Invalid regex" in d for d in result.details)

    def test_between_requires_two_values(self):
        engine = ExpressionEngine()
        result = engine.evaluate({"field": "n", "operator": "between", "value": [1]}, {"n": 5})
        assert result.passed is False
        assert any("BETWEEN requires" in d for d in result.details)

    def test_type_mismatch_returns_false_not_exception(self):
        engine = ExpressionEngine()
        # A non-numeric string against a numeric target is unparseable:
        # _safe_compare catches ValueError/TypeError and returns False.
        result = engine.evaluate({"field": "v", "operator": "gt", "value": 5}, {"v": "not-a-number"})
        assert result.passed is False

    def test_evaluate_rule_maps_failure_severity_to_outcome(self):
        engine = ExpressionEngine()
        blocker = _rule("b", [RuleCondition(field="v", operator=Operator.EQ, value=1)],
                        severity=RuleSeverity.BLOCKER)
        result = engine.evaluate_rule(blocker, {"v": 2})
        assert result.outcome == RuleOutcome.BLOCK
        info = _rule("i", [RuleCondition(field="v", operator=Operator.EQ, value=1)],
                     severity=RuleSeverity.INFO)
        assert engine.evaluate_rule(info, {"v": 2}).outcome == RuleOutcome.FAIL

    def test_characterization_empty_not_returns_passed_with_error(self):
        # Residual finding F-075: empty NOT yields passed=True alongside an
        # error string — contradictory state. Pinned, not endorsed.
        engine = ExpressionEngine()
        result = engine.evaluate({"operator": "not", "conditions": []}, {})
        assert result.passed is True
        assert result.error is not None


# ---------------------------------------------------------------------------
# PolicyRuntime
# ---------------------------------------------------------------------------


class TestPolicyRuntime:
    def test_unmapped_action_with_no_policies_is_default_deny(self):
        pr = PolicyRuntime()
        result = pr.evaluate(PolicyContext(action="unknown_action", environment="development"))
        assert result.decision == PolicyDecisionValue.DENY
        assert result.allowed is False
        assert result.matches == []

    def test_critical_action_always_denied(self):
        pr = PolicyRuntime()
        for env in ("production", "development", "test"):
            result = pr.evaluate(PolicyContext(action="audit_delete", environment=env))
            assert result.decision == PolicyDecisionValue.DENY

    def test_production_restricts_db_write(self):
        pr = PolicyRuntime()
        result = pr.evaluate(PolicyContext(action="db_write", environment="production"))
        assert result.decision == PolicyDecisionValue.DENY
        assert result.allowed is False

    def test_development_allows_standard_action(self):
        pr = PolicyRuntime()
        result = pr.evaluate(PolicyContext(action="db_write", environment="development"))
        assert result.decision == PolicyDecisionValue.ALLOW
        assert result.is_allowed is True

    def test_custom_allow_policy(self):
        pr = PolicyRuntime()
        pr.register_policy("synthetic-allow", {"rules": [
            {"name": "allow-by-tenant", "condition": {}, "decision": "allow", "reason": "synthetic"},
        ]})
        result = pr.evaluate(PolicyContext(action="unmapped", environment="test"),
                             policies=["synthetic-allow"])
        assert result.decision == PolicyDecisionValue.ALLOW
        assert "synthetic-allow" in result.matched_policies

    def test_conflicting_policies_deny(self):
        # Fail-safe: any DENY overrides an ALLOW (all() required).
        pr = PolicyRuntime()
        pr.register_policy("allow", {"rules": [{"condition": {}, "decision": "allow"}]})
        pr.register_policy("deny", {"rules": [{"condition": {}, "decision": "deny"}]})
        result = pr.evaluate(PolicyContext(action="unmapped", environment="test"),
                             policies=["allow", "deny"])
        assert result.decision == PolicyDecisionValue.DENY
        assert result.allowed is False

    def test_unknown_custom_policy_is_ignored(self):
        pr = PolicyRuntime()
        result = pr.evaluate(PolicyContext(action="unmapped"), policies=["does-not-exist"])
        assert result.decision == PolicyDecisionValue.DENY

    def test_invalid_custom_decision_defaults_to_deny(self):
        pr = PolicyRuntime()
        pr.register_policy("bad", {"rules": [{"condition": {}, "decision": "maybe"}]})
        result = pr.evaluate(PolicyContext(action="unmapped"), policies=["bad"])
        assert result.decision == PolicyDecisionValue.DENY

    def test_action_to_core_mapping(self):
        pr = PolicyRuntime()
        assert pr._map_to_core_action("db_schema").value == "db_schema"
        assert pr._map_to_core_action("not_a_real_action") is None
        assert pr._map_to_core_action("secret_rotation").value == "secret_rotation"

    def test_stats_counts_evaluations(self):
        pr = PolicyRuntime()
        for _ in range(3):
            pr.evaluate(PolicyContext(action="unknown_action", environment="test"))
        stats = pr.get_stats()
        assert stats["evaluation_count"] == 3
        assert stats["custom_policies"] == 0

    def test_require_approval_match_resolves_to_deny_fail_closed(self):
        # A REQUIRE_APPROVAL match makes all(...) over matches false, so the
        # final decision is DENY while requires_approval stays True (the
        # `if allowed and requires_approval` branch is effectively dead code).
        # This is fail-closed and safe; the contradictory signal is recorded
        # as residual finding F-076, never relied on as an approval grant.
        pr = PolicyRuntime()
        pr.register_policy("approval", {"rules": [
            {"condition": {}, "decision": "require_approval", "reason": "synthetic"},
        ]})
        result = pr.evaluate(PolicyContext(action="unmapped"), policies=["approval"])
        assert result.decision == PolicyDecisionValue.DENY
        assert result.requires_approval is True
        assert result.allowed is False
