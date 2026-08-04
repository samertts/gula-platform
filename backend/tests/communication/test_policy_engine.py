"""Unit tests: Policy Engine (priority, escalation, fallback, preferences,
required/optional channels, mandatory overrides)."""

from __future__ import annotations

from shared.communication.policy import (
    Policy,
    PolicyEngine,
    RecipientPreferences,
)

from .fakes import DictPreferenceStore


def make_engine(**prefs_by_recipient):
    return PolicyEngine(preference_store=DictPreferenceStore(prefs_by_recipient))


class TestPolicyBasics:
    def test_register_and_get(self):
        engine = PolicyEngine()
        policy = engine.register(Policy(id="p", required_channels=("email",)))
        assert engine.get("p") is policy

    def test_duplicate_registration_rejected(self):
        engine = PolicyEngine()
        engine.register(Policy(id="p"))
        try:
            engine.register(Policy(id="p"))
        except ValueError:
            return
        raise AssertionError("duplicate policy id must raise")

    def test_policy_requires_id(self):
        try:
            Policy(id="")
        except ValueError:
            return
        raise AssertionError("empty policy id must raise")

    def test_required_channels_included(self):
        decision = PolicyEngine().decide(
            Policy(id="p", required_channels=("email", "sms")),
            "anyone",
        )
        assert decision.channels == ["email", "sms"]

    def test_optional_channels_included_by_default(self):
        decision = PolicyEngine().decide(
            Policy(id="p", optional_channels=("telegram",)),
            "anyone",
        )
        assert decision.channels == ["telegram"]


class TestPreferences:
    def test_recipient_blocked_optional_channel_skipped(self):
        engine = make_engine(
            user1=RecipientPreferences(allowed_channels=frozenset({"email"})),
        )
        decision = engine.decide(
            Policy(id="p", optional_channels=("telegram", "email")),
            "user1",
        )
        assert "telegram" not in decision.channels
        assert "email" in decision.channels
        assert decision.skipped == (("telegram", "recipient_preference"),)

    def test_blocked_required_channel_skipped_unless_mandatory(self):
        prefs = RecipientPreferences(allowed_channels=frozenset({"email"}))
        engine = make_engine(user1=prefs)

        optional = engine.decide(Policy(id="p", required_channels=("sms",)), "user1")
        assert optional.channels == []
        assert optional.skipped == (("sms", "recipient_preference"),)

        mandatory = engine.decide(
            Policy(id="p", required_channels=("sms",), mandatory=True),
            "user1",
        )
        assert mandatory.channels == ["sms"]

    def test_preferred_channels_ordered_first(self):
        engine = make_engine(
            user1=RecipientPreferences(
                allowed_channels=frozenset({"sms", "telegram", "email"}),
                preferred_channels=("telegram",),
            ),
        )
        decision = engine.decide(
            Policy(id="p", optional_channels=("email", "sms", "telegram")),
            "user1",
        )
        assert decision.channels[0] == "telegram"

    def test_quiet_hours_do_not_block_mandatory(self):
        prefs = RecipientPreferences(allowed_channels=frozenset({"sms"}), quiet_hours=True)
        engine = make_engine(user1=prefs)
        decision = engine.decide(
            Policy(id="p", required_channels=("sms",), mandatory=True),
            "user1",
        )
        assert decision.channels == ["sms"]

    def test_fallback_channels_always_included(self):
        decision = PolicyEngine().decide(
            Policy(id="p", required_channels=("email",), fallback_channels=("sms",)),
            "anyone",
        )
        assert decision.channels == ["email", "sms"]

    def test_unrestricted_preferences_when_no_store(self):
        engine = PolicyEngine()
        decision = engine.decide(
            Policy(id="p", required_channels=("email",)),
            "anyone",
        )
        assert decision.channels == ["email"]


class TestPriority:
    def test_priority_carried_into_attempts(self):
        from shared.communication.model import Priority

        decision = PolicyEngine().decide(
            Policy(id="p", required_channels=("email",), priority=Priority.URGENT),
            "anyone",
        )
        assert decision.attempts[0].priority == Priority.URGENT
        assert decision.attempts[0].is_required is True
        assert decision.attempts[0].is_fallback is False

    def test_fallback_attempt_marked(self):
        decision = PolicyEngine().decide(
            Policy(id="p", required_channels=("email",), fallback_channels=("sms",)),
            "anyone",
        )
        assert decision.attempts[1].is_fallback is True

    def test_decision_serialisation(self):
        decision = PolicyEngine().decide(
            Policy(id="p", required_channels=("email",)),
            "anyone",
        )
        payload = decision.to_dict()
        assert payload["policy_id"] == "p"
        assert payload["attempts"][0]["channel"] == "email"


class TestSerialisation:
    def test_policy_to_dict(self):
        payload = Policy(
            id="p",
            required_channels=("email",),
            escalation_channels=("sms",),
            mandatory=True,
        ).to_dict()
        assert payload["required_channels"] == ["email"]
        assert payload["escalation_channels"] == ["sms"]
        assert payload["mandatory"] is True
