"""Phase 2 — Mission Router.

Before starting any mission, determine its type, size, risk, complexity, and
the required engines. Never execute unnecessary engines. Small missions run a
minimal pipeline; large features run the full governance pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass

from .core import Mission

MISSION_TYPES = {
    "tiny_bug": "tiny bug",
    "bug": "bug fix",
    "infrastructure": "infrastructure change",
    "feature": "large feature",
    "docs": "documentation",
    "security": "security change",
    "maintenance": "maintenance/refactor",
}

# A tiny bug only needs Builder + Reviewer, then done.
TINY_BUG_ENGINES = ["builder", "reviewer"]
INFRASTRUCTURE_ENGINES = ["architect", "builder", "reviewer", "deployer"]
LARGE_FEATURE_ENGINES = ["architect", "orchestrator", "builder", "reviewer", "learner", "optimizer"]
SECURITY_ENGINES = ["architect", "builder", "reviewer", "deployer"]
DOCS_ENGINES = ["builder", "reviewer"]
MAINTENANCE_ENGINES = ["architect", "builder", "reviewer"]


@dataclass(frozen=True)
class MissionProfile:
    """A pre-classified mission ready for routing."""

    mission: Mission
    mission_type: str
    size: str
    risk: str
    complexity: int


def classify(
    mission_id: str,
    name: str,
    mission_type: str,
    size: str = "small",
    risk: str = "low",
    complexity: int = 1,
    **kwargs: object,
) -> MissionProfile:
    """Classify a mission by type, size, risk, and complexity."""
    mtype = mission_type.strip().lower()
    msize = size.strip().lower()
    mrisk = risk.strip().lower()
    mcomplexity = max(1, min(10, int(complexity)))

    engines = route_engines(mtype, msize, mrisk, mcomplexity)
    reason = _routing_reason(mtype, msize, mrisk, mcomplexity)
    mission = Mission(
        mission_id=mission_id,
        name=name,
        mission_type=mtype,
        size=msize,
        risk=mrisk,
        complexity=mcomplexity,
        required_engines=engines,
        reason=reason,
    )
    return MissionProfile(mission=mission, mission_type=mtype, size=msize,
                          risk=mrisk, complexity=mcomplexity)


def route_engines(mission_type: str, size: str, risk: str, complexity: int) -> list[str]:
    """Determine the minimum required engine pipeline for a mission.

    Rules:
      - Tiny bug (or small size + low risk + low complexity): Builder, Reviewer.
      - Infrastructure change: Architect, Builder, Reviewer, Deployer.
      - Security change: Architect, Builder, Reviewer, Deployer.
      - Large feature (feature type, or size large/xl): full pipeline incl.
        Orchestrator, Learner, Optimizer.
      - Anything else: Architect, Builder, Reviewer.
    """
    mtype = mission_type.strip().lower()
    size = size.strip().lower()
    risk = risk.strip().lower()

    if mtype == "infrastructure":
        return list(INFRASTRUCTURE_ENGINES)
    if mtype == "security":
        return list(SECURITY_ENGINES)
    if mtype == "docs":
        return list(DOCS_ENGINES)
    if mtype == "maintenance":
        return list(MAINTENANCE_ENGINES)
    if mtype == "feature" or size in ("large", "xl") or complexity >= 7 or risk == "critical":
        return list(LARGE_FEATURE_ENGINES)
    if mtype in ("tiny_bug",) or (size in ("tiny", "small") and risk == "low" and complexity <= 2):
        return list(TINY_BUG_ENGINES)
    return ["architect", "builder", "reviewer"]


def _routing_reason(mtype: str, size: str, risk: str, complexity: int) -> str:
    if mtype == "infrastructure":
        return "Infrastructure change requires Architect design, deployment approval"
    if mtype == "security":
        return "Security change requires Architect, Reviewer, and Deployer"
    if mtype == "docs":
        return "Documentation change: minimal pipeline"
    if mtype == "maintenance":
        return "Maintenance/refactor requires architecture supervision"
    if mtype == "feature" or size in ("large", "xl") or complexity >= 7 or risk == "critical":
        return "Large feature: full governance pipeline incl. orchestration, learning, optimization"
    if mtype in ("tiny_bug",) or (size in ("tiny", "small") and risk == "low" and complexity <= 2):
        return "Tiny scope: Builder + Reviewer only, no unnecessary engines"
    return "Standard change: Architect + Builder + Reviewer"
