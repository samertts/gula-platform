"""Phase 6 — Design Review.

Review candidate designs across eight dimensions: architecture,
scalability, reliability, maintainability, security, performance, cost,
and compliance. Each dimension is scored against repo evidence; the overall
verdict is pass / conditional / fail.
"""

from __future__ import annotations

from pathlib import Path

from scripts.architect.core import (
    REVIEW_DIMENSIONS,
    REVIEW_DIR,
    DesignReview,
    ReviewFinding,
    ReviewVerdict,
    make_id,
    write_json,
)
from scripts.kernel.core import REPO_ROOT, utcnow

# Evidence probes per dimension -> (present-paths, default score).
DIMENSION_EVIDENCE: dict[str, tuple[tuple[str, ...], int]] = {
    "architecture": (("docs/adr/", "architecture/", "backend/app/services/"), 85),
    "scalability": (("scripts/deployer/", "backend/app/services/offline_sync_service.py"), 80),
    "reliability": (("backend/app/tasks/", "scripts/self_heal.py"), 80),
    "maintainability": (("scripts/reviewer/", "scripts/optimizer/", "backend/app/services/"), 80),
    "security": (("shared/security/", "backend/app/security/", "docs/security/"), 90),
    "performance": (("scripts/optimizer/", "backend/app/services/metrics_service.py"), 80),
    "cost": (("docs/constitution/COST_GOVERNANCE.md", "docker-compose.yml"), 80),
    "compliance": (("backend/app/fhir/", "docs/constitution/", "docs/adr/"), 85),
}


def _score_dimension(root: Path, dimension: str) -> int:
    patterns, default = DIMENSION_EVIDENCE.get(dimension, ((), 50))
    found = 0
    for pattern in patterns:
        path = root / pattern
        if path.exists():
            found += 1
    if found >= 2:
        return default
    if found == 1:
        return max(default - 15, 0)
    return max(default - 40, 0)


def _verdict(score: int) -> str:
    if score >= 80:
        return ReviewVerdict.PASS.value
    if score >= 50:
        return ReviewVerdict.CONDITIONAL.value
    return ReviewVerdict.FAIL.value


def review_design(candidate: str, root: Path | None = None) -> DesignReview:
    """Review a candidate design deterministically against evidence."""
    root = root or REPO_ROOT
    findings: list[ReviewFinding] = []
    for dimension in REVIEW_DIMENSIONS:
        score = _score_dimension(root, dimension)
        findings.append(ReviewFinding(
            dimension=dimension,
            verdict=_verdict(score),
            score=score,
            notes=f"Evidence-scored {dimension} at {score}/100.",
        ))
    scores = [f.score for f in findings]
    overall = round(sum(scores) / len(scores)) if scores else 0
    verdict = _verdict(overall)
    return DesignReview(
        review_id=make_id("REV"),
        candidate=candidate,
        findings=findings,
        verdict=verdict,
    )


def persist_review(candidate: str, root: Path | None = None) -> Path:
    """Persist a design review under state/review/."""
    root = root or REPO_ROOT
    review = review_design(candidate, root)
    path = REVIEW_DIR / "latest.json"
    write_json(path, review.to_dict())
    return path


def render_markdown(review: DesignReview) -> str:
    lines = [
        "# GULA-ARCHITECT-001 — Design Review",
        "",
        f"Generated: **{utcnow()}**",
        "",
        f"Candidate: **{review.candidate}**",
        "",
        f"Overall verdict: **{review.verdict.upper()}** "
        f"({review.overall_score()}/100).",
        "",
        "| Dimension | Score | Verdict |",
        "|---|---|---|",
    ]
    for finding in review.findings:
        lines.append(
            f"| {finding.dimension} | {finding.score}/100 | "
            f"{finding.verdict} |"
        )
    lines.append("")
    return "\n".join(lines)
