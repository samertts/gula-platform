from __future__ import annotations

from typing import cast

import pytest
from app.core.release_capabilities import (
    PHASE1_CAPABILITIES,
    CapabilityDecision,
    ReleasePolicyConfig,
    decide_release_capability,
    phase1_policy_from_environment,
    require_release_capability,
)
from fastapi import HTTPException
from sqlalchemy.orm import Session

FAKE_DB = cast(Session, object())
ALL_PHASE1 = frozenset(PHASE1_CAPABILITIES)


def entitled(_feature: str, _lab_id: int, _db: Session) -> bool:
    return True


def denied_entitlement(_feature: str, _lab_id: int, _db: Session) -> bool:
    return False


def enabled_policy(*, approved_tenant_ids: frozenset[int] = frozenset({7})) -> ReleasePolicyConfig:
    return ReleasePolicyConfig(
        enabled_capability_keys=ALL_PHASE1,
        approved_tenant_ids=approved_tenant_ids,
    )


class TestReleaseCapabilityPolicy:
    def test_default_policy_denies_even_a_known_phase1_capability(self) -> None:
        decision = decide_release_capability(
            "phase1.identity",
            7,
            FAKE_DB,
            ReleasePolicyConfig(),
            entitlement_resolver=entitled,
        )

        assert decision.allowed is False
        assert decision.reason == "not_enabled_for_release"

    def test_environment_policy_defaults_to_no_enabled_capabilities(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("GULA_RELEASE_ENABLED_CAPABILITIES", raising=False)
        monkeypatch.delenv("GULA_RELEASE_APPROVED_TENANT_IDS", raising=False)

        policy = phase1_policy_from_environment()

        assert policy.enabled_capability_keys == frozenset()
        assert policy.approved_tenant_ids == frozenset()

    def test_environment_policy_parses_only_explicit_valid_tenants(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(
            "GULA_RELEASE_ENABLED_CAPABILITIES",
            "phase1.lims.orders, phase1.lims.sample_tracking",
        )
        monkeypatch.setenv("GULA_RELEASE_APPROVED_TENANT_IDS", "7, invalid, -3, 12")

        policy = phase1_policy_from_environment()

        assert policy.enabled_capability_keys == frozenset(
            {"phase1.lims.orders", "phase1.lims.sample_tracking"}
        )
        assert policy.approved_tenant_ids == frozenset({7, 12})

    def test_unknown_capability_is_rejected_even_if_tenant_has_entitlement(self) -> None:
        decision = decide_release_capability(
            "phase1.ai.interpretation",
            7,
            FAKE_DB,
            enabled_policy(),
            entitlement_resolver=entitled,
        )

        assert decision.allowed is False
        assert decision.reason == "unknown_capability"

    def test_emergency_kill_switch_overrides_release_and_subscription(self) -> None:
        policy = ReleasePolicyConfig(
            enabled_capability_keys=ALL_PHASE1,
            emergency_disabled_capability_keys=frozenset({"phase1.lims.result_entry"}),
            approved_tenant_ids=frozenset({7}),
        )

        decision = decide_release_capability(
            "phase1.lims.result_entry",
            7,
            FAKE_DB,
            policy,
            entitlement_resolver=entitled,
        )

        assert decision.allowed is False
        assert decision.reason == "emergency_kill_switch"

    def test_clinical_capability_requires_named_tenant_approval(self) -> None:
        decision = decide_release_capability(
            "phase1.lims.result_entry",
            8,
            FAKE_DB,
            enabled_policy(approved_tenant_ids=frozenset({7})),
            entitlement_resolver=entitled,
        )

        assert decision.allowed is False
        assert decision.reason == "tenant_approval_required"

    def test_dependency_must_be_enabled_before_result_entry(self) -> None:
        policy = ReleasePolicyConfig(
            enabled_capability_keys=frozenset({"phase1.lims.result_entry"}),
            approved_tenant_ids=frozenset({7}),
        )

        decision = decide_release_capability(
            "phase1.lims.result_entry",
            7,
            FAKE_DB,
            policy,
            entitlement_resolver=entitled,
        )

        assert decision.allowed is False
        assert decision.reason == "dependency_not_available"

    def test_subscription_entitlement_is_checked_after_release_policy(self) -> None:
        decision = decide_release_capability(
            "phase1.patient_registry",
            7,
            FAKE_DB,
            enabled_policy(),
            entitlement_resolver=denied_entitlement,
        )

        assert decision.allowed is False
        assert decision.reason == "subscription_entitlement_required"

    def test_fully_approved_and_entitled_capability_is_allowed(self) -> None:
        decision = decide_release_capability(
            "phase1.lims.critical_alerts",
            7,
            FAKE_DB,
            enabled_policy(),
            entitlement_resolver=entitled,
        )

        assert decision.allowed is True
        assert decision.reason == "allowed"

    def test_require_release_capability_returns_structured_safe_denial(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def deny(*_args: object, **_kwargs: object) -> CapabilityDecision:
            return CapabilityDecision(
                capability_key="phase1.identity",
                allowed=False,
                reason="emergency_kill_switch",
                policy_version="test-policy-v1",
            )

        monkeypatch.setattr("app.core.release_capabilities.decide_release_capability", deny)

        with pytest.raises(HTTPException) as exc_info:
            require_release_capability(
                "phase1.identity",
                7,
                FAKE_DB,
                ReleasePolicyConfig(),
            )

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["error"] == "release_capability_not_available"
        assert exc_info.value.detail["reason"] == "emergency_kill_switch"
        assert exc_info.value.detail["policy_version"] == "test-policy-v1"
