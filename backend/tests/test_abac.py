from __future__ import annotations

import pytest
from app.security.abac import (
    ABACEngine,
    ABACRule,
    AttributeCondition,
    Effect,
)


class TestABAC:
    def test_allow_rule(self):
        engine = ABACEngine()
        rule = ABACRule(
            name="Allow doctors to read patients",
            resource="patient",
            action="read",
            effect=Effect.ALLOW,
            conditions=[
                AttributeCondition(attribute="user.role", operator="equals", value="doctor"),
            ],
        )
        engine.add_rule(rule)
        assert engine.can_access("patient", "read", {"role": "doctor"}) is True
        assert engine.can_access("patient", "read", {"role": "nurse"}) is False

    def test_deny_overrides_allow(self):
        engine = ABACEngine()
        engine.add_rule(ABACRule(
            name="Allow all",
            resource="*",
            action="*",
            effect=Effect.ALLOW,
            priority=200,
        ))
        engine.add_rule(ABACRule(
            name="Deny delete",
            resource="patient",
            action="delete",
            effect=Effect.DENY,
            priority=100,
        ))
        assert engine.can_access("patient", "read") is True
        assert engine.can_access("patient", "delete") is False

    def test_resource_specific_rule(self):
        engine = ABACEngine()
        engine.add_rule(ABACRule(
            name="Allow read patient",
            resource="patient",
            action="read",
            effect=Effect.ALLOW,
        ))
        assert engine.can_access("patient", "read") is True
        assert engine.can_access("order", "read") is False

    def test_condition_operators(self):
        engine = ABACEngine()
        engine.add_rule(ABACRule(
            name="Iraqi doctors only",
            resource="patient",
            action="read",
            effect=Effect.ALLOW,
            conditions=[
                AttributeCondition(attribute="user.country", operator="equals", value="IQ"),
                AttributeCondition(attribute="user.role", operator="in", value=["doctor", "specialist"]),
            ],
        ))
        assert engine.can_access("patient", "read", {"country": "IQ", "role": "doctor"}) is True
        assert engine.can_access("patient", "read", {"country": "US", "role": "doctor"}) is False

    def test_department_restriction(self):
        engine = ABACEngine()
        engine.add_rule(ABACRule(
            name="Lab dept can write results",
            resource="result",
            action="write",
            effect=Effect.ALLOW,
            conditions=[
                AttributeCondition(attribute="user.department", operator="equals", value="lab"),
            ],
        ))
        assert engine.can_access("result", "write", {"department": "lab"}) is True
        assert engine.can_access("result", "write", {"department": "admin"}) is False

    def test_owner_access(self):
        engine = ABACEngine()
        engine.add_rule(ABACRule(
            name="Owner can edit",
            resource="record",
            action="edit",
            effect=Effect.ALLOW,
            conditions=[
                AttributeCondition(attribute="user.role", operator="equals", value="admin"),
            ],
            priority=50,
        ))
        assert engine.can_access("record", "edit", {"role": "admin"}) is True
        assert engine.can_access("record", "edit", {"role": "user"}) is False

    def test_list_rules(self):
        engine = ABACEngine()
        engine.add_rule(ABACRule(name="R1", resource="a", action="r", effect=Effect.ALLOW))
        engine.add_rule(ABACRule(name="R2", resource="b", action="w", effect=Effect.DENY))
        assert len(engine.list_rules()) == 2
        assert len(engine.list_rules("a")) == 1
