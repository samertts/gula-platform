"""Phase 0 — Knowledge Audit.

Audit the full knowledge system: registry, graph, memory, skills,
playbooks, runbooks, ADR, constitution, bridge files, templates, reports,
and search indexes. Generate LEARNER_AUDIT_REPORT.md at the repository
root. Deterministic; detects what actually exists and reports honest gaps.
"""

from __future__ import annotations

from pathlib import Path

from scripts.kernel.core import REPO_ROOT
from scripts.learner.core import (
    AUDIT_COMPONENTS,
    AUDIT_PATH,
    KnowledgeItem,
)

# Component -> candidate files/directories that prove it exists.
AUDIT_PATTERNS: dict[str, tuple[str, ...]] = {
    "registry": (".ai/core/registry/REGISTRY.md", ".ai/core/kernel/state/registry"),
    "graph": (".ai/core/graph/", "docs/brain/brain_index.json"),
    "memory": (".ai/core/memory/PROJECT_MEMORY.md", ".ai/core/memory/"),
    "skills": (".ai/core/skills/", ".agents/skills/"),
    "playbooks": (".ai/core/playbooks/",),
    "runbooks": (".ai/core/runbooks/",),
    "adr": ("docs/adr/", "docs/architecture/adr/"),
    "constitution": (
        "AI_OPERATING_CONSTITUTION.md",
        "docs/constitution/",
        ".ai/core/constitution/",
    ),
    "bridge-files": (".ai/core/",),
    "templates": (".ai/core/templates/", ".agents/skills/*/SKILL.md"),
    "reports": (".ai/core/reports/", "reports/validation/"),
    "search-indexes": (".ai/core/kernel/state", "docs/brain/brain_index.json"),
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


def audit_system() -> list[KnowledgeItem]:
    """Collect evidence for every knowledge component."""
    items: list[KnowledgeItem] = []
    for kind in AUDIT_COMPONENTS:
        files = _component_files(kind)
        evidence = sorted({p.relative_to(REPO_ROOT).as_posix() for p in files})
        items.append(KnowledgeItem(
            item_id=f"KA-{kind}",
            kind="knowledge-audit",
            title=kind,
            status="verified" if evidence else "planned",
            confidence="verified" if evidence else "low",
            tags=["audit", kind],
            body="\n".join(f"- `{path}`" for path in evidence[:12]),
        ))
    return items


def render_markdown(items: list[KnowledgeItem]) -> str:
    lines = [
        "# LEARNER_AUDIT_REPORT.md",
        "",
        "Audit of the knowledge system for GULA-LEARNER-001.",
        "",
        "| Component | Status | Notes | Evidence count |",
        "|---|---|---|---|",
    ]
    for item in items:
        present = item.status == "verified"
        lines.append(
            f"| {item.title} | {'present' if present else 'absent'} | "
            f"{'configured' if present else 'NOT FOUND'} | {len(item.body.splitlines())} |"
        )
    present = sum(1 for item in items if item.status == "verified")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(
        f"**AUDIT COMPLETE** — {present}/{len(items)} knowledge components present. "
        "The Learner can index, evolve, and search the knowledge stores that exist "
        "and flag honest gaps for the ones that do not."
    )
    lines.append("")
    return "\n".join(lines)


def run_audit() -> Path:
    """Write LEARNER_AUDIT_REPORT.md and return its path."""
    items = audit_system()
    AUDIT_PATH.write_text(render_markdown(items), encoding="utf-8")
    return AUDIT_PATH
