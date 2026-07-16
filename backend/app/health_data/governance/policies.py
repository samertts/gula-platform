from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app._compat import UTC
from app.health_data.enums import DataClassification

logger = logging.getLogger("gula.health_data.governance.policies")


class PolicyEffect(Enum):
    ALLOW = "allow"
    DENY = "deny"
    AUDIT = "audit"
    MASK = "mask"
    ANONYMIZE = "anonymize"


class PolicyScope(Enum):
    GLOBAL = "global"
    TENANT = "tenant"
    DATASET = "dataset"
    FIELD = "field"


@dataclass
class GovernancePolicy:
    id: str
    name: str
    description: str = ""
    scope: PolicyScope = PolicyScope.GLOBAL
    effect: PolicyEffect = PolicyEffect.AUDIT
    classification: DataClassification | None = None
    conditions: dict[str, Any] = field(default_factory=dict)
    priority: int = 100
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class RetentionPolicy(GovernancePolicy):
    retention_days: int = 365
    archive_after_days: int = 90
    delete_after_days: int = 365
    storage_tier_transition: list[dict] = field(default_factory=list)


@dataclass
class AccessPolicy(GovernancePolicy):
    allowed_roles: list[str] = field(default_factory=list)
    allowed_purposes: list[str] = field(default_factory=list)
    require_consent: bool = False
    require_break_glass: bool = False
    mfa_required: bool = False


@dataclass
class ConsentPolicy(GovernancePolicy):
    consent_scope: str = "patient_care"
    opt_out_allowed: bool = True
    consent_duration_days: int = 365
    share_with_third_party: bool = False


class PolicyEngine:
    def __init__(self):
        self._policies: dict[str, GovernancePolicy] = {}

    def add(self, policy: GovernancePolicy) -> None:
        self._policies[policy.id] = policy
        logger.info("Policy added: %s (%s)", policy.name, policy.effect.value)

    def remove(self, policy_id: str) -> bool:
        if policy_id in self._policies:
            del self._policies[policy_id]
            logger.info("Policy removed: %s", policy_id)
            return True
        return False

    def get(self, policy_id: str) -> GovernancePolicy | None:
        return self._policies.get(policy_id)

    def list(self, scope: PolicyScope | None = None) -> list[GovernancePolicy]:
        pols = list(self._policies.values())
        if scope:
            pols = [p for p in pols if p.scope == scope]
        return sorted(pols, key=lambda p: p.priority)

    def evaluate(
        self,
        classification: DataClassification,
        role: str,
        purpose: str,
        dataset: str = "",
        tenant_id: str = "",
    ) -> tuple[PolicyEffect, str]:
        applicable = sorted(
            [p for p in self._policies.values() if p.enabled],
            key=lambda p: p.priority,
        )

        for policy in applicable:
            if policy.classification and policy.classification != classification:
                continue
            if isinstance(policy, AccessPolicy):
                if policy.allowed_roles and role not in policy.allowed_roles:
                    return PolicyEffect.DENY, f"Role {role} not in allowed roles for policy {policy.name}"
                if policy.allowed_purposes and purpose not in policy.allowed_purposes:
                    return PolicyEffect.DENY, f"Purpose {purpose} not allowed by policy {policy.name}"

            if isinstance(policy, ConsentPolicy) and policy.opt_out_allowed:
                pass

            if policy.effect == PolicyEffect.DENY:
                return PolicyEffect.DENY, f"Denied by policy {policy.name}"

        return PolicyEffect.ALLOW, "Allowed by all applicable policies"
