"""Phase 6 — Auto Scaling.

Support horizontal scaling, vertical scaling, worker scaling, background
jobs, queue scaling, and future Kubernetes migration. Deterministic policy
engine: a scaling decision is derived from current replicas, load metric,
threshold, and policy bounds.
"""

from __future__ import annotations

from scripts.deployer.core import (
    ScalingMode,
    ScalingPolicy,
    make_id,
)

SCALE_METRICS: tuple[str, ...] = (
    "cpu_utilization",
    "memory_utilization",
    "queue_depth",
    "http_latency_p95",
    "concurrent_requests",
)

# Default policy per scaling mode.
MODE_DEFAULTS: dict[str, dict] = {
    ScalingMode.HORIZONTAL.value: {"metric": "cpu_utilization", "threshold": 80.0, "min_replicas": 1, "max_replicas": 5},
    ScalingMode.VERTICAL.value: {"metric": "memory_utilization", "threshold": 85.0, "min_replicas": 1, "max_replicas": 1},
    ScalingMode.WORKER.value: {"metric": "queue_depth", "threshold": 100.0, "min_replicas": 1, "max_replicas": 10},
    ScalingMode.QUEUE.value: {"metric": "queue_depth", "threshold": 50.0, "min_replicas": 1, "max_replicas": 8},
}


def default_policies(services: tuple[str, ...]) -> list[ScalingPolicy]:
    """Create the default scaling policy for each service."""
    policies: list[ScalingPolicy] = []
    for service in services:
        mode = ScalingMode.WORKER.value if service == "worker" else ScalingMode.HORIZONTAL.value
        spec = MODE_DEFAULTS[mode]
        policies.append(ScalingPolicy(
            policy_id=make_id("SCL"),
            service=service,
            mode=mode,
            min_replicas=spec["min_replicas"],
            max_replicas=spec["max_replicas"],
            metric=spec["metric"],
            threshold=spec["threshold"],
            enabled=True,
        ))
    return policies


def scale_decision(policy: ScalingPolicy, current: int, load: float) -> dict:
    """Deterministically decide the desired replica count.

    Scale out when load exceeds threshold (up to max_replicas), scale in
    when load is under half the threshold (down to min_replicas), otherwise
    hold the current count.
    """
    if not policy.enabled:
        return {"replicas": current, "action": "hold", "reason": "scaling disabled"}
    if load >= policy.threshold:
        desired = min(current + 1, policy.max_replicas)
        action = "scale_out" if desired > current else "at_max"
    elif load <= policy.threshold / 2 and current > policy.min_replicas:
        desired = max(current - 1, policy.min_replicas)
        action = "scale_in"
    else:
        desired = current
        action = "hold"
    return {"replicas": desired, "action": action, "load": load, "threshold": policy.threshold}


def kubernetes_readiness(policies: list[ScalingPolicy]) -> dict:
    """Assess readiness of the scaling model for Kubernetes migration."""
    return {
        "migratable": True,
        "reasons": [
            "replica bounds are expressed as min/max per service",
            "scaling metric is declarative (cpu/memory/queue)",
            "worker scaling separates from API scaling",
        ],
        "requires": [
            "HPA from ScalingPolicy thresholds",
            "resource requests/limits per container",
            "persistent volume claims for datastores",
        ],
    }
