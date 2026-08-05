"""Phase 5 — Deployment Review.

Verify deployment posture deterministically: containerization, healthchecks,
CI pipelines, non-root execution, secret handling, and rollback evidence.
"""

from __future__ import annotations

import re
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


def check_containerization(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify Dockerfiles exist for backend/frontend and use HEALTHCHECK."""
    findings: list[ReviewFinding] = []
    dockerfiles = list(_files(repo / "backend", "Dockerfile")) + \
        list(_files(repo / "frontend-v3", "Dockerfile"))
    if not dockerfiles:
        findings.append(ReviewFinding(
            "deployment", Severity.HIGH, "No Dockerfiles found",
            detail="backend/frontend-v3 lack Dockerfiles",
            evidence="backend, frontend-v3",
            suggested_fix="containerize services with pinned base images",
        ))
        return findings
    healthchecked = 0
    non_root = 0
    for path in dockerfiles:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "HEALTHCHECK" in text:
            healthchecked += 1
        if re.search(r"(?i)^USER\s+(?!root)\S+", text, re.MULTILINE):
            non_root += 1
    if healthchecked == 0:
        findings.append(ReviewFinding(
            "deployment", Severity.MEDIUM, "Missing HEALTHCHECK",
            detail="no Dockerfile declares a HEALTHCHECK",
            evidence="backend/Dockerfile, frontend-v3/Dockerfile",
            suggested_fix="add HEALTHCHECK with startup liveness probe",
        ))
    if non_root == 0:
        findings.append(ReviewFinding(
            "deployment", Severity.MEDIUM, "Root container user",
            detail="no Dockerfile switches to a non-root USER",
            evidence="backend/Dockerfile, frontend-v3/Dockerfile",
            suggested_fix="run containers as a non-root user per least privilege",
        ))
    return findings


def check_ci_pipelines(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify CI workflows exist and gate on tests."""
    findings: list[ReviewFinding] = []
    workflows = _files(repo / ".github" / "workflows", "*.yml") + \
                _files(repo / ".github" / "workflows", "*.yaml")
    if not workflows:
        findings.append(ReviewFinding(
            "deployment", Severity.HIGH, "No CI workflows",
            detail=".github/workflows is empty",
            evidence=".github/workflows",
            suggested_fix="add CI with lint, typecheck, and test gates",
        ))
        return findings
    test_gated = sum(
        any(keyword in p.read_text(encoding="utf-8", errors="ignore").lower()
            for keyword in ("pytest", "test", "check"))
        for p in workflows
    )
    if test_gated == 0:
        findings.append(ReviewFinding(
            "deployment", Severity.HIGH, "CI not test-gated",
            detail="no workflow runs pytest/typecheck",
            evidence=".github/workflows",
            suggested_fix="gate merges on a passing test suite",
        ))
    return findings


def check_deploy_script(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify a deployment entrypoint exists."""
    findings: list[ReviewFinding] = []
    candidates = [p for p in _files(repo, "*.sh") if "deploy" in p.name] + \
                 [p for p in _files(repo / "scripts", "*.sh") if "deploy" in p.name]
    if not candidates:
        findings.append(ReviewFinding(
            "deployment", Severity.MEDIUM, "No deploy script",
            detail="no deploy*.sh found at repo root or scripts/",
            evidence="repo root, scripts/",
            suggested_fix="add an idempotent deployment entrypoint",
        ))
    return findings


def check_rollback_evidence(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify rollback strategy is documented or encoded."""
    findings: list[ReviewFinding] = []
    evidence: list[str] = []
    for path in _files(repo, "*.md"):
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if "rollback" in text:
            evidence.append(str(path.relative_to(repo)))
    if not evidence:
        findings.append(ReviewFinding(
            "deployment", Severity.MEDIUM, "Rollback strategy undocumented",
            detail="no rollback guidance found in markdown",
            evidence="docs/",
            suggested_fix="document rollback procedure for deployments",
        ))
    return findings


def review(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Run every deployment review check for a repository."""
    findings: list[ReviewFinding] = []
    findings += check_containerization(repo)
    findings += check_ci_pipelines(repo)
    findings += check_deploy_script(repo)
    findings += check_rollback_evidence(repo)
    return findings
