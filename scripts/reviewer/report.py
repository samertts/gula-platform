"""Phase 10 — Report.

Persist the ReviewReport as JSON in .ai/core/reviewer/state and render a
root-level REVIEWER_IMPLEMENTATION_REPORT.md. Also exposes a gate() helper
that returns exit-code semantics for CI/kernel wiring.
"""

from __future__ import annotations

from pathlib import Path

from scripts.kernel.core import REPO_ROOT
from scripts.reviewer.core import STATE_DIR, Decision, ReviewReport, write_json
from scripts.reviewer.decision import decide, summary_lines

REVIEWER_REPORT_PATH = REPO_ROOT / "REVIEWER_IMPLEMENTATION_REPORT.md"


def run(report: ReviewReport) -> Path:
    """Persist the report JSON and render the markdown. Returns report path."""
    state_path = STATE_DIR / "latest_review.json"
    write_json(state_path, report.to_dict())

    sections = [
        "# REVIEWER_IMPLEMENTATION_REPORT.md",
        "",
        "Deterministic review verdict from GULA-REVIEWER-001.",
        "",
        "```",
        *summary_lines(report),
        "```",
        "",
        "## Area Findings",
        "",
    ]
    for area in report.area_reviews:
        sections.append(f"### {area.area} — {area.decision} (score {area.score:.1f})")
        sections.append("")
        if not area.findings:
            sections.append("_no findings_")
        else:
            sections.append("| Severity | Title | Detail | Evidence | Suggested fix |")
            sections.append("|---|---|---|---|---|")
            for f in area.findings:
                sections.append(
                    f"| {f.severity.value} | {f.title} | {f.detail} | "
                    f"`{f.evidence}` | {f.suggested_fix} |"
                )
        sections.append("")
    sections.append("---")
    sections.append(f"Reviewed at: {report.reviewed_at}")
    sections.append(f"Overall score: {report.overall_score:.1f}/100 — {report.decision}")
    sections.append("")
    REVIEWER_REPORT_PATH.write_text("\n".join(sections), encoding="utf-8")
    return REVIEWER_REPORT_PATH


def gate(report: ReviewReport) -> int:
    """Return 0 when the review passes (PASS or PASS_WITH_WARNINGS), else 1.

    REJECT always fails the gate; PASS_WITH_WARNINGS is advisory only, so a
    repository with warnings still compiles/deploys but the report records
    the warnings for the next acceptance step.
    """
    if report.decision == Decision.REJECT.value:
        return 1
    return 0


def main(repo: Path = REPO_ROOT) -> int:
    """Run the full review, render the report, and return the gate code."""
    report = decide(repo)
    run(report)
    for line in summary_lines(report):
        print(line)
    return gate(report)


if __name__ == "__main__":
    raise SystemExit(main())
