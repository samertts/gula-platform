"""Phase 5 — Developer Experience.

Improve developer productivity without changing behavior: build speed, test
speed, development startup, repository navigation, knowledge search,
automation, tooling, and developer feedback. Every dimension receives a
score (0-100) derived from deterministic repo evidence and a concrete
recommendation. Reduces unnecessary engineering effort across the platform.
"""

from __future__ import annotations

from pathlib import Path

from scripts.kernel.core import REPO_ROOT, utcnow
from scripts.optimizer.core import (
    DX_DIMENSIONS,
    STATE_DIR,
    DxFinding,
    read_json,
    write_json,
)

DX_PATH = STATE_DIR / "developer_experience.json"

# Dimension -> evidence globs that prove tooling exists.
DX_EVIDENCE: dict[str, tuple[str, ...]] = {
    "build-speed": (
        "backend/pyproject.toml",
        "frontend-v3/package.json",
        "frontend-v3/vite.config.ts",
    ),
    "test-speed": (
        "backend/pyproject.toml",
        "frontend-v3/vite.config.ts",
        "backend/tests/",
    ),
    "dev-startup": (
        "backend/Dockerfile",
        "docker-compose.yml",
        ".env.example",
        "Makefile",
    ),
    "repository-navigation": (
        "README.md",
        "AGENTS.md",
        "docs/",
        "backend/app/",
        "frontend-v3/src/",
    ),
    "knowledge-search": (
        ".ai/core/learner/search_index.json",
        "docs/brain/PROJECT_BRAIN.md",
        ".ai/core/registry/REGISTRY.md",
    ),
    "automation": (
        ".github/workflows/",
        "Makefile",
        ".pre-commit-config.yaml",
        "scripts/kernel.py",
    ),
    "tooling": (
        "backend/pyproject.toml",
        ".pre-commit-config.yaml",
        "frontend-v3/package.json",
        "frontend-v3/vite.config.ts",
    ),
    "developer-feedback": (
        "docs/ai/RISK_REGISTER.md",
        "reports/validation/validation_report.md",
        "ORCHESTRATOR_AUDIT_REPORT.md",
    ),
}

# Dimension -> recommendation when tooling is missing.
DX_RECOMMENDATIONS: dict[str, str] = {
    "build-speed": "Add caching to the build pipeline and keep the build matrix minimal.",
    "test-speed": "Split slow integration suites from fast unit suites and cache dependencies.",
    "dev-startup": "Provide a one-command local environment with sample data and health checks.",
    "repository-navigation": "Keep the README, architecture map, and engine indexes current.",
    "knowledge-search": "Rebuild the knowledge search index after every structural change.",
    "automation": "Automate quality gates, lint, and formatting in pre-commit and CI.",
    "tooling": "Standardize on a single linter, formatter, and type checker for the stack.",
    "developer-feedback": "Publish validation reports and risk registers so feedback reaches developers.",
}


def assess_dx(root: Path = REPO_ROOT) -> list[DxFinding]:
    """Score every developer-experience dimension deterministically."""
    findings: list[DxFinding] = []
    for index, dimension in enumerate(DX_DIMENSIONS):
        present = 0
        total = 0
        for pattern in DX_EVIDENCE.get(dimension, ()):
            total += 1
            if _any_match(root, pattern):
                present += 1
        score = round(present / total * 100) if total else 0
        findings.append(DxFinding(
            dx_id=f"DX-{index + 1:06d}",
            dimension=dimension,
            score=score,
            recommendation=DX_RECOMMENDATIONS.get(
                dimension,
                "Measure and improve this developer-experience dimension.",
            ),
        ))
    return findings


def persist_dx(findings: list[DxFinding]) -> Path:
    payload = {"findings": [f.to_dict() for f in findings], "updated_at": utcnow()}
    write_json(DX_PATH, payload)
    return DX_PATH


def load_dx() -> list[DxFinding]:
    data = read_json(DX_PATH)
    return [DxFinding(**item) for item in data.get("findings", [])]


def average_score(findings: list[DxFinding] | None = None) -> float:
    """Average developer-experience score across all dimensions."""
    findings = findings if findings is not None else load_dx()
    if not findings:
        return 0.0
    return round(sum(f.score for f in findings) / len(findings), 1)


def _any_match(root: Path, pattern: str) -> bool:
    if pattern.endswith("/"):
        return (root / pattern).exists()
    if any(ch in pattern for ch in "*?["):
        return bool(list(root.glob(pattern)))
    return (root / pattern).exists()
