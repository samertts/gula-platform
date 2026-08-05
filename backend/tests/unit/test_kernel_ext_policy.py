"""Unit tests for GULA-KERNEL-EXT-001 Phase 2 — Policy Engine."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.kernel.ext.policy import (
    OPERATORS,
    POLICY_CATEGORIES,
    Policy,
    PolicyEngine,
    PolicyError,
    _evaluate_condition,
    default_policies,
    render_policy_markdown,
    validate_policy,
)


def _policy(**overrides) -> Policy:
    base = {
        "id": "POLICY-100001",
        "category": "security",
        "statement": "no secrets",
        "action": "deny",
        "operator": "contains",
        "operand": "secret",
        "applies_to": "content",
    }
    base.update(overrides)
    return Policy(**base)


class TestValidation:
    def test_valid_policy_passes(self):
        assert validate_policy(_policy()) == []

    def test_bad_id(self):
        errors = validate_policy(_policy(id="POLICY-x"))
        assert any("policy id" in e for e in errors)

    def test_bad_category(self):
        errors = validate_policy(_policy(category="nope"))
        assert any("unknown category" in e for e in errors)

    def test_bad_action(self):
        errors = validate_policy(_policy(action="maybe"))
        assert any("action must be" in e for e in errors)

    def test_bad_operator(self):
        errors = validate_policy(_policy(operator="~="))
        assert any("unknown operator" in e for e in errors)

    def test_empty_statement(self):
        errors = validate_policy(_policy(statement=" "))
        assert any("statement is required" in e for e in errors)

    def test_all_categories_known(self):
        for category in POLICY_CATEGORIES:
            assert validate_policy(_policy(category=category)) == []

    def test_all_operators_valid(self):
        for op in OPERATORS:
            assert validate_policy(_policy(operator=op)) == []


class TestOperators:
    @pytest.mark.parametrize("op,actual,expected,result", [
        ("eq", 5, 5, True),
        ("neq", 5, 4, True),
        ("lt", 3, 5, True),
        ("lte", 5, 5, True),
        ("gt", 6, 5, True),
        ("gte", 5, 5, True),
        ("in", "x", ["x", "y"], True),
        ("not_in", "z", ["x", "y"], True),
        ("contains", ["a", "b"], "b", True),
        ("matches", "SECRET_KEY", r"^SECRET_", True),
    ])
    def test_operator_semantics(self, op, actual, expected, result):
        assert _evaluate_condition(op, actual, expected) is result

    def test_unknown_operator_raises(self):
        with pytest.raises(PolicyError):
            _evaluate_condition("nope", 1, 1)


class TestEngine:
    def test_register_and_get(self):
        engine = PolicyEngine()
        policy = _policy()
        engine.register(policy)
        assert engine.get("POLICY-100001") is policy

    def test_register_duplicate_same_version_raises(self):
        engine = PolicyEngine()
        engine.register(_policy())
        with pytest.raises(PolicyError):
            engine.register(_policy())

    def test_replace_marks_deprecated_and_audits(self):
        engine = PolicyEngine()
        engine.register(_policy(version="1.0.0"))
        engine.register(_policy(version="2.0.0"))
        assert engine.get("POLICY-100001").version == "2.0.0"
        assert engine.get("POLICY-100001").supersedes == "1.0.0"
        events = [h["event"] for h in engine.snapshot()["history"]]
        assert "policy_replaced" in events

    def test_search_by_category(self):
        engine = PolicyEngine()
        engine.register(_policy(id="POLICY-100001", category="security"))
        engine.register(_policy(id="POLICY-100002", category="cost"))
        assert [p.id for p in engine.search(category="cost")] == ["POLICY-100002"]

    def test_evaluate_deny(self):
        engine = PolicyEngine()
        engine.register(_policy())
        violations = engine.evaluate({"content": "contains secret value"})
        assert any(v.verdict == "deny" for v in violations)

    def test_evaluate_allow(self):
        engine = PolicyEngine()
        engine.register(_policy())
        violations = engine.evaluate({"content": "clean body"})
        assert not violations

    def test_is_allowed(self):
        engine = PolicyEngine()
        engine.register(_policy())
        assert engine.is_allowed({"content": "clean"})
        assert not engine.is_allowed({"content": "contains secret"})

    def test_applies_to_missing_key_skipped(self):
        engine = PolicyEngine()
        engine.register(_policy())
        assert engine.evaluate({"other": "x"}) == []

    def test_warn_verdict(self):
        engine = PolicyEngine()
        engine.register(_policy(action="warn", operator="contains", operand="x", applies_to="content"))
        violations = engine.evaluate({"content": "has x"})
        assert violations and violations[0].verdict == "warn"

    def test_deprecated_policy_not_evaluated(self):
        engine = PolicyEngine()
        engine.register(_policy(version="1.0.0"))
        engine.register(_policy(version="2.0.0"))
        violations = engine.evaluate({"content": "contains secret value"})
        assert len(violations) == 1  # only v2 active

    def test_default_policies_register(self):
        engine = PolicyEngine()
        for policy in default_policies():
            engine.register(policy)
        assert len(engine.search()) == len(default_policies())

    def test_default_policies_unique_ids(self):
        ids = [p.id for p in default_policies()]
        assert len(ids) == len(set(ids))


class TestDefaults:
    def test_denies_secrets(self):
        engine = PolicyEngine()
        for policy in default_policies():
            engine.register(policy)
        assert not engine.is_allowed({"content": "token = secret-key-123"})

    def test_denies_over_autonomy(self):
        engine = PolicyEngine()
        for policy in default_policies():
            engine.register(policy)
        assert not engine.is_allowed({"autonomy_level": "L7"})

    def test_denies_unverified_knowledge(self):
        engine = PolicyEngine()
        for policy in default_policies():
            engine.register(policy)
        assert not engine.is_allowed({"knowledge_verified": False})

    def test_allows_compliant_context(self):
        engine = PolicyEngine()
        for policy in default_policies():
            engine.register(policy)
        context = {
            "content": "clean",
            "deployment_approval": "manual",
            "autonomy_level": "L5",
            "phase_files": 20,
            "phase_seconds": 120,
            "knowledge_verified": True,
            "bypass_quality": False,
            "has_rollback": True,
            "uses_paid_service": False,
            "constitution_change": "manual",
            "architecture_change": "manual",
            "removes_national_feature": False,
            "has_benchmark": True,
            "has_docs": True,
            "context_tokens": 1000,
            "simulated": True,
        }
        assert engine.is_allowed(context)


class TestRender:
    def test_render_includes_policies(self):
        rendered = render_policy_markdown()
        assert "POLICY-000001" in rendered
        assert "security" in rendered
