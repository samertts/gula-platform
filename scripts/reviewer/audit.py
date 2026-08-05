"""Phase 0 — Audit of the current review process.

Audit the existing review/verification surface: quality gates, testing,
documentation, architecture, security, deployment, and knowledge. Generate
REVIEWER_AUDIT_REPORT.md at the repository root.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.kernel.core import REPO_ROOT, Finding, Severity

REVIEWER_AUDIT_PATH = REPO_ROOT / "REVIEWER_AUDIT_REPORT.md"


@dataclass
class AuditArea:
    """One audit dimension with evidence of existing verification."""

    name: str
    evidence: list[str] = field(default_factory=list)
    present: bool = False
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "present": self.present,
            "evidence": self.evidence,
            "detail": self.detail,
        }


def _exists(patterns: list[str]) -> list[str]:
    found: list[str] = []
    for pattern in patterns:
        for path in REPO_ROOT.glob(pattern):
            found.append(str(path.relative_to(REPO_ROOT)))
    return sorted(set(found))


def audit_current_process() -> list[AuditArea]:
    """Collect evidence for each verification surface."""
    surfaces = {
        "quality-gates": [
            "scripts/enterprise_validation_engine.py",
            "reports/validation/baseline.json",
            ".github/workflows/ai-governance.yml",
        ],
        "testing": [
            "backend/tests/*.py",
            "backend/tests/unit/*.py",
            "frontend-v3/src/**/__tests__/*.ts",
        ],
        "documentation": [
            "docs/*.md",
            "docs/adr/*.md",
            "docs/constitution/*.md",
        ],
        "architecture": [
            "docs/architecture/*.md",
            "docs/adr/*.md",
            "ARCHITECTURE.md",
        ],
        "security": [
            "backend/app/security/*.py",
            "SECURITY.md",
            "docs/security/*.md",
        ],
        "deployment": [
            "deploy.sh",
            "scripts/deploy.sh",
            "docker-compose*.yml",
            ".github/workflows/*.yml",
        ],
        "knowledge": [
            ".ai/core/registry/*.md",
            ".ai/core/index/*.md",
            ".ai/core/skills/*.md",
            ".ai/core/playbooks/*.md",
            ".ai/core/runbooks/*.md",
            ".ai/core/memory/*.md",
        ],
    }
    areas: list[AuditArea] = []
    for name, patterns in surfaces.items():
        evidence = _exists(patterns)
        areas.append(AuditArea(
            name=name,
            evidence=evidence,
            present=bool(evidence),
            detail=f"{len(evidence)} artifacts located",
        ))
    return areas


def audit_findings(areas: list[AuditArea]) -> list[Finding]:
    """Derive findings from audit areas."""
    findings: list[Finding] = []
    for area in areas:
        if not area.present:
            findings.append(Finding(
                f"RV-{area.name.upper()[:2]}-1",
                f"{area.name} surface absent",
                Severity.HIGH, "reviewer-audit",
                detail=f"no evidence found for {area.name}",
            ))
    findings.append(Finding(
        "RV-AUD-1",
        "Independent Reviewer absent",
        Severity.MEDIUM, "reviewer-audit",
        detail="scripts/reviewer not yet present; verification currently ad-hoc",
    ))
    findings.append(Finding(
        "RV-AUD-2",
        "Verification authority separation unproven",
        Severity.MEDIUM, "reviewer-audit",
        detail="no evidence that Builder output is independently gated before merge",
    ))
    return findings


def render_audit_markdown(areas: list[AuditArea], findings: list[Finding]) -> str:
    lines = [
        "# REVIEWER_AUDIT_REPORT.md",
        "",
        "Audit of the current review/verification process for GULA-REVIEWER-001.",
        "",
        "## Audit Areas",
        "",
        "| Area | Status | Detail |",
        "|---|---|---|",
    ]
    for area in areas:
        state = "present" if area.present else "absent"
        lines.append(f"| {area.name} | {state} | {area.detail} |")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    if not findings:
        lines.append("_none_")
    else:
        for finding in findings:
            lines.append(
                f"- [{finding.severity.value}] {finding.id} — {finding.title}: {finding.detail}"
            )
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    high = [f for f in findings if f.severity in {Severity.HIGH, Severity.CRITICAL}]
    lines.append(
        f"**AUDIT COMPLETE** — {len(findings)} findings, {len(high)} high/critical. "
        "An independent Reviewer Engine is required to make verification "
        "deterministic, auditable, and authoritative."
    )
    lines.append("")
    return "\n".join(lines)


def run_audit() -> Path:
    """Run the audit and write REVIEWER_AUDIT_REPORT.md. Returns the path."""
    areas = audit_current_process()
    findings = audit_findings(areas)
    REVIEWER_AUDIT_PATH.write_text(
        render_audit_markdown(areas, findings), encoding="utf-8"
    )
    return REVIEWER_AUDIT_PATH
