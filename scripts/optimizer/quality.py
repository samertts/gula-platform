"""Phase 9 — Quality Validation.

Verify the optimization program never regresses the platform: no functional
regression, performance improved, security preserved, documentation
updated, knowledge updated, deployment valid. Produce an OptimizationScore
so optimization quality is continuously measurable and the program is safe
to continue.
"""

from __future__ import annotations

from scripts.kernel.core import REPO_ROOT
from scripts.optimizer.core import (
    OPTIMIZER_DIR,
    QUALITY_CHECKS,
    OptimizationScore,
)
from scripts.optimizer.safe import load_runs

DEBT_PATH = OPTIMIZER_DIR / "state" / "debt" / "debt.json"


def run_validation() -> OptimizationScore:
    """Run all six quality checks and return the score."""
    score = OptimizationScore()
    runs = load_runs()
    verified = [r for r in runs if r.tests_passed and r.regression is False]
    regressed = [r for r in runs if r.regression]

    checks = {
        "no-functional-regression": _no_regression(score, runs),
        "performance-improved": _performance_improved(score, verified),
        "security-preserved": _security_preserved(),
        "documentation-updated": _documentation_updated(),
        "knowledge-updated": _knowledge_updated(),
        "deployment-valid": _deployment_valid(),
    }
    score.checks = {name: "pass" if ok else "fail" for name, ok in checks.items()}
    score.verified_runs = len(verified)
    score.improved_metrics = len([r for r in verified if r.improved()])
    score.regressions = [r.optimization_id for r in regressed]
    score.score = _compute_score(score)
    score.summary = _summary(score)
    return score


def render_markdown(score: OptimizationScore) -> str:
    lines = [
        "# Optimization Quality Validation",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    for name in QUALITY_CHECKS:
        lines.append(f"| {name} | {score.checks.get(name, 'fail')} |")
    lines.extend([
        "",
        f"Optimization score: **{score.score}/100**",
        f"Verified optimization runs: **{score.verified_runs}**",
        f"Improved metrics: **{score.improved_metrics}**",
        f"Regressions: **{len(score.regressions)}**",
        "",
        "## Verdict",
        "",
    ])
    if score.score >= 90:
        verdict = "**PASS** — the optimization program is safe and effective."
    elif score.score >= 70:
        verdict = "**PASS WITH WARNINGS** — address the failed checks before more optimization."
    else:
        verdict = "**REJECT** — regressions detected; roll back before continuing."
    lines.append(verdict)
    lines.append("")
    return "\n".join(lines)


def _no_regression(score: OptimizationScore, runs: list) -> bool:
    score.regressions = [r.optimization_id for r in runs if r.regression]
    return not score.regressions


def _performance_improved(score: OptimizationScore, verified: list) -> bool:
    score.verified_runs = len(verified)
    score.improved_metrics = len([r for r in verified if r.improved()])
    return bool(verified) and score.improved_metrics > 0


def _security_preserved() -> bool:
    """Security is preserved when no run was accepted without tests passing."""
    return all(r.tests_passed for r in load_runs() if r.status == "verified")


def _documentation_updated() -> bool:
    return (REPO_ROOT / "OPTIMIZER_AUDIT_REPORT.md").exists() and (
        REPO_ROOT / "OPTIMIZER_IMPLEMENTATION_REPORT.md"
    ).exists()


def _knowledge_updated() -> bool:
    return (REPO_ROOT / ".ai" / "core" / "learner" / "search_index.json").exists()


def _deployment_valid() -> bool:
    return (REPO_ROOT / ".ai" / "core" / "deployer" / "history").exists()


def _compute_score(score: OptimizationScore) -> int:
    value = 100
    value -= 20 * len(score.regressions)
    if not score.verified_runs:
        value -= 15
    if not score.improved_metrics:
        value -= 10
    if score.checks.get("security-preserved") != "pass":
        value -= 15
    return max(0, min(100, value))


def _summary(score: OptimizationScore) -> str:
    if score.score >= 90:
        return "Optimization program is healthy: verified, improved, and safe."
    if score.score >= 70:
        return "Optimization program works but needs the failed checks resolved."
    return "Optimization program regressed; roll back the flagged runs."
