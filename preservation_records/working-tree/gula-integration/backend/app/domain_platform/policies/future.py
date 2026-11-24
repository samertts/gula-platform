"""PROGRAM-BETA-COMMIT-0.2 — Future policies (ADR-027).

Nine canonical policies are registered in the default registry but
*disabled*. They expose the same :class:`Policy` interface and return a
deterministic ``skipped`` result if evaluated directly, yet the engine never
executes disabled policies — so enabling a future policy is a configuration
change (set ``enabled = True`` and implement ``evaluate``), never an engine
redesign.

No fake logic is shipped: these modules intentionally contain no rule
bodies. Each entry records the policy's scope so the report manifest always
documents the full governance catalog.
"""

from __future__ import annotations

from app.domain_platform.policies.core import (
    PolicyContext,
    PolicyResult,
    PolicyStatus,
)


class FuturePolicy:
    """Registered-but-disabled placeholder for a not-yet-implemented policy."""

    enabled = False

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    def evaluate(self, context: PolicyContext) -> PolicyResult:
        return PolicyResult(
            policy=self.name,
            status=PolicyStatus.SKIPPED,
            summary=(
                f"policy '{self.name}' is registered but not yet implemented "
                "(ADR-027); it stays disabled until a rule body is provided"
            ),
        )


LIFECYCLE_POLICY = FuturePolicy(
    "lifecycle_policy",
    "Domain lifecycle state machine compliance (install/activate/suspend/upgrade/rollback).",
)
DOMAIN_OWNERSHIP_POLICY = FuturePolicy(
    "domain_ownership_policy",
    "No Domain owns another Domain; ownership stays with Shared Core / platform.",
)
PRODUCTION_READINESS_POLICY = FuturePolicy(
    "production_readiness_policy",
    "Production-readiness gates: health, observability, deployment, DR, rollback.",
)
SHARED_CORE_POLICY = FuturePolicy(
    "shared_core_policy",
    "Shared Core usage 100%; zero reimplementation of canonical infrastructure.",
)
DEPENDENCY_POLICY = FuturePolicy(
    "dependency_policy",
    "Dependency graph rules: no circular dependencies, no skip-layer imports.",
)
CROSS_DOMAIN_COMMUNICATION_POLICY = FuturePolicy(
    "cross_domain_communication_policy",
    "Cross-domain traffic flows only through versioned contracts and the gateway.",
)
API_GOVERNANCE_POLICY = FuturePolicy(
    "api_governance_policy",
    "API contract governance: versioning, idempotency, OpenAPI validation, structured errors.",
)
SECURITY_POLICY = FuturePolicy(
    "security_policy",
    "Security posture: OWASP ASVS / API Top 10, secrets, encryption, least privilege.",
)
DATA_GOVERNANCE_POLICY = FuturePolicy(
    "data_governance_policy",
    "Data governance: retention, classification, auditability, immutable audit log.",
)

FUTURE_POLICIES: tuple[FuturePolicy, ...] = (
    LIFECYCLE_POLICY,
    DOMAIN_OWNERSHIP_POLICY,
    PRODUCTION_READINESS_POLICY,
    SHARED_CORE_POLICY,
    DEPENDENCY_POLICY,
    CROSS_DOMAIN_COMMUNICATION_POLICY,
    API_GOVERNANCE_POLICY,
    SECURITY_POLICY,
    DATA_GOVERNANCE_POLICY,
)
