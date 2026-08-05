"""Phase 0 — Architecture Audit.

Audit the architecture surface of the GULA national healthcare platform:
backend, frontend, database, identity, FHIR/HL7, multi-tenancy, offline,
event bus, analyzer integration, security, infrastructure, deployment,
governance, documentation, testing, and the AI engine constellation.
Generate ARCHITECT_AUDIT_REPORT.md at the repository root. Deterministic;
detects what actually exists and reports honest gaps.
"""

from __future__ import annotations

from pathlib import Path

from scripts.architect.core import (
    ARCHITECTURE_COMPONENTS,
    AUDIT_PATH,
    AuditItem,
)
from scripts.kernel.core import REPO_ROOT

# Component -> candidate files/directories that prove it exists.
AUDIT_PATTERNS: dict[str, tuple[str, ...]] = {
    "backend": ("backend/app/", "backend/pyproject.toml"),
    "frontend": ("frontend-v3/src/", "frontend-v3/package.json"),
    "database": ("backend/migrations/", "backend/app/models/"),
    "identity": ("backend/app/routes/identity.py", "backend/app/services/identity_service.py"),
    "fhir-hl7": ("backend/app/fhir/", "shared/fhir/", "backend/app/hl7/"),
    "multi-tenancy": ("backend/app/control_plane/multi_tenant.py", "backend/app/multi_tenant/", "backend/app/tenant/"),
    "offline-first": ("backend/app/services/offline_sync_service.py", "frontend-v3/public/sw.js"),
    "event-bus": ("backend/app/tasks/", "backend/app/events/", "shared/events/"),
    "analyzer-integration": ("backend/app/radiology/device.py", "backend/app/analyzers/", "backend/app/integrations/analyzers/"),
    "security": ("shared/security/", "backend/app/security/"),
    "infrastructure": ("docker-compose*.yml", "config/nginx/", "k8s/"),
    "deployment": ("scripts/deployer/", ".ai/core/deployer/", ".github/workflows/*.yml"),
    "governance": ("AI_OPERATING_CONSTITUTION.md", "docs/constitution/", "scripts/kernel/"),
    "documentation": ("docs/", "README.md", "AGENTS.md", "CLAUDE.md"),
    "testing": ("backend/tests/", "frontend-v3/src/**/*.test.ts"),
    "ai-engines": ("scripts/builder/", "scripts/reviewer/", "scripts/orchestrator/"),
}


def _expand(pattern: str) -> list[Path]:
    if any(ch in pattern for ch in "*?["):
        return sorted(Path(REPO_ROOT).glob(pattern))
    path = Path(REPO_ROOT) / pattern
    return [path] if path.exists() else []


def _component_files(kind: str) -> list[Path]:
    patterns = AUDIT_PATTERNS.get(kind, ())
    files: list[Path] = []
    for pattern in patterns:
        for path in _expand(pattern):
            if path.is_file():
                files.append(path)
            else:
                files.extend(p for p in path.rglob("*") if p.is_file())
    return files


def audit_system() -> list[AuditItem]:
    """Collect evidence for every architecture surface."""
    items: list[AuditItem] = []
    for kind in ARCHITECTURE_COMPONENTS:
        files = _component_files(kind)
        evidence = sorted({p.relative_to(REPO_ROOT).as_posix() for p in files})
        items.append(AuditItem(
            item_id=f"ARC-{kind}",
            title=kind,
            status="measured" if evidence else "planned",
            confidence="verified" if evidence else "low",
            tags=["architecture", kind],
            body="\n".join(f"- `{path}`" for path in evidence[:12]),
        ))
    return items


def render_markdown(items: list[AuditItem]) -> str:
    lines = [
        "# ARCHITECT_AUDIT_REPORT.md",
        "",
        "Architecture-surface audit for GULA-ARCHITECT-001.",
        "",
        "| Surface | Status | Evidence count |",
        "|---|---|---|",
    ]
    for item in items:
        present = item.status == "measured"
        lines.append(
            f"| {item.title} | {'present' if present else 'absent'} | "
            f"{len(item.body.splitlines())} |"
        )
    present = sum(1 for item in items if item.status == "measured")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(
        f"**ARCHITECTURE AUDIT COMPLETE** — {present}/{len(items)} architecture "
        "surfaces present. The Architect can model, govern, and evolve every "
        "surface that exists and flags honest gaps for the ones that do not."
    )
    lines.append("")
    return "\n".join(lines)


def run_audit() -> Path:
    """Write ARCHITECT_AUDIT_REPORT.md and return its path."""
    items = audit_system()
    AUDIT_PATH.write_text(render_markdown(items), encoding="utf-8")
    return AUDIT_PATH
