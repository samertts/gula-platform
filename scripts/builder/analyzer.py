"""Phase 1 — Mission Analyzer.

Classify a free-form objective into a mission type, estimate complexity,
risk, dependencies, required knowledge, expected files, execution cost,
execution time, outputs, verification strategy, and rollback strategy.
Deterministic keyword + weight scoring. No I/O at import time.
"""

from __future__ import annotations

import re
import uuid

from scripts.builder.core import (
    COMPLEXITY_LEVELS,
    MISSION_KEYWORDS,
    MISSION_TYPE_NAMES,
    MISSION_TYPES,
    RISK_LEVELS,
    TYPE_COMPLEXITY,
    TYPE_RISK,
    MissionAnalysis,
)


class AnalyzerError(Exception):
    """Raised for invalid analyzer inputs."""


def normalize(objective: str) -> str:
    """Lowercase and collapse whitespace for keyword matching."""
    if not objective or not objective.strip():
        raise AnalyzerError("objective must not be empty")
    return re.sub(r"\s+", " ", objective.strip().lower())


# Generic verbs are weak signals; domain terms are strong signals. Strong
# signals outvote generic verbs so "add security audit logging" is classified
# as security, not feature.
WEAK_KEYWORDS: frozenset[str] = frozenset(
    {"build", "add", "create", "implement", "new", "support", "fix", "improve", "use"}
)


def _keyword_weight(keyword: str) -> int:
    return 1 if keyword in WEAK_KEYWORDS else 3


def classify(objective: str) -> str:
    """Return the best-matching mission type (deterministic)."""
    text = normalize(objective)
    scores = dict.fromkeys(MISSION_TYPES, 0)
    for mission, keywords in MISSION_KEYWORDS.items():
        scores[mission] = sum(
            _keyword_weight(keyword) for keyword in keywords if keyword in text
        )
    best = max(scores, key=lambda m: scores[m])
    if scores[best] == 0:
        return "architecture"
    return best


def classify_scores(objective: str) -> dict[str, int]:
    """Return per-mission-type weighted keyword scores (for diagnostics)."""
    text = normalize(objective)
    return {
        mission: sum(_keyword_weight(keyword) for keyword in keywords if keyword in text)
        for mission, keywords in MISSION_KEYWORDS.items()
    }


def _level(index: int, scale: tuple[str, ...]) -> str:
    return scale[max(0, min(len(scale) - 1, index))]


def complexity_score(mission_type: str, objective: str, expected_files: list[str]) -> int:
    """0 (trivial) .. 4 (critical)."""
    base = TYPE_COMPLEXITY.get(mission_type, 2)
    file_bonus = len(expected_files) // 3
    words = len(normalize(objective).split())
    detail_bonus = 1 if words > 12 else 0
    return min(4, base + min(file_bonus, 2) + detail_bonus)


def risk_score(mission_type: str, complexity_index: int) -> int:
    """0 (negligible) .. 4 (critical)."""
    base = TYPE_RISK.get(mission_type, 2)
    return min(4, base + complexity_index // 2)


def expected_files_for(mission_type: str) -> list[str]:
    """Baseline set of files a mission of this type usually touches."""
    base = {
        "feature": ["source module", "API route", "service", "unit tests", "docs update"],
        "bug": ["faulty module", "unit test (regression)"],
        "refactor": ["restructured module", "tests", "docs update"],
        "deployment": ["workflow file", "deploy config", "release notes"],
        "security": ["security module", "config", "tests", "audit record"],
        "documentation": ["documentation file"],
        "infrastructure": ["docker/config", "CI workflow", "runbook"],
        "performance": ["hot path module", "benchmark", "tests"],
        "testing": ["test file", "fixtures"],
        "architecture": ["ADR", "module boundary", "tests"],
    }
    return list(base.get(mission_type, ["module", "tests"]))


def required_knowledge_for(mission_type: str) -> list[str]:
    """Knowledge domains the analyzer expects to consult."""
    base = {
        "feature": ["architecture", "existing services", "API contracts"],
        "bug": ["failure records", "relevant module", "runbooks"],
        "refactor": ["architecture", "ADR", "code quality"],
        "deployment": ["deployment runbooks", "CI workflows"],
        "security": ["security policy", "OWASP guidance", "encryption"],
        "documentation": ["docs style", "knowledge system"],
        "infrastructure": ["infrastructure docs", "docker/k8s"],
        "performance": ["performance guides", "benchmark baselines"],
        "testing": ["test conventions", "pytest config"],
        "architecture": ["constitution", "ADR", "layering rules"],
    }
    return list(base.get(mission_type, ["registry", "skills"]))


def outputs_for(mission_type: str) -> list[str]:
    """Expected outputs for a mission of this type."""
    base = {
        "feature": ["implemented module", "passing tests", "docs"],
        "bug": ["fixed module", "regression test", "verification"],
        "refactor": ["refactored module", "passing tests", "no behavior change"],
        "deployment": ["deployed artifact", "post-deploy health"],
        "security": ["hardened module", "verification", "audit trail"],
        "documentation": ["documentation"],
        "infrastructure": ["provisioned infra", "runbook"],
        "performance": ["benchmark result", "optimized module"],
        "testing": ["test suite", "coverage report"],
        "architecture": ["ADR", "updated module boundaries"],
    }
    return list(base.get(mission_type, ["verified change"]))


def verification_strategy_for(mission_type: str) -> str:
    base = {
        "feature": "run unit tests + type check; manual smoke on affected route",
        "bug": "run regression test proving the defect is fixed",
        "refactor": "run full test suite; verify no behavior drift",
        "deployment": "deploy to staging; run health checks + smoke tests",
        "security": "run security tests; confirm no new vulnerabilities",
        "documentation": "render docs; verify links and accuracy",
        "infrastructure": "validate config (docker build / terraform plan); run CI",
        "performance": "run benchmark before/after; assert no regression",
        "testing": "run full suite; assert target coverage",
        "architecture": "run architecture compliance checks; verify contracts",
    }
    return base.get(mission_type, "run test suite and type check")


def rollback_strategy_for(mission_type: str) -> str:
    base = {
        "feature": "revert commit; keep migrations backward-compatible",
        "bug": "revert fix commit; defect documented as known",
        "refactor": "revert refactor; behavior preserved by tests",
        "deployment": "rollback artifact to previous release",
        "security": "revert hardening commit; re-raise incident if needed",
        "documentation": "revert documentation file",
        "infrastructure": "restore previous config; re-provision if needed",
        "performance": "revert optimization; restore baseline",
        "testing": "revert test changes; suite unaffected",
        "architecture": "revert ADR decision; restore previous boundaries",
    }
    return base.get(mission_type, "revert the atomic change")


def cost_for(complexity_index: int) -> str:
    costs = ("trivial", "low", "medium", "high")
    return costs[min(complexity_index, 3)]


def minutes_for(mission_type: str, complexity_index: int) -> int:
    base = TYPE_COMPLEXITY.get(mission_type, 2)
    return 5 * (base + complexity_index + 1)


def analyze(objective: str, mission_id: str | None = None) -> MissionAnalysis:
    """Produce a complete MissionAnalysis for a free-form objective."""
    normalized = normalize(objective)
    mission_type = classify(normalized)
    expected_files = expected_files_for(mission_type)

    complexity_index = complexity_score(mission_type, normalized, expected_files)
    risk_index = risk_score(mission_type, complexity_index)

    return MissionAnalysis(
        mission_id=mission_id or f"MSN-{uuid.uuid4().hex[:8].upper()}",
        objective=objective.strip(),
        mission_type=mission_type,
        complexity=_level(complexity_index, COMPLEXITY_LEVELS),
        risk=_level(risk_index, RISK_LEVELS),
        dependencies=[f"kernel-{mission_type}"],
        required_knowledge=required_knowledge_for(mission_type),
        expected_files=expected_files,
        execution_cost=cost_for(complexity_index),
        execution_time_minutes=minutes_for(mission_type, complexity_index),
        outputs=outputs_for(mission_type),
        verification_strategy=verification_strategy_for(mission_type),
        rollback_strategy=rollback_strategy_for(mission_type),
        confidence=0.85,
    )


def describe(mission_type: str) -> str:
    """Human description for a mission type."""
    return MISSION_TYPE_NAMES.get(mission_type, "Unknown mission type")
