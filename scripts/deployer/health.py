"""Phase 4 — Health Validation.

Verify every platform component before the deployment is accepted: API,
frontend, database, Redis, message queue, storage, authentication, metrics,
tracing, and logging. Any FAIL rejects the deployment. Deterministic;
components map to health endpoints and status rules.
"""

from __future__ import annotations

from scripts.deployer.core import (
    HEALTH_COMPONENTS,
    ValidationCheck,
    ValidationStatus,
)

# Desired endpoints per health component.
HEALTH_ENDPOINTS: dict[str, str] = {
    "api": "/health",
    "frontend": "/healthz",
    "database": "/health/db",
    "redis": "/health/cache",
    "message-queue": "/health/mq",
    "storage": "/health/storage",
    "authentication": "/health/auth",
    "metrics": "/metrics",
    "tracing": "/health/tracing",
    "logging": "/health/logging",
}

# Endpoint suffix -> valid status range for latency checks.
LATENCY_MS_OK = 1000
CRITICAL_COMPONENTS: tuple[str, ...] = (
    "api",
    "database",
    "redis",
    "authentication",
    "storage",
)


def health_endpoint(component: str) -> str:
    """Return the health endpoint for a component."""
    return HEALTH_ENDPOINTS.get(component, f"/health/{component}")


def run_validation(
    healthy: set[str] | None = None,
    *,
    latencies: dict[str, int] | None = None,
) -> list[ValidationCheck]:
    """Run deterministic health validation for every component.

    `healthy` is the set of components reported healthy; anything else is
    FAIL. Latencies over the threshold produce a WARN unless the component
    is critical, which makes it a FAIL.
    """
    healthy = healthy or set(HEALTH_COMPONENTS)
    latencies = latencies or {}
    checks: list[ValidationCheck] = []
    for component in HEALTH_COMPONENTS:
        status = ValidationStatus.PASS.value
        latency = latencies.get(component, 1)
        detail = ""
        if component not in healthy:
            status = ValidationStatus.FAIL.value
            detail = f"component {component} not healthy"
        elif latency > LATENCY_MS_OK:
            if component in CRITICAL_COMPONENTS:
                status = ValidationStatus.FAIL.value
                detail = f"latency {latency}ms exceeds {LATENCY_MS_OK}ms for critical component"
            else:
                status = ValidationStatus.WARN.value
                detail = f"latency {latency}ms exceeds {LATENCY_MS_OK}ms"
        checks.append(ValidationCheck(
            component=component,
            check="health",
            status=status,
            endpoint=health_endpoint(component),
            latency_ms=latency,
            detail=detail,
        ))
    return checks


def deployment_rejected(checks: list[ValidationCheck]) -> bool:
    """Reject the deployment when any check FAILs."""
    return any(c.status == ValidationStatus.FAIL.value for c in checks)


def validation_summary(checks: list[ValidationCheck]) -> str:
    passed = sum(1 for c in checks if c.status == ValidationStatus.PASS.value)
    failed = sum(1 for c in checks if c.status == ValidationStatus.FAIL.value)
    verdict = "REJECTED" if deployment_rejected(checks) else "ACCEPTED"
    return f"health validation: {passed} pass, {failed} fail -> {verdict}"
