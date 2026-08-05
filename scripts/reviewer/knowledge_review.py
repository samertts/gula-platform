"""Phase 8 — Knowledge Review.

Verify the AI knowledge layer deterministically: registry, index, skills,
playbooks, runbooks, memory, and the active engines' READMEs. Ensures every
engine directory ships a README so the brain stays navigable.
"""

from __future__ import annotations

from pathlib import Path

from scripts.kernel.core import REPO_ROOT, Severity
from scripts.reviewer.core import ReviewFinding


def _files(root: Path, glob: str) -> list[Path]:
    if not root.exists():
        return []
    excluded = {".venv", "site-packages", "node_modules", "migrations", "__pycache__", "dist", "build"}
    return sorted(
        p for p in root.rglob(glob)
        if not any(part in excluded for part in p.parts)
    )


def check_registry_and_index(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify the registry and index exist and are non-empty."""
    findings: list[ReviewFinding] = []
    registry = _files(repo / ".ai" / "core" / "registry", "*.md")
    index = _files(repo / ".ai" / "core" / "index", "*.md")
    if not registry:
        findings.append(ReviewFinding(
            "knowledge", Severity.HIGH, "Registry missing",
            detail=".ai/core/registry has no markdown",
            evidence=".ai/core/registry",
            suggested_fix="publish the capability/module registry",
        ))
    else:
        text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in registry)
        if len(text) < 500:
            findings.append(ReviewFinding(
                "knowledge", Severity.LOW, "Registry sparse",
                detail="registry markdown is minimal",
                evidence=".ai/core/registry",
                suggested_fix="keep the registry current with each engine",
            ))
    if not index:
        findings.append(ReviewFinding(
            "knowledge", Severity.MEDIUM, "Knowledge index missing",
            detail=".ai/core/index has no markdown",
            evidence=".ai/core/index",
            suggested_fix="publish a knowledge index so the brain is navigable",
        ))
    return findings


def check_engine_readmes(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify each engine under scripts/ documents itself in .ai/core/<name>/."""
    findings: list[ReviewFinding] = []
    engines = sorted(p for p in (repo / "scripts").iterdir() if p.is_dir() and (p / "__init__.py").exists())
    for engine in engines:
        readme = repo / ".ai" / "core" / engine.name / "README.md"
        if not readme.exists():
            findings.append(ReviewFinding(
                "knowledge", Severity.MEDIUM, "Engine README missing",
                detail=f"scripts/{engine.name} has no .ai/core/{engine.name}/README.md",
                evidence=f".ai/core/{engine.name}",
                suggested_fix="document the engine: purpose, commands, decision model",
            ))
    return findings


def check_skill_and_playbook_layers(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify skills/playbooks/runbooks/memory layers exist."""
    findings: list[ReviewFinding] = []
    layers = {
        "skills": "skills",
        "playbooks": "playbooks",
        "runbooks": "runbooks",
        "memory": "memory",
    }
    for label, name in layers.items():
        files = _files(repo / ".ai" / "core" / name, "*.md")
        if not files:
            findings.append(ReviewFinding(
                "knowledge", Severity.MEDIUM, f"No {label} layer",
                detail=f".ai/core/{name} is empty",
                evidence=f".ai/core/{name}",
                suggested_fix=f"add operational {name} content",
            ))
    return findings


def check_brain_references(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify the project brain and bootstrap doc are current and referenced."""
    findings: list[ReviewFinding] = []
    brain = repo / "docs" / "brain" / "PROJECT_BRAIN.md"
    bootstrap = repo / "AI_BOOTSTRAP.md"
    if not brain.exists():
        findings.append(ReviewFinding(
            "knowledge", Severity.HIGH, "Project brain missing",
            detail="docs/brain/PROJECT_BRAIN.md not found",
            evidence="docs/brain",
            suggested_fix="regenerate the brain with scripts/project_brain.py",
        ))
    if not bootstrap.exists():
        findings.append(ReviewFinding(
            "knowledge", Severity.MEDIUM, "Bootstrap doc missing",
            detail="AI_BOOTSTRAP.md not found",
            evidence="repo root",
            suggested_fix="restore the onboarding bootstrap document",
        ))
    return findings


def review(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Run every knowledge review check for a repository."""
    findings: list[ReviewFinding] = []
    findings += check_registry_and_index(repo)
    findings += check_engine_readmes(repo)
    findings += check_skill_and_playbook_layers(repo)
    findings += check_brain_references(repo)
    return findings
