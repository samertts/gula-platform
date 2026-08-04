"""Phase 0 — Foundation Audit.

Audit the entire repository: every AI subsystem, governance, knowledge,
deployment, execution, and architecture. Identify duplicated responsibilities
and missing responsibilities. Generate KERNEL_AUDIT_REPORT.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .core import ENGINE_REGISTRY, REPO_ROOT, Finding, Severity

# Subsystem markers used to locate real implementations in the repository.
SUBSYSTEM_MARKERS: dict[str, list[str]] = {
    "governor": ["scripts/governor", "scripts/governor.py", "GOVERNOR_AUDIT_REPORT.md"],
    "validation": ["scripts/enterprise_validation_engine.py", "reports/validation"],
    "brain": ["scripts/project_brain.py", "docs/brain/PROJECT_BRAIN.md"],
    "constitution": ["AI_OPERATING_CONSTITUTION.md", "scripts/constitution_enforcer.py"],
    "knowledge": [".ai/core", ".ai/core/index", ".ai/core/registry"],
    "deployment": [".github/workflows", "deploy.sh", "scripts/deploy.sh"],
    "observability": ["scripts/enterprise_metrics.py", "scripts/gula_monitor.py"],
    "self-heal": ["scripts/self_heal.py", "scripts/auto_heal.sh"],
    "security": ["scripts/pre-commit-check-secrets.py", "scripts/rotate-secrets.sh"],
    "kernel": ["scripts/kernel", "scripts/kernel.py"],
}


@dataclass
class Subsystem:
    """An AI subsystem found (or missing) in the repository."""

    name: str
    present: bool
    evidence: list[str] = field(default_factory=list)


def _glob_matches(patterns: list[str]) -> list[str]:
    matches: list[str] = []
    for pattern in patterns:
        if "*" in pattern:
            for path in REPO_ROOT.glob(pattern):
                matches.append(str(path.relative_to(REPO_ROOT)))
        else:
            path = REPO_ROOT / pattern
            if path.exists():
                matches.append(pattern)
    return sorted(set(matches))


def scan_subsystems() -> list[Subsystem]:
    """Scan the repository for evidence of each AI subsystem."""
    return [
        Subsystem(name=name, present=bool(evidence := _glob_matches(patterns)), evidence=evidence)
        for name, patterns in SUBSYSTEM_MARKERS.items()
    ]


def find_duplicate_responsibilities() -> list[Finding]:
    """Detect responsibilities implemented in more than one place.

    The Kernel's mandate is to eliminate duplicated infrastructure, so this
    audit enumerates every known overlap between existing scripts.
    """
    overlaps = {
        "knowledge index": [
            "scripts/project_brain.py",
            "scripts/auto_registry.py",
            ".ai/core/index",
        ],
        "governance validation": [
            "scripts/enterprise_validation_engine.py",
            "scripts/validate_constitution.py",
            "scripts/validate_knowledge.py",
            "scripts/validate_ai_system.py",
        ],
        "technical debt": [
            "scripts/debt_automation.py",
            "scripts/technical_debt_registry.py",
            "scripts/repository_scorecard.py",
        ],
        "health monitoring": [
            "scripts/gula_monitor.py",
            "scripts/health_reports.py",
            "scripts/enterprise_metrics.py",
        ],
        "architecture compliance": [
            "scripts/architecture_compliance_engine.py",
            "scripts/architecture_guardian.py",
            "scripts/zero_drift_engine.py",
        ],
    }
    findings: list[Finding] = []
    for responsibility, markers in overlaps.items():
        present = [m for m in markers if (REPO_ROOT / m).exists()]
        if len(present) > 1:
            findings.append(Finding(
                id=f"KRN-DUP-{len(findings) + 1:03d}",
                title=f"Duplicated responsibility: {responsibility}",
                severity=Severity.MEDIUM,
                category="architecture",
                detail=f"Responsibility implemented in {len(present)} places",
                evidence=", ".join(present),
                proposed_fix="Route all callers through the Kernel instead of ad-hoc scripts",
            ))
    return findings


def find_missing_responsibilities() -> list[Finding]:
    """Identify responsibilities required by the Kernel mission that are missing."""
    required = {
        "execution state": ["scripts/kernel/state.py"],
        "autonomy engine": ["scripts/kernel/autonomy.py"],
        "mission scheduler": ["scripts/kernel/scheduler.py"],
        "lock manager": ["scripts/kernel/locks.py"],
        "simulation engine": ["scripts/kernel/simulation.py"],
        "observability": ["scripts/kernel/observability.py"],
        "failure recovery": ["scripts/kernel/recovery.py"],
        "technical debt engine": ["scripts/kernel/debt.py"],
    }
    findings: list[Finding] = []
    for responsibility, markers in required.items():
        if not any((REPO_ROOT / m).exists() for m in markers):
            findings.append(Finding(
                id=f"KRN-MISS-{len(findings) + 1:03d}",
                title=f"Missing responsibility: {responsibility}",
                severity=Severity.HIGH,
                category="execution",
                detail=f"No implementation found for '{responsibility}'",
                proposed_fix="Implement as a Kernel module (every engine depends on the Kernel)",
            ))
    return findings


def audit_findings() -> list[Finding]:
    """Produce the complete Phase 0 audit finding set."""
    findings: list[Finding] = []
    subsystems = scan_subsystems()
    missing = [s.name for s in subsystems if not s.present]
    if missing:
        findings.append(Finding(
            id="KRN-0001",
            title="Missing AI subsystems",
            severity=Severity.MEDIUM,
            category="architecture",
            detail=f"Subsystems with no implementation evidence: {', '.join(sorted(missing))}",
        ))

    # Every governed engine must expose the full Kernel contract.
    from .contract import contract_violations

    for violation in contract_violations(ENGINE_REGISTRY):
        findings.append(Finding(
            id=f"KRN-CONTRACT-{len(findings) + 1:04d}",
            title="Engine contract violation",
            severity=Severity.MEDIUM,
            category="engine-communication",
            detail=violation,
        ))

    findings.extend(find_duplicate_responsibilities())
    findings.extend(find_missing_responsibilities())
    return findings


def render_audit_markdown(findings: list[Finding], subsystems: list[Subsystem]) -> str:
    """Render the KERNEL_AUDIT_REPORT.md document."""
    lines = [
        "# KERNEL AUDIT REPORT",
        "",
        "> Mission: GULA-KERNEL-001 — Phase 0: Foundation Audit",
        "> Generated by: `scripts/kernel`",
        "",
        "## Executive Summary",
        "",
        "This report audits the entire repository to identify duplicated and",
        "missing responsibilities. It is the foundation for the Enterprise AI",
        "Execution Kernel — the permanent execution layer shared by every AI",
        "Engine.",
        "",
        "## 1. Subsystem Inventory",
        "",
        "| Subsystem | Present | Evidence |",
        "|---|---|---|",
    ]
    for subsystem in sorted(subsystems, key=lambda s: s.name):
        evidence = ", ".join(subsystem.evidence[:3]) or "—"
        lines.append(
            f"| {subsystem.name} | {'yes' if subsystem.present else 'NO'} | {evidence} |"
        )

    lines += [
        "",
        "## 2. Duplicated Responsibilities",
        "",
        "The Kernel eliminates duplicated infrastructure. Every detected overlap",
        "is listed so callers can be unified behind the Kernel.",
        "",
        "| ID | Category | Severity | Title | Detail |",
        "|---|---|---|---|---|",
    ]
    for finding in [f for f in findings if f.category == "architecture"]:
        lines.append(
            f"| {finding.id} | {finding.category} | {finding.severity.value} | "
            f"{finding.title} | {finding.detail} |"
        )

    lines += [
        "",
        "## 3. Missing Responsibilities",
        "",
        "| ID | Category | Severity | Title | Detail |",
        "|---|---|---|---|---|",
    ]
    for finding in [f for f in findings if f.category == "execution"]:
        lines.append(
            f"| {finding.id} | {finding.category} | {finding.severity.value} | "
            f"{finding.title} | {finding.detail} |"
        )

    lines += [
        "",
        "## 4. Findings Summary",
        "",
        "| ID | Category | Severity | Title |",
        "|---|---|---|---|",
    ]
    for finding in findings:
        lines.append(
            f"| {finding.id} | {finding.category} | {finding.severity.value} | {finding.title} |"
        )
    lines += [
        "",
        f"**Audit findings: {len(findings)}**",
        "",
    ]
    return "\n".join(lines) + "\n"
