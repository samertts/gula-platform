"""Phase 7 — Self Review.

Before completing any mission the Builder reviews: architecture, security,
performance, testing, deployment, documentation, code quality, and knowledge.
The review is driven by evidence collected during execution; each area is a
pass/fail check with severity. Only continue when all validations pass.
"""

from __future__ import annotations

from typing import Any

from scripts.builder.core import (
    ReviewFinding,
    ReviewReport,
)
from scripts.kernel.core import Severity

REVIEW_AREAS: tuple[str, ...] = (
    "architecture",
    "security",
    "performance",
    "testing",
    "deployment",
    "documentation",
    "code-quality",
    "knowledge",
)

# Evidence keys in the execution context that satisfy each area.
AREA_EVIDENCE: dict[str, tuple[str, ...]] = {
    "architecture": ("adr", "architecture_approved", "layering_verified"),
    "security": ("security_verified", "no_new_vulnerabilities", "least_privilege"),
    "performance": ("benchmark_pass", "no_regression", "performance_ok"),
    "testing": ("tests_run", "tests_pass", "coverage_ok"),
    "deployment": ("deploy_verified", "rollback_armed", "health_ok"),
    "documentation": ("docs_updated", "docstring_added", "readme_updated"),
    "code-quality": ("ruff_clean", "typecheck_clean", "lint_clean"),
    "knowledge": ("registry_updated", "knowledge_updated", "skill_reused"),
}


def _area_pass(area: str, context: dict[str, Any]) -> tuple[bool, str]:
    evidence = AREA_EVIDENCE[area]
    present = [key for key in evidence if context.get(key) is True]
    if present:
        return True, f"evidence: {', '.join(present)}"
    return False, "missing evidence: " + ", ".join(evidence)


def review(mission_id: str, context: dict[str, Any] | None = None) -> ReviewReport:
    """Run all review areas against the execution evidence."""
    context = context or {}
    report = ReviewReport(mission_id=mission_id)
    for area in REVIEW_AREAS:
        passed, detail = _area_pass(area, context)
        severity = Severity.MEDIUM if passed else Severity.HIGH
        report.findings.append(ReviewFinding(
            area=area,
            severity=severity,
            detail=detail,
            passed=passed,
        ))
    return report


def review_verdict(report: ReviewReport) -> str:
    """PASS only when every review area passed."""
    return report.verdict()


def can_continue(report: ReviewReport) -> bool:
    """True when the review found no failures."""
    return not report.failed()


def summary(report: ReviewReport) -> str:
    """Compact summary of the review."""
    failed = report.failed()
    return f"{report.verdict()} ({len(report.findings) - len(failed)}/{len(report.findings)} areas passed)"
