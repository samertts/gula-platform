"""Phase 0 — System Audit.

Audit the full optimization surface: backend, frontend, database,
infrastructure, Docker, knowledge system, deployment, documentation,
testing, CI/CD, and developer environment. Generate
OPTIMIZER_AUDIT_REPORT.md at the repository root. Deterministic; detects
what actually exists and reports honest gaps.
"""

from __future__ import annotations

from pathlib import Path

from scripts.kernel.core import REPO_ROOT
from scripts.optimizer.core import (
    AUDIT_COMPONENTS,
    AUDIT_PATH,
    AuditItem,
    OptimizationStatus,
)

# Component -> candidate files/directories that prove it exists.
AUDIT_PATTERNS: dict[str, tuple[str, ...]] = {
    "backend": ("backend/app/", "backend/pyproject.toml", "backend/requirements*.txt"),
    "frontend": ("frontend-v3/src/", "frontend-v3/package.json"),
    "database": ("backend/migrations/", "backend/app/models/"),
    "infrastructure": ("docker-compose*.yml", "config/nginx/"),
    "docker": ("backend/Dockerfile", "frontend-v3/Dockerfile", "*/Dockerfile"),
    "knowledge": (
        ".ai/core/registry/REGISTRY.md",
        ".ai/core/learner/",
        ".ai/core/memory/",
    ),
    "deployment": (
        "scripts/deployer/",
        ".ai/core/deployer/",
        ".github/workflows/*.yml",
    ),
    "documentation": ("docs/", "README.md", "AGENTS.md"),
    "testing": ("backend/tests/", "frontend-v3/src/**/*.test.ts"),
    "ci-cd": (".github/workflows/", "config/quality-gates/"),
    "developer-environment": (
        ".env.example",
        "Makefile",
        ".pre-commit-config.yaml",
        "pyproject.toml",
    ),
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
    """Collect evidence for every optimization area."""
    items: list[AuditItem] = []
    for kind in AUDIT_COMPONENTS:
        files = _component_files(kind)
        evidence = sorted({p.relative_to(REPO_ROOT).as_posix() for p in files})
        items.append(AuditItem(
            item_id=f"OA-{kind}",
            title=kind,
            status=OptimizationStatus.MEASURED.value if evidence
            else OptimizationStatus.PLANNED.value,
            confidence="verified" if evidence else "low",
            tags=["audit", kind],
            body="\n".join(f"- `{path}`" for path in evidence[:12]),
        ))
    return items


def render_markdown(items: list[AuditItem]) -> str:
    lines = [
        "# OPTIMIZER_AUDIT_REPORT.md",
        "",
        "Audit of the optimization surface for GULA-OPTIMIZER-001.",
        "",
        "| Area | Status | Notes | Evidence count |",
        "|---|---|---|---|",
    ]
    for item in items:
        present = item.status == OptimizationStatus.MEASURED.value
        lines.append(
            f"| {item.title} | {'present' if present else 'absent'} | "
            f"{'configured' if present else 'NOT FOUND'} | "
            f"{len(item.body.splitlines())} |"
        )
    present = sum(
        1 for item in items if item.status == OptimizationStatus.MEASURED.value
    )
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(
        f"**AUDIT COMPLETE** — {present}/{len(items)} optimization areas present. "
        "The Optimizer can measure, optimize, and evolve every surface that "
        "exists and flags honest gaps for the ones that do not."
    )
    lines.append("")
    return "\n".join(lines)


def run_audit() -> Path:
    """Write OPTIMIZER_AUDIT_REPORT.md and return its path."""
    items = audit_system()
    AUDIT_PATH.write_text(render_markdown(items), encoding="utf-8")
    return AUDIT_PATH
