"""PROGRAM-BETA-COMMIT-0.2 — Architecture Policy Engine package (ADR-027).

The default registry ships with the Dormancy Policy enabled (the first
implemented policy) and the nine canonical future policies registered but
disabled. ``POLICY_CATALOG`` is the authoritative, ordered list of every
governance policy the platform recognizes; a lockstep test keeps the
registry names identical to it.
"""

from __future__ import annotations

from app.domain_platform.policies.core import (
    POLICY_ENGINE_VERSION,
    Policy,
    PolicyBaseline,
    PolicyContext,
    PolicyEngine,
    PolicyFinding,
    PolicyRegistry,
    PolicyReport,
    PolicyResult,
    PolicySeverity,
    PolicyStatus,
    PolicyWaiver,
    compute_status,
)
from app.domain_platform.policies.dormancy_policy import DormancyPolicy
from app.domain_platform.policies.future import FUTURE_POLICIES

# The canonical governance catalog (ADR-027). Ordered alphabetically by name
# = the canonical run order; a lockstep test keeps the registry names
# identical to it.
POLICY_CATALOG: tuple[str, ...] = (
    "api_governance_policy",
    "cross_domain_communication_policy",
    "data_governance_policy",
    "dependency_policy",
    "domain_ownership_policy",
    "dormancy_policy",
    "lifecycle_policy",
    "production_readiness_policy",
    "security_policy",
    "shared_core_policy",
)


def build_default_registry() -> PolicyRegistry:
    """The standard registry: Dormancy Policy enabled, nine futures disabled."""
    registry = PolicyRegistry()
    registry.register(DormancyPolicy())
    for policy in FUTURE_POLICIES:
        registry.register(policy)
    return registry


__all__ = [
    "POLICY_CATALOG",
    "POLICY_ENGINE_VERSION",
    "Policy",
    "PolicyBaseline",
    "PolicyContext",
    "PolicyEngine",
    "PolicyFinding",
    "PolicyRegistry",
    "PolicyReport",
    "PolicyResult",
    "PolicySeverity",
    "PolicyStatus",
    "PolicyWaiver",
    "build_default_registry",
    "compute_status",
]
