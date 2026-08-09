from __future__ import annotations

import pytest
from app.identity.models.account import Account
from app.models.lab_user import LabUser
from app.security.abac import (
    ABACDecision,
    ABACEngine,
    ABACRequest,
    ABACRule,
    AttributeCondition,
    Effect,
    subject_from_principal,
)


class TestABACEngineFoundation:
    def test_fail_closed_with_no_rules(self):
        decision = ABACEngine().decide(
            ABACRequest(resource="patient", action="read", subject={"subject_id": "u1"})
        )
        assert decision.allowed is False
        assert decision.effect is Effect.DENY
        assert decision.rule_id is None

    def test_fail_closed_unknown_resource(self):
        engine = ABACEngine()
        engine.add_rule(
            ABACRule(
                id="r1",
                name="patient read",
                resource="patient",
                action="read",
                effect=Effect.ALLOW,
            )
        )
        decision = engine.decide(
            ABACRequest(resource="order", action="read", subject={"subject_id": "u1"})
        )
        assert decision.allowed is False
        assert "fail-closed" in decision.reason

    def test_explicit_deny_overrides_lower_priority_allow(self):
        engine = ABACEngine()
        engine.add_rule(
            ABACRule(
                id="allow-all",
                name="allow all",
                resource="*",
                action="*",
                effect=Effect.ALLOW,
                priority=200,
            )
        )
        engine.add_rule(
            ABACRule(
                id="deny-delete",
                name="deny delete",
                resource="patient",
                action="delete",
                effect=Effect.DENY,
                priority=100,
            )
        )
        assert (
            engine.decide(
                ABACRequest(resource="patient", action="delete", subject={"subject_id": "u1"})
            ).allowed
            is False
        )
        assert (
            engine.decide(
                ABACRequest(resource="patient", action="read", subject={"subject_id": "u1"})
            ).allowed
            is True
        )

    def test_deny_by_default_for_non_declared_scope(self):
        engine = ABACEngine()
        engine.add_rule(
            ABACRule(
                id="r",
                name="patient read only",
                resource="patient",
                action="read",
                effect=Effect.ALLOW,
            )
        )
        assert engine.can_access("patient", "write") is False
        assert engine.can_access("result", "read") is False

    def test_deterministic_tie_break_by_rule_id(self):
        def build(rule_ids):
            engine = ABACEngine()
            for rule_id in rule_ids:
                engine.add_rule(
                    ABACRule(
                        id=rule_id,
                        name=rule_id,
                        resource="*",
                        action="*",
                        effect=Effect.ALLOW,
                        priority=100,
                        conditions=[AttributeCondition("user.org_id", "equals", "org-1")],
                    )
                )
            return engine

        forward = build(["r-a", "r-b"])
        reverse = build(["r-b", "r-a"])
        request = ABACRequest("x", "y", {"subject_id": "u1", "org_id": "org-1"})
        assert forward.decide(request).rule_id == "r-a"
        assert reverse.decide(request).rule_id == "r-a"

    def test_wildcard_resource_rule_applies_with_priority(self):
        engine = ABACEngine()
        engine.add_rule(
            ABACRule(
                id="deny-read",
                name="deny all reads",
                resource="*",
                action="read",
                effect=Effect.DENY,
                priority=100,
            )
        )
        engine.add_rule(
            ABACRule(
                id="allow-patient-read",
                name="allow patient read",
                resource="patient",
                action="read",
                effect=Effect.ALLOW,
                priority=200,
            )
        )
        assert engine.can_access("patient", "read") is False
        assert engine.can_access("result", "read") is False

    def test_inactive_rule_is_skipped(self):
        engine = ABACEngine()
        engine.add_rule(
            ABACRule(
                id="inactive",
                name="inactive allow",
                resource="*",
                action="*",
                effect=Effect.ALLOW,
                is_active=False,
            )
        )
        assert engine.can_access("patient", "read") is False


class TestPurposeOfUse:
    def test_rule_with_purposes_requires_matching_purpose(self):
        engine = ABACEngine()
        engine.add_rule(
            ABACRule(
                id="treatment-read",
                name="treatment purpose read",
                resource="patient",
                action="read",
                effect=Effect.ALLOW,
                purposes=["treatment"],
                conditions=[AttributeCondition("user.role", "equals", "doctor")],
            )
        )
        subject = {"subject_id": "u1", "role": "doctor"}
        assert (
            engine.decide(ABACRequest("patient", "read", subject, purpose="treatment")).allowed
            is True
        )
        assert (
            engine.decide(ABACRequest("patient", "read", subject, purpose="research")).allowed
            is False
        )
        assert engine.decide(ABACRequest("patient", "read", subject)).allowed is False

    def test_empty_purposes_match_any_purpose(self):
        engine = ABACEngine()
        engine.add_rule(
            ABACRule(
                id="any",
                name="any purpose",
                resource="patient",
                action="read",
                effect=Effect.ALLOW,
            )
        )
        subject = {"subject_id": "u1"}
        assert (
            engine.decide(ABACRequest("patient", "read", subject, purpose="treatment")).allowed
            is True
        )
        assert engine.decide(ABACRequest("patient", "read", subject)).allowed is True

    def test_purpose_does_not_bypass_conditions(self):
        engine = ABACEngine()
        engine.add_rule(
            ABACRule(
                id="doctor-only",
                name="doctor only",
                resource="patient",
                action="read",
                effect=Effect.ALLOW,
                purposes=["treatment"],
                conditions=[AttributeCondition("user.role", "equals", "doctor")],
            )
        )
        decision = engine.decide(
            ABACRequest(
                "patient", "read", {"subject_id": "u1", "role": "nurse"}, purpose="treatment"
            )
        )
        assert decision.allowed is False

    def test_check_respects_purpose_keyword(self):
        engine = ABACEngine()
        engine.add_rule(
            ABACRule(
                id="r",
                name="treatment only",
                resource="patient",
                action="read",
                effect=Effect.ALLOW,
                purposes=["treatment"],
            )
        )
        assert engine.check("patient", "read", purpose="treatment") is Effect.ALLOW
        assert engine.check("patient", "read") is Effect.DENY


class TestContextAttributes:
    def test_org_facility_department_context(self):
        engine = ABACEngine()
        engine.add_rule(
            ABACRule(
                id="lab-staff",
                name="lab staff read within facility",
                resource="result",
                action="read",
                effect=Effect.ALLOW,
                conditions=[
                    AttributeCondition("user.org_id", "equals", "org-1"),
                    AttributeCondition("user.facility_id", "equals", "fac-7"),
                    AttributeCondition("user.department_id", "equals", "dept-lab"),
                ],
            )
        )
        subject = {
            "subject_id": "u1",
            "org_id": "org-1",
            "facility_id": "fac-7",
            "department_id": "dept-lab",
        }
        assert engine.can_access("result", "read", subject) is True
        assert engine.can_access("result", "read", {**subject, "facility_id": "fac-8"}) is False

    def test_role_and_attribute_combined(self):
        engine = ABACEngine()
        engine.add_rule(
            ABACRule(
                id="senior-doctor",
                name="senior doctor in cardiology",
                resource="patient",
                action="write",
                effect=Effect.ALLOW,
                conditions=[
                    AttributeCondition("user.role", "equals", "doctor"),
                    AttributeCondition("user.specialty", "equals", "cardiology"),
                ],
            )
        )
        assert (
            engine.can_access("patient", "write", {"role": "doctor", "specialty": "cardiology"})
            is True
        )
        assert (
            engine.can_access("patient", "write", {"role": "doctor", "specialty": "neurology"})
            is False
        )

    def test_environment_and_resource_attributes(self):
        engine = ABACEngine()
        engine.add_rule(
            ABACRule(
                id="within-hours",
                name="write only within working hours",
                resource="result",
                action="write",
                effect=Effect.ALLOW,
                conditions=[
                    AttributeCondition("env.hour_of_day", "less_than", 22),
                    AttributeCondition("resource.status", "in", ["draft", "pending"]),
                ],
            )
        )
        assert (
            engine.can_access(
                "result",
                "write",
                resource_attrs={"status": "draft"},
                environment={"hour_of_day": 10},
            )
            is True
        )
        assert (
            engine.can_access(
                "result",
                "write",
                resource_attrs={"status": "draft"},
                environment={"hour_of_day": 23},
            )
            is False
        )

    def test_decide_allows_subjectless_environment_policy(self):
        engine = ABACEngine()
        engine.add_rule(
            ABACRule(
                id="night-deny",
                name="deny at night",
                resource="*",
                action="*",
                effect=Effect.DENY,
                conditions=[AttributeCondition("env.hour_of_day", "greater_than", 22)],
            )
        )
        decision = engine.decide(ABACRequest("patient", "read", environment={"hour_of_day": 23}))
        assert decision.allowed is False
        assert decision.rule_id == "night-deny"


class TestDecisionAudit:
    def test_decision_recorded_with_rule(self):
        engine = ABACEngine()
        engine.add_rule(
            ABACRule(id="r1", name="allow", resource="patient", action="read", effect=Effect.ALLOW)
        )
        engine.decide(ABACRequest("patient", "read", {"subject_id": "u1"}, purpose="treatment"))
        decisions = engine.recent_decisions()
        assert len(decisions) == 1
        decision = decisions[0]
        assert decision.allowed is True
        assert decision.rule_id == "r1"
        assert decision.subject_id == "u1"
        assert decision.purpose == "treatment"
        assert decision.resource == "patient"

    def test_denied_decision_recorded_without_rule(self):
        engine = ABACEngine()
        decision = engine.decide(ABACRequest("patient", "read", {"subject_id": "u1"}))
        assert decision.allowed is False
        assert decision.rule_id is None
        assert "fail-closed" in decision.reason

    def test_decision_log_ordering_and_hook(self):
        calls: list[ABACDecision] = []
        engine = ABACEngine(on_decision=calls.append)
        engine.add_rule(
            ABACRule(id="r1", name="allow", resource="*", action="*", effect=Effect.ALLOW)
        )
        engine.decide(ABACRequest("a", "r", {"subject_id": "u1"}))
        engine.decide(ABACRequest("b", "w", {"subject_id": "u1"}))
        assert len(calls) == 2
        assert [decision.resource for decision in calls] == ["a", "b"]
        assert [decision.resource for decision in engine.recent_decisions()] == ["a", "b"]

    def test_decision_log_capacity(self):
        engine = ABACEngine(decision_log_maxlen=3)
        engine.add_rule(
            ABACRule(id="r1", name="allow", resource="*", action="*", effect=Effect.ALLOW)
        )
        for index in range(5):
            engine.decide(ABACRequest(f"r{index}", "read", {"subject_id": "u1"}))
        assert [decision.resource for decision in engine.recent_decisions()] == ["r2", "r3", "r4"]


class TestRequestValidation:
    def test_subject_without_subject_id_rejected(self):
        engine = ABACEngine()
        with pytest.raises(ValueError, match="subject_id"):
            engine.decide(ABACRequest("patient", "read", {"role": "doctor"}))

    def test_empty_resource_or_action_rejected(self):
        with pytest.raises(ValueError, match="resource"):
            ABACRequest("", "read")
        with pytest.raises(ValueError, match="action"):
            ABACRequest("patient", "")

    def test_invalid_log_capacity_rejected(self):
        with pytest.raises(ValueError):
            ABACEngine(decision_log_maxlen=0)


class TestTrustedSubject:
    def test_account_principal(self):
        account = Account(uuid="acc-1", identity_id="id-abc", account_type="human", status="active")
        subject = subject_from_principal(account, roles=["doctor"])
        assert subject["subject_id"] == "acc-1"
        assert subject["identity_id"] == "id-abc"
        assert subject["account_type"] == "human"
        assert subject["status"] == "active"
        assert subject["roles"] == ["doctor"]

    def test_lab_user_principal(self):
        user = LabUser(id=7, lab_id=3, role="admin")
        subject = subject_from_principal(user)
        assert subject["subject_id"] == "lab-user:7"
        assert subject["lab_id"] == 3
        assert subject["role"] == "admin"

    def test_unsupported_principal(self):
        with pytest.raises(TypeError, match="unsupported principal"):
            subject_from_principal({"id": 1})
