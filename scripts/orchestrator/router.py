"""Phase 3 — Engineering Router.

Automatically assign every task to the engine that owns its surface:
backend/frontend/database/architecture/security/testing -> Builder,
deployment/infrastructure -> Deployer, verification -> Reviewer,
knowledge/documentation/research -> Learner, optimization/observability
-> Optimizer. Never assign unrelated work. Fallback engine for absent
engines is recorded as a routing decision.
"""

from __future__ import annotations

from scripts.orchestrator.core import (
    SURFACE_ROUTING,
    OrchestratedPlan,
)


def _fallback_engine(engine: str, available: set[str]) -> str:
    """Map to the closest available engine when the target is absent."""
    if engine in available:
        return engine
    fallbacks: dict[str, tuple[str, ...]] = {
        "deployer": ("builder", "kernel"),
        "optimizer": ("builder", "reviewer"),
        "learner": ("kernel",),
        "reviewer": ("kernel",),
        "builder": ("kernel",),
    }
    for candidate in fallbacks.get(engine, ()):
        if candidate in available:
            return candidate
    return "kernel"


def route_plan(
    plan: OrchestratedPlan,
    *,
    available: set[str] | None = None,
) -> OrchestratedPlan:
    """Assign an engine to every unassigned task based on its surface.

    When `available` is given, absent engines are replaced with the closest
    available engine and the substitution is recorded in the task name is not
    changed; evidence captures the fallback.
    """
    available = available or set(SURFACE_ROUTING.values()) | {"kernel"}
    for task in plan.tasks:
        if task.engine:
            continue
        preferred = SURFACE_ROUTING.get(task.surface, "kernel")
        assigned = _fallback_engine(preferred, available)
        task.engine = assigned
        if assigned != preferred:
            task.evidence = f"fallback:{preferred}->{assigned}"
    return plan


def routing_summary(plan: OrchestratedPlan) -> dict[str, int]:
    """Count tasks assigned to each engine."""
    summary: dict[str, int] = {}
    for task in plan.tasks:
        summary[task.engine] = summary.get(task.engine, 0) + 1
    return summary


def routing_decisions(plan: OrchestratedPlan) -> list[dict[str, str]]:
    """Record each fallback routing decision for the decision log."""
    decisions: list[dict[str, str]] = []
    for task in plan.tasks:
        if task.evidence:
            decisions.append({
                "task_id": task.task_id,
                "name": task.name,
                "evidence": task.evidence,
            })
    return decisions
