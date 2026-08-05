"""Phase 7 — Future Simulation.

Project platform capacity from 100 to 1,000,000 users using explicit,
deterministic assumptions: active-user fraction, per-user daily request
volume, peak multiplier, cache footprint, and per-replica request capacity.
Exposes the assumptions in the report so they can be challenged and tuned.
"""

from __future__ import annotations

from pathlib import Path

from scripts.architect.core import (
    SCALE_STEPS,
    SIMULATION_DIR,
    ScaleProjection,
    write_json,
)
from scripts.kernel.core import utcnow

# Explicit, tunable assumptions behind every projection.
ACTIVE_USER_FRACTION = 0.10
REQUESTS_PER_ACTIVE_USER_PER_DAY = 50
PEAK_MULTIPLIER = 3.0
CACHE_BYTES_PER_USER = 50 * 1024
STORAGE_BYTES_PER_USER = 50 * 1024 * 1024
REQUESTS_PER_REPLICA_PER_SECOND = 500.0
BASE_DATABASE_CONNECTIONS = 20
CONNECTIONS_PER_REQUESTS_PER_SECOND = 4
REPLICA_MONTHLY_COST_USD = 50
STORAGE_MONTHLY_COST_PER_GB_USD = 0.05
CACHE_MONTHLY_COST_PER_GB_USD = 0.10

TIERS: dict[int, str] = {
    100: "single-node",
    1_000: "small-cluster",
    10_000: "regional",
    100_000: "multi-region",
    1_000_000: "national",
}

# Tier -> likely first bottleneck at that scale.
BOTTLENECKS: dict[str, str] = {
    "single-node": "CPU and memory headroom under peak clinical load",
    "small-cluster": "database connection pool saturation",
    "regional": "cache memory and analytics query load",
    "multi-region": "cross-governorate sync latency and partition handling",
    "national": "data residency, federation, and compliance across governorates",
}


def _tier(users: int) -> str:
    tier = "single-node"
    for step in SCALE_STEPS:
        if users >= step:
            tier = TIERS[step]
    return tier


def project_scale(users: int) -> ScaleProjection:
    """Project capacity, storage, and cost for a given user population."""
    active = users * ACTIVE_USER_FRACTION
    requests_per_second = round(
        active * REQUESTS_PER_ACTIVE_USER_PER_DAY / 86400 * PEAK_MULTIPLIER
    )
    database_connections = (
        BASE_DATABASE_CONNECTIONS
        + round(requests_per_second / CONNECTIONS_PER_REQUESTS_PER_SECOND)
    )
    cache_memory_gb = round(users * CACHE_BYTES_PER_USER / (1024**3), 2)
    storage_gb = round(users * STORAGE_BYTES_PER_USER / (1024**3), 1)
    app_replicas = max(1, int(requests_per_second / REQUESTS_PER_REPLICA_PER_SECOND) + 1)
    tier = _tier(users)
    monthly_cost_usd = round(
        app_replicas * REPLICA_MONTHLY_COST_USD
        + storage_gb * STORAGE_MONTHLY_COST_PER_GB_USD
        + cache_memory_gb * CACHE_MONTHLY_COST_PER_GB_USD
    )
    return ScaleProjection(
        users=users,
        requests_per_second=requests_per_second,
        database_connections=database_connections,
        cache_memory_gb=cache_memory_gb,
        storage_gb=storage_gb,
        monthly_cost_usd=monthly_cost_usd,
        app_replicas=app_replicas,
        tier=tier,
        predicted_bottleneck=BOTTLENECKS[tier],
        note=(
            "Assumes 10% active users, 50 requests/active-user/day, "
            "3x peak multiplier, 50 KB cache/user, 50 MB clinical "
            "storage/user, 500 requests/sec/replica."
        ),
    )


def project_full() -> list[ScaleProjection]:
    """Project every scale step deterministically."""
    return [project_scale(step) for step in SCALE_STEPS]


def persist_simulation() -> Path:
    """Persist the projections under state/simulation/."""
    projections = project_full()
    path = SIMULATION_DIR / "projections.json"
    write_json(path, {
        "discovered_at": utcnow(),
        "assumptions": {
            "active_user_fraction": ACTIVE_USER_FRACTION,
            "requests_per_active_user_per_day": REQUESTS_PER_ACTIVE_USER_PER_DAY,
            "peak_multiplier": PEAK_MULTIPLIER,
            "cache_bytes_per_user": CACHE_BYTES_PER_USER,
            "storage_bytes_per_user": STORAGE_BYTES_PER_USER,
            "requests_per_replica_per_second": REQUESTS_PER_REPLICA_PER_SECOND,
            "replica_monthly_cost_usd": REPLICA_MONTHLY_COST_USD,
        },
        "projections": [p.to_dict() for p in projections],
    })
    return path


def render_markdown(projections: list[ScaleProjection]) -> str:
    lines = [
        "# GULA-ARCHITECT-001 — Future Simulation",
        "",
        f"Generated: **{utcnow()}**",
        "",
        "Projections from 100 to 1,000,000 users with explicit assumptions: "
        "10% active fraction, 50 requests/active-user/day, 3x peak "
        "multiplier, 50 KB cache/user, 50 MB clinical storage/user, "
        "500 requests/sec/replica.",
        "",
        "| Users | Requests/s | DB connections | Cache (GB) | Storage (GB) | "
        "Replicas | Monthly cost | Tier |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for projection in projections:
        lines.append(
            f"| {projection.users:,} | {projection.requests_per_second} | "
            f"{projection.database_connections} | "
            f"{projection.cache_memory_gb} | {projection.storage_gb} | "
            f"{projection.app_replicas} | "
            f"${projection.monthly_cost_usd}/mo | {projection.tier} |"
        )
    lines.extend([
        "",
        "## Predicted Bottlenecks",
        "",
    ])
    for projection in projections:
        lines.append(
            f"- **{projection.users:,} users** ({projection.tier}): "
            f"{projection.predicted_bottleneck}"
        )
    lines.extend([
        "",
        "## Notes",
        "",
        "- The 1M-user projection remains within a single logical national "
        "platform: horizontal replica scaling, partitioned data stores, and "
        "cache sharding keep the architecture monolithic-first.",
        "- Assumptions are explicit and tunable; re-run "
        "`architect-simulation` after revisiting the assumptions.",
        "",
    ])
    return "\n".join(lines)
