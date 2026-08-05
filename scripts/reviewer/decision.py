"""Phase 9 — Decision Engine.

Aggregate every area's findings into a single deterministic verdict:
PASS, PASS_WITH_WARNINGS, or REJECT. Uses core.py's weighted severity model
and area weights. Produces a ReviewReport (auditable: every finding is listed
with severity + evidence).
"""

from __future__ import annotations

from pathlib import Path

from scripts.kernel.core import REPO_ROOT
from scripts.reviewer.core import (
    AreaReview,
    Decision,
    ReviewFinding,
    ReviewReport,
    decide_area,
    decide_overall,
    overall_score,
    score_area,
    utcnow,
)

# The eight review areas in execution order. Each maps to a phase module
# exposing review(repo) -> list[ReviewFinding].
AREA_MODULES: dict[str, str] = {
    "architecture": "architecture_review",
    "code": "code_review",
    "security": "security_review",
    "tests": "test_review",
    "deployment": "deployment_review",
    "documentation": "docs_review",
    "performance": "performance_review",
    "knowledge": "knowledge_review",
}


def _load_findings(repo: Path, area: str) -> list[ReviewFinding]:
    """Import the area module and run its review(repo) deterministically."""
    module = __import__(
        f"scripts.reviewer.{AREA_MODULES[area]}", fromlist=["review"]
    )
    return list(module.review(repo))


def decide(
    repo: Path = REPO_ROOT,
    *,
    target: str = "repository",
    mission_id: str = "",
) -> ReviewReport:
    """Run all area reviews and produce the aggregate verdict."""
    area_reviews: list[AreaReview] = []
    for area in AREA_MODULES:
        findings = _load_findings(repo, area)
        area_reviews.append(
            AreaReview(
                area=area,
                findings=findings,
                score=score_area(findings),
                decision=decide_area(findings),
            )
        )
    return ReviewReport(
        target=target,
        mission_id=mission_id,
        area_reviews=area_reviews,
        decision=decide_overall(area_reviews),
        overall_score=overall_score(area_reviews),
        reviewed_at=utcnow(),
    )


def summary_lines(report: ReviewReport) -> list[str]:
    """Human-readable summary of a ReviewReport."""
    lines = [
        f"Reviewer verdict: {report.decision} (score {report.overall_score:.1f}/100)",
        f"Target: {report.target} | Mission: {report.mission_id or '—'} | {report.reviewed_at}",
        "",
    ]
    for area in report.area_reviews:
        lines.append(
            f"- {area.area:<14} {area.decision:<20} "
            f"score {area.score:5.1f}  ({len(area.findings)} finding(s))"
        )
    lines.append("")
    high = [f for a in report.area_reviews for f in a.findings
            if f.severity.value in {"HIGH", "CRITICAL"}]
    if high:
        lines.append(f"High/critical findings: {len(high)}")
        for f in high[:10]:
            lines.append(f"  - [{f.severity.value}] {f.title}: {f.detail}")
    return lines
