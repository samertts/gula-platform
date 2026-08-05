"""Phase 1 — Mission Classifier.

Automatically classify a single objective: type (12 kinds), priority,
complexity, risk, dependencies, expected duration, and required specialists.
Deterministic keyword scoring, no I/O at import time.
"""

from __future__ import annotations

import re

from scripts.orchestrator.core import (
    COMPLEXITY_LEVELS,
    DURATION_BY_COMPLEXITY,
    MISSION_KEYWORDS,
    MISSION_TYPE_NAMES,
    MISSION_TYPES,
    RISK_LEVELS,
    TYPE_COMPLEXITY,
    TYPE_RISK,
    MissionClassification,
)


def normalize(objective: str) -> str:
    """Collapse whitespace and casing for deterministic matching."""
    return re.sub(r"\s+", " ", objective.strip().lower())


def classify(objective: str, mission_id: str | None = None) -> MissionClassification:
    """Classify a single objective into a MissionClassification."""
    raw = normalize(objective)
    if not raw:
        raise ValueError("objective must not be empty")

    scores: dict[str, int] = dict.fromkeys(MISSION_TYPES, 0)
    for mtype, keywords in MISSION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in raw:
                scores[mtype] += 1
                # Knowledge/documentation and performance/optimization overlap
                # heavily; break ties by counting exact keyword length.
    mission_type = max(MISSION_TYPES, key=lambda m: (scores[m], len(MISSION_KEYWORDS[m])))
    if all(s == 0 for s in scores.values()):
        mission_type = "research"

    complexity_idx = TYPE_COMPLEXITY[mission_type]
    risk_idx = TYPE_RISK[mission_type]

    # Word count inflates complexity for long, multi-surface objectives.
    word_count = len(raw.split())
    if word_count > 25:
        complexity_idx = min(4, complexity_idx + 1)
    if "critical" in raw or "production" in raw or "national" in raw:
        risk_idx = min(4, risk_idx + 1)

    complexity = COMPLEXITY_LEVELS[complexity_idx]
    risk = RISK_LEVELS[risk_idx]
    priority = _priority_for(risk_idx, complexity_idx)
    duration_min, duration_max = DURATION_BY_COMPLEXITY[complexity]
    duration_minutes = min(
        duration_min + (len(raw.split()) * 2),
        duration_max,
    )

    dependencies = _dependencies_for(mission_type, raw)
    specialists = _specialists_for(mission_type)

    rationale = [
        f"type={mission_type} (score {scores[mission_type]}, matches {MISSION_TYPE_NAMES[mission_type]})",
        f"complexity={complexity} risk={risk} priority={priority}",
        f"estimated duration {duration_minutes} minutes",
        f"specialists: {', '.join(specialists) or 'none'}",
    ]
    if all(s == 0 for s in scores.values()):
        rationale.append("no keyword match; treated as research")

    return MissionClassification(
        objective=objective,
        mission_type=mission_type,
        priority=priority,
        complexity=complexity,
        risk=risk,
        dependencies=dependencies,
        duration_minutes=duration_minutes,
        required_specialists=specialists,
        rationale=rationale,
    )


def _priority_for(risk_idx: int, complexity_idx: int) -> str:
    combined = risk_idx + complexity_idx
    if combined >= 6:
        return "critical"
    if combined >= 4:
        return "high"
    if combined >= 2:
        return "medium"
    return "low"


def _dependencies_for(mission_type: str, raw: str) -> list[str]:
    """Keyword signals that name the systems a mission depends on."""
    deps: list[str] = []
    if any(k in raw for k in ("backend", "api", "service", "server", "database", "model")):
        deps.append("backend")
    if any(k in raw for k in ("frontend", "ui", "page", "dashboard", "screen")):
        deps.append("frontend")
    if any(k in raw for k in ("docker", "deploy", "kubernetes", "helm", "github actions", "ci/cd", "pipeline")):
        deps.append("deployment")
    if any(k in raw for k in ("fhir", "hl7", "iso", "cap", "clsi")):
        deps.append("standards")
    if any(k in raw for k in ("auth", "security", "permission", "encrypt")):
        deps.append("security")
    if mission_type == "testing":
        deps.append("verification")
    if mission_type == "deployment":
        deps.append("release")
    return deps


def _specialists_for(mission_type: str) -> list[str]:
    """Map a mission type to the engines/specialists that should handle it."""
    mapping = {
        "feature": ["builder"],
        "bug": ["builder", "reviewer"],
        "refactor": ["builder", "reviewer"],
        "deployment": ["deployer"],
        "security": ["builder", "reviewer"],
        "performance": ["optimizer", "reviewer"],
        "architecture": ["builder", "reviewer"],
        "documentation": ["learner"],
        "knowledge": ["learner"],
        "infrastructure": ["deployer", "builder"],
        "testing": ["builder", "reviewer"],
        "research": ["learner"],
    }
    return mapping.get(mission_type, [])


def describe(c: MissionClassification) -> str:
    return (
        f"{c.mission_type} mission: {c.objective[:60]}"
        f" [{c.priority}] {c.complexity} complexity / {c.risk} risk"
    )
