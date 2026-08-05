"""Phase 1 — Architecture Review.

Verify: Clean Architecture, SOLID, dependency direction, module boundaries,
ADR compliance, and constitution compliance. Produces ReviewFinding records
with evidence. Deterministic; no I/O at import time.
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.kernel.core import REPO_ROOT, Severity
from scripts.reviewer.core import ReviewFinding

# Layered directories that must keep their direction (routes -> services).
ARCHITECTURE_LAYERS: dict[str, tuple[str, ...]] = {
    "routes": ("backend/app/routes",),
    "services": ("backend/app/services",),
    "models": ("backend/app/models",),
}


def _files(root: Path, glob: str) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob(glob))


def check_clean_architecture(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify route/service/model layering exists and routes stay thin."""
    findings: list[ReviewFinding] = []

    routes = _files(repo / "backend/app/routes", "*.py")
    services = _files(repo / "backend/app/services", "*.py")
    models = _files(repo / "backend/app/models", "*.py")
    fat: list[str] = []

    if not routes:
        findings.append(ReviewFinding(
            "architecture", Severity.HIGH, "No routes layer",
            detail="backend/app/routes is empty", evidence=str(repo / "backend/app/routes"),
            suggested_fix="add API routes before claiming layered architecture",
        ))
    if not services:
        findings.append(ReviewFinding(
            "architecture", Severity.MEDIUM, "No services layer",
            detail="backend/app/services is empty", evidence=str(repo / "backend/app/services"),
            suggested_fix="extract business logic from routes into services",
        ))
    if not models:
        findings.append(ReviewFinding(
            "architecture", Severity.MEDIUM, "No models layer",
            detail="backend/app/models is empty", evidence=str(repo / "backend/app/models"),
            suggested_fix="define persistent models in a dedicated models layer",
        ))

    for route in routes:
        text = route.read_text(encoding="utf-8", errors="ignore")
        if text.count("app.") > 200 or len(text.splitlines()) > 500:
            fat.append(route.relative_to(repo).as_posix())
    if fat:
        findings.append(ReviewFinding(
            "architecture", Severity.MEDIUM, "Fat routes",
            detail=f"{len(fat)} routes exceed the 500-line / 200-call threshold "
                   f"(e.g. {Path(fat[0]).name})",
            evidence="backend/app/routes",
            suggested_fix="delegate logic to service modules to keep routes thin",
        ))
    return findings


def check_solid_signals(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Check for dependency-inversion and interface signals in services."""
    findings: list[ReviewFinding] = []
    services = _files(repo / "backend/app/services", "*.py")
    injected = 0
    for service in services:
        text = service.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"def __init__\(self.*session|def __init__\(self.*repo|def __init__\(self.*db", text):
            injected += 1
    if services and injected < len(services) * 0.3:
        findings.append(ReviewFinding(
            "architecture", Severity.MEDIUM, "Low dependency injection usage",
            detail=f"{injected}/{len(services)} services inject dependencies",
            evidence="backend/app/services",
            suggested_fix="prefer constructor injection of session/repository",
        ))
    return findings


def check_module_boundaries(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify bounded-context directories exist and are discoverable."""
    findings: list[ReviewFinding] = []
    core_dirs = [
        "backend/app/ehr", "backend/app/national", "backend/app/identity",
        "backend/app/clinical", "backend/app/audit",
    ]
    present = [d for d in core_dirs if (repo / d).exists()]
    if len(present) < len(core_dirs) * 0.5:
        findings.append(ReviewFinding(
            "architecture", Severity.MEDIUM, "Module boundaries incomplete",
            detail=f"{len(present)}/{len(core_dirs)} core bounded contexts present",
            evidence=", ".join(core_dirs),
            suggested_fix="declare remaining bounded contexts explicitly",
        ))
    return findings


def check_adr_compliance(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify ADRs exist and follow the approved naming/status convention."""
    findings: list[ReviewFinding] = []
    adr_dir = repo / "docs" / "adr"
    adrs = _files(adr_dir, "*.md")
    if not adrs:
        findings.append(ReviewFinding(
            "architecture", Severity.HIGH, "No ADRs recorded",
            detail="docs/adr contains no architecture decision records",
            evidence="docs/adr",
            suggested_fix="record architecture decisions as ADRs",
        ))
        return findings
    malformed = 0
    for adr in adrs:
        text = adr.read_text(encoding="utf-8", errors="ignore")
        if not re.search(r"^#\s+ADR-\d+", text, re.MULTILINE):
            malformed += 1
    if malformed:
        findings.append(ReviewFinding(
            "architecture", Severity.MEDIUM, "ADR naming deviation",
            detail=f"{malformed}/{len(adrs)} ADRs missing 'ADR-<n>' heading",
            evidence="docs/adr",
            suggested_fix="rename ADRs to follow the ADR-<n> convention",
        ))
    return findings


def check_constitution_compliance(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Verify the constitution exists and is referenced by the codebase."""
    findings: list[ReviewFinding] = []
    constitution = repo / "AI_OPERATING_CONSTITUTION.md"
    if not constitution.exists():
        findings.append(ReviewFinding(
            "architecture", Severity.CRITICAL, "Constitution missing",
            detail="AI_OPERATING_CONSTITUTION.md not found",
            evidence="repo root",
            suggested_fix="restore the operating constitution",
        ))
        return findings
    references = 0
    for path in (repo / "AGENTS.md", repo / "CLAUDE.md", repo / "AI_BOOTSTRAP.md"):
        if path.exists() and "AI_OPERATING_CONSTITUTION" in path.read_text(encoding="utf-8", errors="ignore"):
            references += 1
    if references == 0:
        findings.append(ReviewFinding(
            "architecture", Severity.MEDIUM, "Constitution unreferenced",
            detail="governance docs do not reference the constitution",
            evidence="AGENTS.md, CLAUDE.md, AI_BOOTSTRAP.md",
            suggested_fix="reference AI_OPERATING_CONSTITUTION.md from governance docs",
        ))
    return findings


def review(repo: Path = REPO_ROOT) -> list[ReviewFinding]:
    """Run every architecture check for a repository."""
    findings: list[ReviewFinding] = []
    findings += check_clean_architecture(repo)
    findings += check_solid_signals(repo)
    findings += check_module_boundaries(repo)
    findings += check_adr_compliance(repo)
    findings += check_constitution_compliance(repo)
    return findings
