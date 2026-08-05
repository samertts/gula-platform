"""Phase 4 — Test Review.

Verify test coverage signals deterministically: test presence, per-module
mapping to tests, backend/frontend test counts, and assertion quality.
Does NOT execute tests (that is the validation engine's job).
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.kernel.core import REPO_ROOT, Severity
from scripts.reviewer.core import ReviewFinding


def _py_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    excluded = {".venv", "site-packages", "node_modules", "migrations", "__pycache__", "dist", "build"}
    return sorted(
        p for p in root.rglob("*.py")
        if "__pycache__" not in p.parts
        and not any(part in excluded for part in p.parts)
    )


def check_test_presence(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify backend and frontend test suites exist."""
    findings: list[ReviewFinding] = []
    backend_tests = _py_files(repo / "backend" / "tests")
    if not backend_tests:
        findings.append(ReviewFinding(
            "tests", Severity.HIGH, "Backend tests absent",
            detail="backend/tests contains no python test files",
            evidence="backend/tests",
            suggested_fix="add pytest suites for backend services",
        ))
    frontend_tests = list((repo / "frontend-v3").rglob("*.test.ts")) if (repo / "frontend-v3").exists() else []
    if not frontend_tests:
        findings.append(ReviewFinding(
            "tests", Severity.MEDIUM, "Frontend tests absent",
            detail="no *.test.ts found under frontend-v3",
            evidence="frontend-v3",
            suggested_fix="add vitest suites for UI components",
        ))
    return findings


def check_module_coverage(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Map service modules to test files; flag services without any test."""
    findings: list[ReviewFinding] = []
    services = [p for p in _py_files(repo / "backend" / "app" / "services")]
    test_texts = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in _py_files(repo / "backend" / "tests"))
    untested: list[str] = []
    for service in services:
        stem = service.stem
        # Import reference patterns: import ..services.<stem> / from ..<stem> import
        if re.search(rf"\b{stem}\b", test_texts):
            continue
        if f"{stem}_service" in test_texts:
            continue
        untested.append(service.name)
    if untested:
        findings.append(ReviewFinding(
            "tests", Severity.MEDIUM, "Services without test references",
            detail=f"{len(untested)} services never referenced by tests "
                   f"(e.g. {', '.join(sorted(untested)[:5])})",
            evidence="backend/app/services",
            suggested_fix="add unit or integration tests for each service module",
        ))
    return findings


def check_assertion_quality(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Flag test files that assert too little relative to their size."""
    findings: list[ReviewFinding] = []
    for path in _py_files(repo / "backend" / "tests"):
        if path.name in {"conftest.py", "fakes.py", "fixtures.py"} or "fixtures" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = len(text.splitlines())
        assertions = len(re.findall(r"\bassert\s", text))
        if lines > 200 and assertions < max(2, lines // 60):
            findings.append(ReviewFinding(
                "tests", Severity.LOW, "Thin assertions",
                detail=f"{path.name}: {assertions} asserts in {lines} lines",
                evidence=path.name,
                suggested_fix="assert on behavior, not just execution paths",
            ))
    return findings


def check_test_count_health(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Report the raw number of test definitions found."""
    findings: list[ReviewFinding] = []
    backend = sum(
        len(re.findall(r"\bdef\s+test_|^class\s+Test", p.read_text(encoding="utf-8", errors="ignore")))
        for p in _py_files(repo / "backend" / "tests")
    )
    frontend = sum(
        len(re.findall(r"\btest\(['\"]|^\s*test\b", p.read_text(encoding="utf-8", errors="ignore")))
        for p in (repo / "frontend-v3").rglob("*.test.ts")
    ) if (repo / "frontend-v3").exists() else 0
    if backend < 100:
        findings.append(ReviewFinding(
            "tests", Severity.MEDIUM, "Backend test count low",
            detail=f"~{backend} test definitions found",
            evidence="backend/tests",
            suggested_fix="expand backend coverage beyond 100 tests",
        ))
    return findings


def review(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Run every test review check for a repository."""
    findings: list[ReviewFinding] = []
    findings += check_test_presence(repo)
    findings += check_module_coverage(repo)
    findings += check_assertion_quality(repo)
    findings += check_test_count_health(repo)
    return findings
