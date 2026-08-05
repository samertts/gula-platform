"""Phase 0 — Repository Audit for the Builder Engine.

Discover the repository: architecture, modules, applications, libraries,
packages, frontend, backend, infrastructure, deployment, documentation,
knowledge system, existing AI systems, and dependencies. Generate
BUILDER_AUDIT_REPORT.md at the repository root.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.kernel.core import REPO_ROOT, Finding, Severity

BUILDER_AUDIT_PATH = REPO_ROOT / "BUILDER_AUDIT_REPORT.md"


@dataclass
class Discovery:
    """A discovered repository dimension (category, entries, counts)."""

    category: str
    entries: list[str] = field(default_factory=list)
    count: int = 0
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "entries": self.entries,
            "count": self.count,
            "detail": self.detail,
        }


def _dirs(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(d.name for d in root.iterdir() if d.is_dir())


def _count_dir(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for _ in root.rglob("*") if _.is_file())


def _first_dirs(root: Path, n: int = 12) -> list[str]:
    return _dirs(root)[:n]


def discover_backend() -> Discovery:
    root = REPO_ROOT / "backend"
    discovery = Discovery("backend")
    if root.exists():
        app = root / "app"
        discovery.count = _count_dir(root)
        discovery.entries = _first_dirs(app)
        discovery.detail = f"{discovery.count} files under backend/"
    return discovery


def discover_frontend() -> Discovery:
    root = REPO_ROOT / "frontend-v3"
    discovery = Discovery("frontend")
    if root.exists():
        src = root / "src"
        discovery.count = _count_dir(src)
        discovery.entries = _first_dirs(src)
        discovery.detail = f"{discovery.count} files under frontend-v3/src"
    return discovery


def discover_knowledge() -> Discovery:
    root = REPO_ROOT / ".ai" / "core"
    discovery = Discovery("knowledge-system")
    if root.exists():
        discovery.count = _count_dir(root)
        discovery.entries = _dirs(root)
        discovery.detail = f"{discovery.count} files across {len(discovery.entries)} directories"
    return discovery


def discover_infrastructure() -> Discovery:
    roots = {
        "docker": REPO_ROOT / "docker",
        "k8s": REPO_ROOT / "k8s",
        "helm": REPO_ROOT / "helm",
        "terraform": REPO_ROOT / "terraform",
        "ci": REPO_ROOT / ".github" / "workflows",
        "deploy-scripts": REPO_ROOT / "scripts",
    }
    discovery = Discovery("infrastructure")
    for name, root in roots.items():
        count = _count_dir(root)
        if count:
            discovery.entries.append(f"{name} ({count})")
            discovery.count += count
    discovery.detail = f"{discovery.count} files across {len(discovery.entries)} surfaces"
    return discovery


def discover_ai_systems() -> Discovery:
    roots = {
        "kernel": REPO_ROOT / "scripts" / "kernel",
        "ext": REPO_ROOT / "scripts" / "kernel" / "ext",
        "builder": REPO_ROOT / "scripts" / "builder",
        "governor": REPO_ROOT / "scripts" / "governor",
        "validation": REPO_ROOT / "reports" / "validation",
        "brain": REPO_ROOT / "docs" / "brain",
    }
    discovery = Discovery("ai-systems")
    for name, root in roots.items():
        count = _count_dir(root)
        if count:
            discovery.entries.append(f"{name} ({count} files)")
            discovery.count += count
    discovery.detail = f"{discovery.count} files across {len(discovery.entries)} systems"
    return discovery


def discover_documentation() -> Discovery:
    root = REPO_ROOT / "docs"
    discovery = Discovery("documentation")
    if root.exists():
        discovery.count = _count_dir(root)
        discovery.entries = _dirs(root)
        discovery.detail = f"{discovery.count} files under docs/"
    return discovery


def discover_dependencies() -> Discovery:
    discovery = Discovery("dependencies")
    manifests = [
        "pyproject.toml",
        "requirements.txt",
        "backend/pyproject.toml",
        "shared/pyproject.toml",
        "package.json",
        "frontend-v3/package.json",
    ]
    for manifest in manifests:
        path = REPO_ROOT / manifest
        if path.exists():
            lines = path.read_text(encoding="utf-8").splitlines()
            discovery.entries.append(f"{manifest} ({len(lines)} lines)")
            discovery.count += 1
    discovery.detail = f"{discovery.count} manifests located"
    return discovery


def discover_services() -> Discovery:
    root = REPO_ROOT / "services"
    discovery = Discovery("services")
    if root.exists():
        discovery.entries = _first_dirs(root, 30)
        discovery.count = len(discovery.entries)
        discovery.detail = f"{discovery.count} service directories under services/"
    return discovery


def audit_repository() -> list[Discovery]:
    """Run all discovery passes."""
    return [
        discover_backend(),
        discover_frontend(),
        discover_knowledge(),
        discover_infrastructure(),
        discover_ai_systems(),
        discover_documentation(),
        discover_dependencies(),
        discover_services(),
    ]


def audit_findings(discoveries: list[Discovery]) -> list[Finding]:
    """Derive findings from discovery results (duplicates + gaps)."""
    findings: list[Finding] = []
    by_category = {d.category: d for d in discoveries}

    backend = by_category.get("backend")
    if backend and backend.count == 0:
        findings.append(Finding("BA-1", "Backend tree empty", Severity.HIGH, "audit",
                                "backend/ contains no files"))

    frontend = by_category.get("frontend")
    if frontend and frontend.count == 0:
        findings.append(Finding("BA-2", "Frontend tree empty", Severity.HIGH, "audit",
                                "frontend-v3/src contains no files"))

    knowledge = by_category.get("knowledge-system")
    if knowledge and knowledge.count == 0:
        findings.append(Finding("BA-3", "Knowledge system missing", Severity.HIGH, "audit",
                                ".ai/core contains no files"))

    ai_systems = by_category.get("ai-systems")
    if ai_systems and ai_systems.count > 0:
        findings.append(Finding("BA-4", "AI systems present", Severity.LOW, "audit",
                                f"{ai_systems.count} files across existing engines"))

    docs = by_category.get("documentation")
    if docs and docs.count > 0:
        findings.append(Finding("BA-5", "Documentation present", Severity.LOW, "audit",
                                f"{docs.count} files under docs/"))

    deps = by_category.get("dependencies")
    if deps and not deps.entries:
        findings.append(Finding("BA-6", "No dependency manifests found", Severity.MEDIUM, "audit",
                                "no pyproject.toml/package.json located"))

    findings.append(Finding("BA-7", "Builder Engine absent", Severity.MEDIUM, "audit",
                            "scripts/builder not yet registered in ai-systems"))
    return findings


def render_audit_markdown(discoveries: list[Discovery], findings: list[Finding]) -> str:
    lines: list[str] = [
        "# BUILDER_AUDIT_REPORT.md",
        "",
        "Repository audit for the GULA Builder Engine (GULA-BUILDER-001).",
        "",
        "## Discovery",
        "",
        "| Category | Count | Detail |",
        "|---|---|---|",
    ]
    for discovery in discoveries:
        lines.append(f"| {discovery.category} | {discovery.count} | {discovery.detail} |")
    lines.append("")
    lines.append("## Detailed Entries")
    lines.append("")
    for discovery in discoveries:
        lines.append(f"### {discovery.category}")
        lines.append("")
        if not discovery.entries:
            lines.append("_none_")
        else:
            for entry in discovery.entries:
                lines.append(f"- {entry}")
        lines.append("")
    lines.append("## Findings")
    lines.append("")
    if not findings:
        lines.append("_none_")
    else:
        for finding in findings:
            lines.append(f"- [{finding.severity.value}] {finding.id} — {finding.title}: {finding.detail}")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    high = [f for f in findings if f.severity in {Severity.HIGH, Severity.CRITICAL}]
    if high:
        lines.append(f"**AUDIT COMPLETE** — {len(findings)} findings, {len(high)} high/critical.")
    else:
        lines.append(f"**AUDIT COMPLETE** — {len(findings)} findings, none high/critical.")
    lines.append("")
    return "\n".join(lines)


def run_audit() -> Path:
    """Run the audit and write BUILDER_AUDIT_REPORT.md. Returns the path."""
    discoveries = audit_repository()
    findings = audit_findings(discoveries)
    BUILDER_AUDIT_PATH.write_text(
        render_audit_markdown(discoveries, findings), encoding="utf-8"
    )
    return BUILDER_AUDIT_PATH
