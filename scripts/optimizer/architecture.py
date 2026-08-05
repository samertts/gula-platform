"""Phase 3 — Architecture Optimization.

Recommend architecture improvements without violating the Constitution:
module boundaries, dependency reduction, caching, indexing, async
processing, lazy loading, code splitting, compression, queue optimization,
and database optimization. Recommendations are deterministic, derived from
evidence, and never change functional requirements — they improve
implementation quality only.
"""

from __future__ import annotations

from pathlib import Path

from scripts.kernel.core import utcnow
from scripts.optimizer.core import (
    ARCHITECTURE_TECHNIQUES,
    STATE_DIR,
    ArchitectureRecommendation,
    read_json,
    write_json,
)

ARCH_PATH = STATE_DIR / "architecture.json"

# Technique -> (rationale, expected impact).
TECHNIQUE_GUIDANCE: dict[str, tuple[str, str]] = {
    "module-boundaries": (
        "Keep Clean Architecture and DDD: modules depend inward, never on "
        "bounded-context siblings.",
        "Lower coupling, clearer ownership, smaller review surfaces.",
    ),
    "dependency-reduction": (
        "Prune unused and duplicated dependencies; prefer standard library.",
        "Smaller images, fewer CVEs, faster installs.",
    ),
    "caching": (
        "Cache hot, read-heavy data with an invalidation policy.",
        "Lower latency, fewer database hits, steadier load.",
    ),
    "indexing": (
        "Add indexes that match the actual query patterns.",
        "Faster lookups and sorted scans on large tables.",
    ),
    "async-processing": (
        "Move non-critical work onto the event bus and task queues.",
        "Responsive APIs and decoupled workers.",
    ),
    "lazy-loading": (
        "Import heavy frontend modules only when the route is visited.",
        "Smaller initial bundle, faster first paint.",
    ),
    "code-splitting": (
        "Split the bundle by route and feature instead of shipping one blob.",
        "Cacheable chunks and reduced initial transfer.",
    ),
    "compression": (
        "Enable gzip/brotli on the proxy and compress API payloads.",
        "Lower bandwidth and faster transfers.",
    ),
    "queue-optimization": (
        "Bound queue sizes, retries, and worker concurrency to the infrastructure.",
        "Predictable backpressure and no worker saturation.",
    ),
    "database-optimization": (
        "Avoid N+1, batch writes, and keep transactions short.",
        "Fewer round trips and lower lock contention.",
    ),
}


def recommend_architecture(areas: list[str] | None = None) -> list[ArchitectureRecommendation]:
    """Generate a deterministic architecture recommendation per technique.

    When no areas are given, every technique receives a recommendation for
    the area it most naturally belongs to.
    """
    areas = [a for a in (areas or []) if a]
    recommendations: list[ArchitectureRecommendation] = []
    for index, technique in enumerate(ARCHITECTURE_TECHNIQUES):
        rationale, impact = TECHNIQUE_GUIDANCE.get(technique, ("", ""))
        area = areas[index % len(areas)] if areas else _default_area(technique)
        recommendations.append(ArchitectureRecommendation(
            recommendation_id=f"ARC-{index + 1:06d}",
            technique=technique,
            area=area,
            rationale=rationale,
            expected_impact=impact,
        ))
    return recommendations


def persist_architecture(recommendations: list[ArchitectureRecommendation]) -> Path:
    payload = {
        "recommendations": [r.to_dict() for r in recommendations],
        "updated_at": utcnow(),
    }
    write_json(ARCH_PATH, payload)
    return ARCH_PATH


def load_architecture() -> list[ArchitectureRecommendation]:
    data = read_json(ARCH_PATH)
    return [
        ArchitectureRecommendation(**item)
        for item in data.get("recommendations", [])
    ]


def _default_area(technique: str) -> str:
    mapping = {
        "module-boundaries": "backend",
        "dependency-reduction": "backend",
        "caching": "backend",
        "indexing": "database",
        "async-processing": "backend",
        "lazy-loading": "frontend",
        "code-splitting": "frontend",
        "compression": "infrastructure",
        "queue-optimization": "infrastructure",
        "database-optimization": "database",
    }
    return mapping.get(technique, "backend")
