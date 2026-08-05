"""Phase 4 — Evolution Planning.

Produce 1/3/5-year architecture roadmaps for the GULA national platform.
Each horizon carries concrete milestones, enabling capabilities, and the
risks they address. Persisted under state/evolution/.
"""

from __future__ import annotations

from pathlib import Path

from scripts.architect.core import (
    EVOLUTION_DIR,
    EVOLUTION_HORIZONS,
    RoadmapMilestone,
    write_json,
)
from scripts.kernel.core import utcnow

# Horizon -> milestone definitions.
# (horizon, title, scope, enabler, risk, technology, migration)
ROADMAP_MILESTONES: tuple[tuple[str, str, str, str, str, str, str], ...] = (
    (
        "1-year",
        "National pilot readiness",
        "Operationalize the national pilot: identity platform, FHIR R4 "
        "contracts, offline sync hardening, multi-tenant isolation proof.",
        "Existing monolith + deployer + reviewer",
        "Scope creep across governorate pilot sites",
        "Python 3.12, FastAPI, PostgreSQL 16, Redis — unchanged stack",
        "Feature-flag pilot rollout; no data migration",
    ),
    (
        "1-year",
        "Clinical safety certification",
        "ISO 15189, CAP, CLSI evidence packs automated and continuously "
        "validated by the quality gates.",
        "Compliance dashboards + regression gates",
        "Audit evidence drift",
        "Automated evidence collection tooling",
        "Additive compliance reports; existing data untouched",
    ),
    (
        "1-year",
        "Observability at national scale",
        "OpenTelemetry tracing, structured logs, and metrics across every "
        "surface; incident runbooks rehearsed.",
        "Deployer observability phase + self-healing",
        "Signal-to-noise ratio in operations",
        "OpenTelemetry OTLP -> Jaeger/Tempo (self-hosted)",
        "Gradual instrumentation; zero schema change",
    ),
    (
        "3-year",
        "Governorate rollout",
        "Multi-directorate deployment with Ministry hierarchy, regional "
        "data residency, and national event bus federation.",
        "Tenant-aware routing + event bus federation",
        "Data residency and latency across governorates",
        "Region-aware tenants, federation adapters",
        "Tenant-aware data routing with backward-compatible reads",
    ),
    (
        "3-year",
        "Analyzer integration network",
        "ASTM/HL7 device bridge standardization across laboratory hardware, "
        "with validation and audit of every result.",
        "Analyzer bridge + clinical safety validation",
        "Device protocol fragmentation",
        "ASTM/HL7 adapter framework",
        "Adapter per protocol; no core schema change",
    ),
    (
        "3-year",
        "National identity federation",
        "Citizen identity authority federated with national health "
        "platform; ABAC authorization at Ministry level.",
        "Identity platform + ABAC engine",
        "Privacy and consent across boundaries",
        "ABAC policy engine, federation gateway",
        "Claims-based identity mapping with rollback adapter",
    ),
    (
        "5-year",
        "National EHR interoperability",
        "Full FHIR R4 national EHR exchange; SNDHS government integration; "
        "cross-governorate continuity of care.",
        "National EHR + government gateways",
        "Specification drift with national standards",
        "National FHIR profiles, gateway services",
        "Canonical FHIR resource migration with dual-write window",
    ),
    (
        "5-year",
        "National intelligence platform",
        "Aggregated analytics and clinical intelligence across the national "
        "platform with strict privacy preservation.",
        "Analytics layer + privacy-preserving computation",
        "De-identification and consent governance",
        "OLAP read replicas, de-identification pipeline",
        "Read-model projections; source of truth unchanged",
    ),
    (
        "5-year",
        "Federated event mesh",
        "Fault-tolerant, self-hosted event mesh connecting every governorate "
        "deployment into one logical platform.",
        "Event bus federation + offline queues",
        "Network partition handling",
        "Federated event bus with durable queues",
        "Gradual federation; local queues remain authoritative",
    ),
)

# Cross-horizon scalability plan (Phase 4).
SCALABILITY_PLAN: tuple[tuple[str, str], ...] = (
    ("100-1k users", "Single node; vertical scaling; replicated app behind a load balancer."),
    ("1k-10k users", "Small cluster; Redis sharding; read replicas for analytics."),
    ("10k-100k users", "Regional deployments; partition data stores by governorate."),
    ("100k-1M users", "Multi-region federation; tenant-aware routing; event mesh."),
)

# Cross-horizon refactoring strategy (Phase 4).
REFACTORING_STRATEGY: tuple[str, ...] = (
    "Always preserve behavioral compatibility; refactor behind interfaces.",
    "One measured extraction at a time; never speculative service splits.",
    "Keep dormant modules mergeable into national releases.",
    "Enforce module boundaries with review gates, not process isolation.",
    "Eliminate circular dependencies before adding new abstractions.",
)


def build_roadmap() -> list[RoadmapMilestone]:
    """Build the evolution roadmap deterministically."""
    milestones = [
        RoadmapMilestone(
            horizon=horizon,
            title=title,
            scope=scope,
            enabler=enabler,
            risk=risk,
            technology=technology,
            migration=migration,
        )
        for horizon, title, scope, enabler, risk, technology, migration in ROADMAP_MILESTONES
    ]
    return sorted(milestones, key=lambda m: (m.horizon, m.title))


def persist_roadmap() -> Path:
    """Persist the roadmap under state/evolution/."""
    milestones = build_roadmap()
    path = EVOLUTION_DIR / "roadmap.json"
    write_json(path, {
        "discovered_at": utcnow(),
        "horizons": list(EVOLUTION_HORIZONS),
        "scalability_plan": [{"scale": s, "plan": p} for s, p in SCALABILITY_PLAN],
        "refactoring_strategy": list(REFACTORING_STRATEGY),
        "milestones": [m.to_dict() for m in milestones],
    })
    return path


def render_markdown(milestones: list[RoadmapMilestone]) -> str:
    lines = [
        "# GULA-ARCHITECT-001 — Evolution Roadmap",
        "",
        f"Generated: **{utcnow()}**",
        "",
        f"**{len(milestones)} milestones** across "
        f"**{len(EVOLUTION_HORIZONS)} horizons**.",
        "",
        "| Horizon | Milestone | Technology evolution | Enabler | Key risk |",
        "|---|---|---|---|---|",
    ]
    for milestone in milestones:
        lines.append(
            f"| {milestone.horizon} | {milestone.title} | "
            f"{milestone.technology} | {milestone.enabler} | {milestone.risk} |"
        )
    lines.extend(["", "## Scope", ""])
    for milestone in milestones:
        lines.append(f"### {milestone.horizon} — {milestone.title}")
        lines.append("")
        lines.append(milestone.scope)
        lines.append("")
        lines.append(f"**Migration strategy:** {milestone.migration}")
        lines.append("")
    lines.extend([
        "",
        "## Scalability Plan",
        "",
        "| Scale | Plan |",
        "|---|---|",
    ])
    for scale, plan in SCALABILITY_PLAN:
        lines.append(f"| {scale} | {plan} |")
    lines.extend([
        "",
        "## Refactoring Strategy",
        "",
    ])
    for strategy in REFACTORING_STRATEGY:
        lines.append(f"- {strategy}")
    lines.append("")
    return "\n".join(lines)
