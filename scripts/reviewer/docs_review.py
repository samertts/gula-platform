"""Phase 6 — Documentation Review.

Verify documentation quality deterministically: presence of core docs,
API documentation, ADRs, security docs, and stale/broken markdown signals.
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


def check_core_docs(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify required top-level documentation exists."""
    findings: list[ReviewFinding] = []
    required = {
        "README.md": "project readme",
        "docs/architecture/ARCHITECTURE.md": "architecture overview",
        "SECURITY.md": "security policy",
        "LICENSE": "license",
    }
    for name, label in required.items():
        if not (repo / name).exists():
            findings.append(ReviewFinding(
                "documentation", Severity.MEDIUM, f"Missing {label}",
                detail=f"{name} not found at expected path",
                evidence="repo",
                suggested_fix=f"add {name} with the {label}",
            ))
    return findings


def check_api_docs(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify API documentation or OpenAPI schema exists."""
    findings: list[ReviewFinding] = []
    openapi = _files(repo / "docs", "*.json") + _files(repo / "docs", "*.yaml")
    openapi = [p for p in openapi if "openapi" in p.name.lower() or "api" in p.name.lower()]
    docs_md = [p for p in _files(repo / "docs", "*.md") if "api" in p.name.lower()]
    if not openapi and not docs_md:
        findings.append(ReviewFinding(
            "documentation", Severity.MEDIUM, "No API documentation",
            detail="no OpenAPI schema or api*.md found under docs/",
            evidence="docs/",
            suggested_fix="publish OpenAPI schema or an API reference",
        ))
    return findings


def check_adr_presence(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify ADR directory has records."""
    findings: list[ReviewFinding] = []
    adrs = _files(repo / "docs" / "adr", "*.md")
    if not adrs:
        findings.append(ReviewFinding(
            "documentation", Severity.HIGH, "No ADRs",
            detail="docs/adr is empty",
            evidence="docs/adr",
            suggested_fix="record architectural decisions as ADRs",
        ))
    return findings


def check_security_docs(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify security documentation exists."""
    findings: list[ReviewFinding] = []
    sec = _files(repo / "docs" / "security", "*.md") + [p for p in _files(repo, "*.md") if p.name.upper() == "SECURITY.MD"]
    if not sec:
        findings.append(ReviewFinding(
            "documentation", Severity.MEDIUM, "No security documentation",
            detail="docs/security is empty and no SECURITY.md found",
            evidence="docs/security",
            suggested_fix="document security model and responsible disclosure",
        ))
    return findings


def check_stale_docs(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Flag markdown files with no non-whitespace content."""
    findings: list[ReviewFinding] = []
    for path in _files(repo / "docs", "*.md"):
        if not path.read_text(encoding="utf-8", errors="ignore").strip():
            findings.append(ReviewFinding(
                "documentation", Severity.LOW, "Empty doc file",
                detail=f"{path.relative_to(repo)} has no content",
                evidence=path.name,
                suggested_fix="fill in or remove the placeholder document",
            ))
    return findings


def review(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Run every documentation review check for a repository."""
    findings: list[ReviewFinding] = []
    findings += check_core_docs(repo)
    findings += check_api_docs(repo)
    findings += check_adr_presence(repo)
    findings += check_security_docs(repo)
    findings += check_stale_docs(repo)
    return findings
