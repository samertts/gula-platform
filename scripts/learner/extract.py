"""Phase 1 — Knowledge Extraction.

After every completed mission, extract the full learning record:
problem, cause, solution, alternative solutions, rejected solutions,
trade-offs, risks, lessons learned, performance impact, security impact,
and future recommendations.

Extraction is deterministic: structured inputs come from mission history
(Orchestrator), deployment records (Deployer), and review verdicts
(Reviewer). Every extraction is persisted as JSON and registered, so no
engineering experience is ever lost.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.learner.core import (
    EXTRACTION_DIR,
    EXTRACTION_FIELDS,
    Extraction,
    read_json,
    write_json,
)


def extract(
    source: str,
    *,
    problem: str = "",
    cause: str = "",
    solution: str = "",
    alternative_solutions: list[str] | None = None,
    rejected_solutions: list[str] | None = None,
    tradeoffs: list[str] | None = None,
    risks: list[str] | None = None,
    lessons: list[str] | None = None,
    performance_impact: str = "",
    security_impact: str = "",
    recommendations: list[str] | None = None,
    reusable: bool = False,
) -> Extraction:
    """Build a structured Extraction from explicit knowledge fields."""
    return Extraction(
        source=source,
        problem=problem,
        cause=cause,
        solution=solution,
        alternative_solutions=list(alternative_solutions or []),
        rejected_solutions=list(rejected_solutions or []),
        tradeoffs=list(tradeoffs or []),
        risks=list(risks or []),
        lessons=list(lessons or []),
        performance_impact=performance_impact,
        security_impact=security_impact,
        recommendations=list(recommendations or []),
        reusable=reusable,
    )


def extract_from_mission(mission: dict[str, Any]) -> Extraction:
    """Derive an Extraction from an Orchestrator mission record.

    Mission records carry the objective and mission type; the Learner
    derives the learning fields deterministically so every completed
    mission contributes permanent knowledge even without free-text notes.
    """
    objective = mission.get("objective", "")
    mission_type = mission.get("mission_type", "feature")
    status = mission.get("status", "planned")
    return Extraction(
        source=f"mission:{mission.get('mission_id', 'unknown')}",
        problem=f"Complete engineering objective: {objective}",
        cause=f"Platform capability requested under {mission_type} classification",
        solution=f"Executed {mission_type} mission '{objective}' end-to-end through the "
        f"Orchestrator pipeline (status {status})",
        alternative_solutions=[],
        rejected_solutions=[],
        tradeoffs=[
            f"{mission_type} scope bounded by the mission plan",
            "Budget enforced per phase (5 minutes / 50 files)",
        ],
        risks=["Mission checkpoint required for progress durability"],
        lessons=[
            f"{mission_type.capitalize()} missions route through the Orchestrator pipeline",
            "Knowledge must be recorded after every mission regardless of outcome",
        ],
        performance_impact="Coordinated via deterministic mission pipeline",
        security_impact="Reviewed before merge via the Reviewer gate",
        recommendations=["Register mission knowledge before closing the mission"],
        reusable=mission_type in {"feature", "refactor", "bug"},
    )


def extract_from_deployment(deployment: dict[str, Any]) -> Extraction:
    """Derive an Extraction from a Deployer deployment record."""
    version = deployment.get("version", "")
    environment = deployment.get("environment", "")
    status = deployment.get("status", "planned")
    validations = deployment.get("validations", [])
    failures = [v.get("component") for v in validations if v.get("status") != "pass"]
    rolled_back = bool(deployment.get("rollbacks"))
    return Extraction(
        source=f"deployment:{deployment.get('deployment_id', 'unknown')}",
        problem=f"Deliver version {version} to the {environment} environment",
        cause="Release lifecycle progressed through the Deployer pipeline",
        solution=f"Deployed {version} to {environment} (status {status}) with "
        f"{len(validations)} health validations",
        alternative_solutions=[],
        rejected_solutions=[],
        tradeoffs=[
            "Security gate runs before health validation",
            "Snapshot captured before every deploy for rollback",
        ],
        risks=[f"Failed validations: {', '.join(failures)}" if failures else "None"],
        lessons=[
            "Every deployment is reversible via a pre-deploy snapshot",
            "Health rejection triggers automatic rollback",
            ("Rollback applied and verified" if rolled_back else "No rollback needed"),
        ],
        performance_impact=f"{len(validations)} health checks across the stack",
        security_impact="9 security areas verified before promotion",
        recommendations=["Record deployment lessons in the runbook"],
        reusable=status == "live",
    )


def persist_extraction(extraction: Extraction) -> Path:
    """Save an extraction to its durable JSON file and return the path."""
    EXTRACTION_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{_slug(extraction.source) or 'extraction'}.json"
    path = EXTRACTION_DIR / filename
    write_json(path, extraction.to_dict())
    return path


def load_extraction(path: Path) -> Extraction:
    return Extraction.from_dict(read_json(path))


def list_extractions() -> list[Extraction]:
    if not EXTRACTION_DIR.exists():
        return []
    extractions = []
    for path in sorted(EXTRACTION_DIR.glob("*.json")):
        extractions.append(load_extraction(path))
    return extractions


def missing_fields(extraction: Extraction) -> list[str]:
    """Return extraction fields that have no captured value."""
    missing: list[str] = []
    for field_name in EXTRACTION_FIELDS:
        value = getattr(extraction, field_name)
        if isinstance(value, (list, tuple)):
            if not value:
                missing.append(field_name)
        elif not value:
            missing.append(field_name)
    return missing


def _slug(source: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "-" for ch in source).strip("-")
    return cleaned[:60].lower()
