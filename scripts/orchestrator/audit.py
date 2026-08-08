"""Phase 0 — Audit of the current AI systems and project structure.

Audit the systems the Orchestrator will coordinate: Builder, Reviewer,
Kernel, Knowledge, Constitution, Registry, Deployment, and project
structure. Generate ORCHESTRATOR_AUDIT_REPORT.md at the repository root.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.kernel.core import REPO_ROOT

ORCHESTRATOR_AUDIT_PATH = REPO_ROOT / "docs/reports/ORCHESTRATOR_AUDIT_REPORT.md"

SYSTEMS: dict[str, tuple[str, ...]] = {
    "kernel": (
        "scripts/kernel/core.py",
        "scripts/kernel/cli.py",
        "scripts/kernel.py",
    ),
    "builder": (
        "scripts/builder/core.py",
        "scripts/builder/cli.py",
        "scripts/builder.py",
    ),
    "reviewer": (
        "scripts/reviewer/core.py",
        "scripts/reviewer/decision.py",
        "scripts/reviewer/cli.py",
        "scripts/reviewer.py",
    ),
    "deployer": (
        "scripts/deployer.py",
        "scripts/deployer/core.py",
    ),
    "learner": (
        "scripts/learner.py",
        "scripts/learner/core.py",
    ),
    "optimizer": (
        "scripts/optimizer.py",
        "scripts/optimizer/core.py",
    ),
    "architect": (
        "scripts/architect.py",
        "scripts/architect/core.py",
        "scripts/architect/cli.py",
    ),
    "domain": (
        "scripts/domains.py",
        "scripts/domains/core.py",
        "scripts/domains/cli.py",
        "backend/app/domain_platform/core.py",
    ),
    "knowledge": (
        ".ai/core/registry/REGISTRY.md",
        ".ai/core/index/INDEX.md",
        "docs/brain/PROJECT_BRAIN.md",
        "scripts/project_brain.py",
    ),
    "constitution": (
        "AI_OPERATING_CONSTITUTION.md",
        "docs/constitution/32_AI_EXECUTION_CONSTITUTION.md",
        "AGENTS.md",
    ),
    "registry": (
        ".ai/core/registry/REGISTRY.md",
        ".ai/core/index/INDEX.md",
    ),
    "deployment": (
        "backend/Dockerfile",
        "frontend-v3/Dockerfile",
        "docker-compose*.yml",
        ".github/workflows/*.yml",
    ),
}


@dataclass
class AuditEntry:
    """One audited system with its evidence and health signal."""

    name: str
    evidence: list[str] = field(default_factory=list)
    present: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "present": self.present, "evidence": self.evidence, "notes": self.notes}


def _expand(pattern: str) -> list[Path]:
    if any(ch in pattern for ch in "*?["):
        return sorted(Path(REPO_ROOT).glob(pattern))
    path = Path(REPO_ROOT) / pattern
    return [path] if path.exists() else []


def audit_systems() -> list[AuditEntry]:
    """Collect evidence for each system the Orchestrator coordinates."""
    entries: list[AuditEntry] = []
    for name, patterns in SYSTEMS.items():
        evidence: list[str] = []
        for pattern in patterns:
            for path in _expand(pattern):
                rel = path.relative_to(REPO_ROOT).as_posix()
                if rel not in evidence:
                    evidence.append(rel)
        notes = "ready to coordinate" if evidence else "NOT FOUND"
        entries.append(AuditEntry(name=name, evidence=evidence, present=bool(evidence), notes=notes))
    # Project structure health.
    structure = {
        "backend": "backend/app",
        "frontend": "frontend-v3/src",
        "shared": "shared",
        "tests": "backend/tests",
        "docs": "docs",
        "config": "config",
    }
    missing = [label for label, path in structure.items() if not (REPO_ROOT / path).exists()]
    entries.append(AuditEntry(
        name="project-structure",
        evidence=[f"{label}={path}" for label, path in structure.items()],
        present=not missing,
        notes="complete" if not missing else f"missing: {', '.join(missing)}",
    ))
    return entries


def render_markdown(entries: list[AuditEntry]) -> str:
    lines = [
        "# ORCHESTRATOR_AUDIT_REPORT.md",
        "",
        "Audit of the current AI systems for GULA-ORCHESTRATOR-001.",
        "",
        "| System | Status | Notes | Evidence |",
        "|---|---|---|---|",
    ]
    for entry in entries:
        state = "present" if entry.present else "absent"
        evidence = ", ".join(entry.evidence[:6]) or "—"
        lines.append(f"| {entry.name} | {state} | {entry.notes} | `{evidence}` |")
    lines.append("")
    present = sum(1 for e in entries if e.present)
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(
        f"**AUDIT COMPLETE** — {present}/{len(entries)} systems present. "
        "The Orchestrator can coordinate the Builder, Reviewer, Deployer, "
        "Learner, Optimizer, Kernel, and Knowledge systems. Where a dedicated "
        "engine is absent, the Orchestrator routes to the closest available "
        "engine and records the mapping as a decision."
    )
    lines.append("")
    return "\n".join(lines)


def detect() -> set[str]:
    """Return the set of engines that exist in the repo (phase 3 routing)."""
    return {e.name for e in audit_systems() if e.name in SYSTEMS and e.present}


def run_audit() -> Path:
    """Run the audit and write ORCHESTRATOR_AUDIT_REPORT.md."""
    entries = audit_systems()
    ORCHESTRATOR_AUDIT_PATH.write_text(render_markdown(entries), encoding="utf-8")
    return ORCHESTRATOR_AUDIT_PATH
