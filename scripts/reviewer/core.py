"""Shared constants, dataclasses, and path helpers for the Reviewer Engine.

The Reviewer Engine (GULA-REVIEWER-001) is the independent engineering
verification authority. It verifies every Builder output before acceptance.
It never writes production features; it only validates. The Reviewer builds
on the Execution Kernel (GULA-KERNEL-001) primitives (findings, severity,
state) and stays fully independent of the Builder (GULA-BUILDER-001).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from scripts.kernel.core import REPO_ROOT, Severity, utcnow

REVIEWER_DIR = REPO_ROOT / ".ai" / "core" / "reviewer"
STATE_DIR = REVIEWER_DIR / "state"
DOCS_DIR = REPO_ROOT / "docs" / "reviewer"

# Review areas across all phases.
REVIEW_AREAS: tuple[str, ...] = (
    "architecture",
    "code",
    "security",
    "tests",
    "deployment",
    "documentation",
    "performance",
    "knowledge",
)

AREA_NAMES: dict[str, str] = {
    "architecture": "Architecture",
    "code": "Code",
    "security": "Security",
    "tests": "Testing",
    "deployment": "Deployment",
    "documentation": "Documentation",
    "performance": "Performance",
    "knowledge": "Knowledge",
}

# Severity score penalties for quality scoring (0-100 scale).
SEVERITY_PENALTY: dict[Severity, float] = {
    Severity.LOW: 2.0,
    Severity.MEDIUM: 5.0,
    Severity.HIGH: 15.0,
    Severity.CRITICAL: 30.0,
}

# Weight of each area in the overall readiness score (sums to 1.0).
AREA_WEIGHT: dict[str, float] = {
    "architecture": 0.15,
    "code": 0.15,
    "security": 0.20,
    "tests": 0.15,
    "deployment": 0.10,
    "documentation": 0.10,
    "performance": 0.05,
    "knowledge": 0.10,
}


class Decision(StrEnum):
    """Phase 9 — final verdict for a review."""

    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS WITH WARNINGS"
    REJECT = "REJECT"


@dataclass
class ReviewFinding:
    """One finding from a review area (immutable record)."""

    area: str
    severity: Severity
    title: str
    detail: str = ""
    evidence: str = ""
    suggested_fix: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "area": self.area,
            "severity": self.severity,
            "title": self.title,
            "detail": self.detail,
            "evidence": self.evidence,
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class AreaReview:
    """Result of reviewing one area."""

    area: str
    findings: list[ReviewFinding] = field(default_factory=list)
    score: float = 100.0
    decision: str = Decision.PASS.value

    def to_dict(self) -> dict[str, Any]:
        return {
            "area": self.area,
            "score": self.score,
            "decision": self.decision,
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass
class ReviewReport:
    """Full review of a change set / repository (phases 1-9)."""

    target: str
    mission_id: str = ""
    area_reviews: list[AreaReview] = field(default_factory=list)
    decision: str = Decision.REJECT.value
    overall_score: float = 0.0
    reviewed_at: str = field(default_factory=utcnow)

    def all_findings(self) -> list[ReviewFinding]:
        return [f for area in self.area_reviews for f in area.findings]

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "mission_id": self.mission_id,
            "decision": self.decision,
            "overall_score": self.overall_score,
            "reviewed_at": self.reviewed_at,
            "area_reviews": [a.to_dict() for a in self.area_reviews],
        }


def ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    import json

    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    import json

    ensure_dirs()
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def score_area(findings: list[ReviewFinding]) -> float:
    """Score an area on a 0-100 scale from its findings."""
    score = 100.0
    for finding in findings:
        score -= SEVERITY_PENALTY.get(finding.severity, 0.0)
    return round(max(0.0, score), 1)


def decide_area(findings: list[ReviewFinding]) -> str:
    """Deterministic area verdict: REJECT on high/critical, else PASS."""
    if any(f.severity in {Severity.HIGH, Severity.CRITICAL} for f in findings):
        return Decision.REJECT.value
    if findings:
        return Decision.PASS_WITH_WARNINGS.value
    return Decision.PASS.value


def decide_overall(area_reviews: list[AreaReview]) -> str:
    """Deterministic overall verdict: any reject rejects the review."""
    if any(a.decision == Decision.REJECT.value for a in area_reviews):
        return Decision.REJECT.value
    if any(a.decision == Decision.PASS_WITH_WARNINGS.value for a in area_reviews):
        return Decision.PASS_WITH_WARNINGS.value
    return Decision.PASS.value


def overall_score(area_reviews: list[AreaReview]) -> float:
    """Weighted overall readiness score (0-100)."""
    total = sum(AREA_WEIGHT.get(a.area, 0.0) * a.score for a in area_reviews)
    return round(total, 1)
