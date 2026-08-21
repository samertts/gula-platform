"""Phase-1 release capability policy.

This module is deliberately separate from subscription entitlements.  A tenant
subscription may grant a commercial feature, but it must never override the
release scope, an emergency kill switch, a capability dependency, or a
per-tenant clinical approval.

Route handlers must use ``require_release_capability`` before invoking a
clinical service.  Client-side visibility is advisory only; this module is the
server-side source of the release decision.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.feature_flags import can_lab_access

logger = logging.getLogger("gula.release_capabilities")

CapabilityRisk = Literal["core", "clinical", "external", "experimental"]
DecisionReason = Literal[
    "allowed",
    "unknown_capability",
    "not_enabled_for_release",
    "emergency_kill_switch",
    "tenant_approval_required",
    "dependency_not_available",
    "subscription_entitlement_required",
]
EntitlementResolver = Callable[[str, int, Session], bool]


@dataclass(frozen=True)
class CapabilityDefinition:
    """A capability that may be exposed by a named release policy."""

    key: str
    entitlement_key: str | None
    risk: CapabilityRisk
    dependencies: tuple[str, ...] = ()
    requires_tenant_approval: bool = False


@dataclass(frozen=True)
class ReleasePolicyConfig:
    """Immutable, environment-scoped input to a release decision.

    An empty ``enabled_capability_keys`` is intentional: deployments fail
    closed until a reviewed release policy enables an explicit capability.
    """

    release_name: str = "phase1"
    policy_version: str = "phase1-default-deny-v1"
    enabled_capability_keys: frozenset[str] = field(default_factory=frozenset)
    emergency_disabled_capability_keys: frozenset[str] = field(default_factory=frozenset)
    approved_tenant_ids: frozenset[int] = field(default_factory=frozenset)


@dataclass(frozen=True)
class CapabilityDecision:
    capability_key: str
    allowed: bool
    reason: DecisionReason
    policy_version: str


# This is the only allowlist candidate for phase 1.  It does not enable a
# feature; an explicit ReleasePolicyConfig and (where applicable) an approved
# tenant are both required.
PHASE1_CAPABILITIES: dict[str, CapabilityDefinition] = {
    "phase1.identity": CapabilityDefinition(
        key="phase1.identity",
        entitlement_key=None,
        risk="core",
    ),
    "phase1.patient_registry": CapabilityDefinition(
        key="phase1.patient_registry",
        entitlement_key="patient_management",
        risk="clinical",
        requires_tenant_approval=True,
    ),
    "phase1.lims.orders": CapabilityDefinition(
        key="phase1.lims.orders",
        entitlement_key="sample_tracking",
        risk="clinical",
        requires_tenant_approval=True,
    ),
    "phase1.lims.sample_tracking": CapabilityDefinition(
        key="phase1.lims.sample_tracking",
        entitlement_key="sample_tracking",
        dependencies=("phase1.lims.orders",),
        risk="clinical",
        requires_tenant_approval=True,
    ),
    "phase1.lims.result_entry": CapabilityDefinition(
        key="phase1.lims.result_entry",
        entitlement_key="basic_results",
        dependencies=("phase1.lims.sample_tracking",),
        risk="clinical",
        requires_tenant_approval=True,
    ),
    "phase1.lims.result_approval": CapabilityDefinition(
        key="phase1.lims.result_approval",
        entitlement_key="basic_results",
        dependencies=("phase1.lims.result_entry",),
        risk="clinical",
        requires_tenant_approval=True,
    ),
    "phase1.lims.critical_alerts": CapabilityDefinition(
        key="phase1.lims.critical_alerts",
        entitlement_key="critical_alerts",
        dependencies=("phase1.lims.result_approval",),
        risk="clinical",
        requires_tenant_approval=True,
    ),
    "phase1.citizen.results_read": CapabilityDefinition(
        key="phase1.citizen.results_read",
        entitlement_key="mobile_access",
        dependencies=("phase1.lims.result_approval",),
        risk="clinical",
        requires_tenant_approval=True,
    ),
}


def decide_release_capability(
    capability_key: str,
    lab_id: int,
    db: Session,
    policy: ReleasePolicyConfig,
    *,
    entitlement_resolver: EntitlementResolver = can_lab_access,
) -> CapabilityDecision:
    """Return a fail-closed server-side release decision for one tenant."""

    return _decide_release_capability(
        capability_key,
        lab_id,
        db,
        policy,
        entitlement_resolver=entitlement_resolver,
        visited=frozenset(),
    )


def _decide_release_capability(
    capability_key: str,
    lab_id: int,
    db: Session,
    policy: ReleasePolicyConfig,
    *,
    entitlement_resolver: EntitlementResolver,
    visited: frozenset[str],
) -> CapabilityDecision:
    definition = PHASE1_CAPABILITIES.get(capability_key)
    if definition is None or capability_key in visited:
        return CapabilityDecision(
            capability_key=capability_key,
            allowed=False,
            reason="unknown_capability",
            policy_version=policy.policy_version,
        )

    if capability_key not in policy.enabled_capability_keys:
        return CapabilityDecision(
            capability_key=capability_key,
            allowed=False,
            reason="not_enabled_for_release",
            policy_version=policy.policy_version,
        )

    if capability_key in policy.emergency_disabled_capability_keys:
        return CapabilityDecision(
            capability_key=capability_key,
            allowed=False,
            reason="emergency_kill_switch",
            policy_version=policy.policy_version,
        )

    if definition.requires_tenant_approval and lab_id not in policy.approved_tenant_ids:
        return CapabilityDecision(
            capability_key=capability_key,
            allowed=False,
            reason="tenant_approval_required",
            policy_version=policy.policy_version,
        )

    for dependency_key in definition.dependencies:
        dependency = _decide_release_capability(
            dependency_key,
            lab_id,
            db,
            policy,
            entitlement_resolver=entitlement_resolver,
            visited=visited | {capability_key},
        )
        if not dependency.allowed:
            return CapabilityDecision(
                capability_key=capability_key,
                allowed=False,
                reason="dependency_not_available",
                policy_version=policy.policy_version,
            )

    if definition.entitlement_key and not entitlement_resolver(definition.entitlement_key, lab_id, db):
        return CapabilityDecision(
            capability_key=capability_key,
            allowed=False,
            reason="subscription_entitlement_required",
            policy_version=policy.policy_version,
        )

    return CapabilityDecision(
        capability_key=capability_key,
        allowed=True,
        reason="allowed",
        policy_version=policy.policy_version,
    )


def require_release_capability(
    capability_key: str,
    lab_id: int,
    db: Session,
    policy: ReleasePolicyConfig,
) -> None:
    """Reject an unavailable release capability before the route handler runs."""

    decision = decide_release_capability(capability_key, lab_id, db, policy)
    if decision.allowed:
        return

    logger.warning(
        "release capability denied capability=%s reason=%s policy_version=%s",
        capability_key,
        decision.reason,
        decision.policy_version,
    )
    raise HTTPException(
        status_code=403,
        detail={
            "error": "release_capability_not_available",
            "capability": capability_key,
            "reason": decision.reason,
            "policy_version": decision.policy_version,
            "message": "This capability is not available in the current release policy.",
            "message_ar": "هذه القدرة غير متاحة في سياسة الإصدار الحالية.",
        },
    )
