"""GULA-KERNEL-EXT-001 Phase 10 — Health Engine.

Platform-wide HEALTH / RISK / READINESS scoring over all Kernel
extensions. Composes the Kernel readiness components
(scripts/kernel/report.py readiness_components) and diagnostics; each
extension contributes weighted component health. Scores are
deterministic, weighted, and severity-aware. No I/O at import time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core import utcnow

HEALTH_DIR = ".ai/core/health/"

READINESS_THRESHOLD = 90.0


class HealthError(Exception):
    """Raised for invalid health inputs."""


@dataclass
class ComponentHealth:
    """One weighted health component."""

    name: str
    status: str  # "pass" | "fail"
    weight: float = 1.0
    critical: bool = False
    detail: str = ""

    def __post_init__(self) -> None:
        if self.status not in {"pass", "fail"}:
            raise HealthError(f"unknown status: {self.status!r}")
        if self.weight <= 0:
            raise HealthError("weight must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "weight": self.weight,
            "critical": self.critical,
            "detail": self.detail,
        }


@dataclass
class HealthReport:
    """HEALTH / RISK / READINESS scores over components."""

    health: float
    risk: float
    readiness: float
    components: list[ComponentHealth] = field(default_factory=list)
    generated_at: str = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "health": self.health,
            "risk": self.risk,
            "readiness": self.readiness,
            "generated_at": self.generated_at,
            "components": [c.to_dict() for c in self.components],
        }


def score_components(components: list[ComponentHealth]) -> HealthReport:
    """Weighted HEALTH/RISK/READINESS scoring."""
    if not components:
        raise HealthError("cannot score an empty component set")
    total = sum(c.weight for c in components)
    passing = sum(c.weight for c in components if c.status == "pass")
    failing = sum(c.weight for c in components if c.status == "fail")
    critical_fail = any(c.status == "fail" and c.critical for c in components)

    health = round(passing / total * 100.0, 1)
    risk = round(failing / total * 100.0, 1)
    readiness = round(health * (0.5 if critical_fail else 1.0), 1)
    return HealthReport(health=health, risk=risk, readiness=readiness, components=components)


def extension_health() -> HealthReport:
    """Score all extensions from live registry/engine state."""
    from ..core import ENGINE_REGISTRY
    from .compatibility import engine_matrix
    from .event_bus import Event, EventBus
    from .evolution import EvolutionEngine
    from .marketplace import CatalogItem, Marketplace
    from .memory import MemoryStore
    from .migration import MigrationEngine, _demo_plan
    from .plugin import PluginRegistry, manifest_from_engine
    from .policy import PolicyEngine, default_policies
    from .workflow import WorkflowEngine, _demo_workflow

    components: list[ComponentHealth] = []

    plugins = PluginRegistry()
    for name, meta in ENGINE_REGISTRY.items():
        plugins.register(manifest_from_engine(name, meta))
    components.append(ComponentHealth(
        "plugin_sdk", "pass" if len(plugins.list()) == len(ENGINE_REGISTRY) else "fail",
        critical=True, detail=f"{len(plugins.list())} plugins registered",
    ))

    policies = PolicyEngine()
    for policy in default_policies():
        policies.register(policy)
    components.append(ComponentHealth(
        "policy_engine", "pass" if len(policies.search()) else "fail",
        critical=True, detail=f"{len(policies.search())} policies",
    ))

    compat = engine_matrix(ENGINE_REGISTRY)
    components.append(ComponentHealth(
        "compatibility", "pass" if not compat.breaking() else "fail",
        critical=True, detail=f"{len(compat.entries('contract'))} contracts",
    ))

    migrations = MigrationEngine()
    plan = migrations.register(_demo_plan())
    migrations.execute(plan.id)
    components.append(ComponentHealth(
        "migration", "pass" if plan.state == "executed" else "fail",
        critical=True, detail=plan.state,
    ))

    bus = EventBus()
    bus.subscribe("*", "audit", lambda _ev: None)
    bus.publish(Event(id="EVT-000900", name="health.check", publisher="ext-health"))
    components.append(ComponentHealth(
        "event_bus", "pass" if not bus.failures() else "fail",
        critical=True, detail=f"{len(bus.events())} events, 0 failures",
    ))

    workflows = WorkflowEngine()
    demo = workflows.register(_demo_workflow())
    workflows.run(demo.id)
    workflows.approve(demo.id, "review")
    components.append(ComponentHealth(
        "workflow", "pass" if demo.state == "completed" else "fail",
        critical=True, detail=demo.state,
    ))

    marketplace = Marketplace()
    marketplace.add(CatalogItem("CAT-000001", "plugin", "governor-plugin", "1.0.0", "demo"))
    marketplace.install("CAT-000001")
    components.append(ComponentHealth(
        "marketplace", "pass" if marketplace.is_installed("CAT-000001") else "fail",
        critical=False, detail=f"{len(marketplace.installed())} installed",
    ))

    evolution = EvolutionEngine(threshold=2)
    evolution.record("repeated_fix", "imports", "a")
    evolution.record("repeated_fix", "imports", "b")
    components.append(ComponentHealth(
        "evolution", "pass" if evolution.detect() else "fail",
        critical=False, detail=f"{len(evolution.signals())} signals",
    ))

    memory = MemoryStore()
    entry = memory.remember("working", "health checkpoint", tags=["health"])
    memory.touch(entry.id)
    memory.touch(entry.id)
    memory.touch(entry.id)
    memory.promote(entry.id)
    components.append(ComponentHealth(
        "memory", "pass" if entry.tier == "long_term" else "fail",
        critical=False, detail=f"{len(memory.entries())} entries",
    ))

    return score_components(components)


def is_ready(report: HealthReport, threshold: float = READINESS_THRESHOLD) -> bool:
    """True when readiness meets the platform threshold."""
    return report.readiness >= threshold
