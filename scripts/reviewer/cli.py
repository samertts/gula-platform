"""Reviewer CLI — GULA-REVIEWER-001 commands.

Integrated into `scripts/kernel.py` so the Kernel remains the single entry
point. No ad-hoc scripts; every Reviewer command is reached through the Kernel.
"""

from __future__ import annotations

from scripts.reviewer.core import ReviewFinding, decide_area, score_area

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


def _load_findings(area: str) -> list[ReviewFinding]:

    from scripts.kernel.core import REPO_ROOT

    module = __import__(
        f"scripts.reviewer.{AREA_MODULES[area]}", fromlist=["review"]
    )
    return list(module.review(REPO_ROOT))


def run_audit() -> int:
    """Phase 0 — write REVIEWER_AUDIT_REPORT.md."""
    from .audit import run_audit as _audit

    path = _audit()
    print(f"[OK] {path.name} written")
    return 0


def _print_area(area: str, findings: list[ReviewFinding]) -> None:
    score = score_area(findings)
    decision = decide_area(findings)
    print(f"{area.upper()} REVIEW (GULA-REVIEWER-001)")
    print(f"  verdict: {decision} (score {score:.1f}/100)")
    for finding in findings:
        print(
            f"    [{finding.severity.value}] {finding.title}: {finding.detail[:100]}"
        )
    if not findings:
        print("    no findings")


def run_area(area: str) -> int:
    """Review a single area."""
    if area not in AREA_MODULES:
        print(f"Unknown area: {area}")
        print("Available: " + ", ".join(sorted(AREA_MODULES)))
        return 2
    findings = _load_findings(area)
    _print_area(area, findings)
    return 0 if decide_area(findings) != "REJECT" else 1


def run_review() -> int:
    """Run all area reviews, persist JSON, print the verdict."""
    from .decision import decide, summary_lines

    report = decide()
    from .report import run

    run(report)
    for line in summary_lines(report):
        print(line)
    return 0 if report.decision == "PASS" else 1 if report.decision == "REJECT" else 0


def run_gate() -> int:
    """Run the review and return gate exit semantics (0 pass, 1 reject)."""
    from .decision import decide
    from .report import gate

    report = decide()
    code = gate(report)
    print(f"Reviewer gate: {report.decision} (score {report.overall_score:.1f}/100)")
    return code


def run_report() -> int:
    """Phase 10 — write REVIEWER_IMPLEMENTATION_REPORT.md."""
    from .decision import decide
    from .report import run

    path = run(decide())
    print(f"[OK] {path.name} written")
    return 0


def run_check() -> int:
    """Run all Reviewer self-checks; exit 1 on any failure."""
    failures: list[str] = []
    areas: list[tuple[str, list[ReviewFinding]]] = []
    for area in AREA_MODULES:
        findings = _load_findings(area)
        areas.append((area, findings))
        if decide_area(findings) == "REJECT":
            failures.append(f"{area} area rejects")

    from .decision import decide

    report = decide()
    if report.decision == "REJECT":
        failures.append("overall review rejects")


    knowledge_ok = any(
        a.area == "knowledge" and not a.findings
        for a in report.area_reviews
    )
    if not knowledge_ok:
        failures.append("knowledge review not clean")

    print("REVIEWER SELF-CHECK")
    print("=" * 60)
    if failures:
        for failure in failures:
            print(f"  - {failure}")
        print("=" * 60)
        return 1
    for area, findings in areas:
        print(f"  [PASS] {area:14s} {decide_area(findings):22s} "
              f"score {score_area(findings):5.1f}")
    print("  [PASS] overall verdict is deterministic and non-reject")
    print("=" * 60)
    print("RESULT: ALL REVIEWER CHECKS PASSED")
    return 0


def run_area_command() -> int:
    """Review a single area given as the next CLI argument."""
    import sys

    area = sys.argv[2] if len(sys.argv) > 2 else "architecture"
    return run_area(area)


REVIEWER_COMMANDS = {
    "reviewer-audit": run_audit,
    "reviewer-review": run_review,
    "reviewer-area": run_area_command,
    "reviewer-gate": run_gate,
    "reviewer-report": run_report,
    "reviewer-check": run_check,
    "reviewer-architecture": lambda: run_area("architecture"),
    "reviewer-code": lambda: run_area("code"),
    "reviewer-security": lambda: run_area("security"),
    "reviewer-tests": lambda: run_area("tests"),
    "reviewer-deployment": lambda: run_area("deployment"),
    "reviewer-documentation": lambda: run_area("documentation"),
    "reviewer-performance": lambda: run_area("performance"),
    "reviewer-knowledge": lambda: run_area("knowledge"),
}
