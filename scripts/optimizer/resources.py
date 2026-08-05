"""Phase 4 — Resource Optimization.

Optimize infrastructure resources without changing behavior: Docker images,
containers, volumes, Redis, PostgreSQL, RabbitMQ, MinIO, worker usage,
background tasks, and infrastructure cost. Every recommendation targets a
specific resource, names the saving type, and stays within the platform's
self-hosted, no-vendor-lock-in, free-first constitution.
"""

from __future__ import annotations

from pathlib import Path

from scripts.kernel.core import utcnow
from scripts.optimizer.core import (
    RESOURCE_TARGETS,
    STATE_DIR,
    ResourceRecommendation,
    read_json,
    write_json,
)

RESOURCES_PATH = STATE_DIR / "resources.json"

# Target -> (saving type, recommendation).
RESOURCE_GUIDANCE: dict[str, tuple[str, str]] = {
    "docker-images": (
        "image-size",
        "Use slim Python 3.12 base images, multi-stage builds, and "
        "`.dockerignore` to keep images small and layer-friendly.",
    ),
    "containers": (
        "memory",
        "Pin CPU/memory limits per container and run as non-root with a "
        "HEALTHCHECK so scheduler placement is predictable.",
    ),
    "volumes": (
        "storage",
        "Right-size named volumes, prune orphaned volumes, and move cold "
        "artifacts to MinIO object storage.",
    ),
    "redis": (
        "memory",
        "Enable Redis eviction policies, cap cache keys, and use lazy "
        "initialization so Redis failures degrade gracefully.",
    ),
    "postgresql": (
        "cpu",
        "Add matching indexes, bound connection pools, and use `autovacuum` "
        "tuning before adding hardware.",
    ),
    "rabbitmq": (
        "memory",
        "Bound queue lengths, set TTLs on dead-letter queues, and enforce "
        "consumer prefetch limits.",
    ),
    "minio": (
        "storage",
        "Apply lifecycle policies to archive old objects and enable "
        "compression for cold buckets.",
    ),
    "worker-usage": (
        "cpu",
        "Size worker concurrency to the queue depth instead of the host "
        "core count; pause idle workers.",
    ),
    "background-tasks": (
        "cpu",
        "Schedule heavy background jobs off-peak and use the bounded queue "
        "instead of unbounded fan-out.",
    ),
    "infrastructure-cost": (
        "cost",
        "Prefer self-hosted free-first components, prune unused resources, "
        "and right-size before scaling out.",
    ),
}


def recommend_resources(targets: list[str] | None = None) -> list[ResourceRecommendation]:
    """Generate a deterministic resource recommendation per target."""
    targets = [t for t in (targets or []) if t]
    chosen = [t for t in targets if t in RESOURCE_TARGETS] or list(RESOURCE_TARGETS)
    recommendations: list[ResourceRecommendation] = []
    for index, target in enumerate(chosen):
        saving_type, recommendation = RESOURCE_GUIDANCE.get(
            target, ("", "Review the resource for waste.")
        )
        recommendations.append(ResourceRecommendation(
            resource_id=f"RES-{index + 1:06d}",
            target=target,
            area=_area(target),
            saving_type=saving_type,
            recommendation=recommendation,
        ))
    return recommendations


def persist_resources(recommendations: list[ResourceRecommendation]) -> Path:
    payload = {
        "recommendations": [r.to_dict() for r in recommendations],
        "updated_at": utcnow(),
    }
    write_json(RESOURCES_PATH, payload)
    return RESOURCES_PATH


def load_resources() -> list[ResourceRecommendation]:
    data = read_json(RESOURCES_PATH)
    return [
        ResourceRecommendation(**item)
        for item in data.get("recommendations", [])
    ]


def _area(target: str) -> str:
    if target in {"docker-images", "containers", "volumes"}:
        return "docker"
    if target in {"redis", "postgresql", "rabbitmq", "minio"}:
        return "datastore"
    if target in {"worker-usage", "background-tasks"}:
        return "backend"
    return "infrastructure"
