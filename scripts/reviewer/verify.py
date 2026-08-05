"""Phase 11 — Change-set Verification (`reviewer-verify`).

Independent verification of a Builder change-set (GULA-BUILDER-001) before
merge. Resolves a mission to its changed files, runs deterministic scoped
checks across the eight review areas, and produces a ReviewReport gated on
the change-set ONLY — not the whole repository.

Change-set sources, in priority order:
  1. Files recorded on the mission (orchestrator registry / builder checkpoints)
  2. Explicit file arguments passed on the CLI
  3. The git working-tree change-set relative to HEAD (--git)

Reuses the Reviewer severity/decision/scoring model (scripts.reviewer.core)
so a change-set verdict is comparable to a whole-repo verdict.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.kernel.core import REPO_ROOT, Severity, utcnow
from scripts.reviewer.core import (
    STATE_DIR,
    ReviewFinding,
    ReviewReport,
    decide_area,
    decide_overall,
    overall_score,
    score_area,
    write_json,
)

REVIEWER_VERIFY_PATH = REPO_ROOT / "REVIEWER_VERIFY_REPORT.md"
ORCHESTRATOR_REGISTRY = REPO_ROOT / ".ai" / "core" / "orchestrator" / "history" / "registry.json"
BUILDER_CHECKPOINT_DIR = REPO_ROOT / ".ai" / "core" / "builder" / "state" / "checkpoints"

# Security patterns shared with security_review.py.
SECRET_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"(?i)(password|passwd|pwd|secret|token|api[_-]?key|private[_-]?key)\s*=\s*['\"][^'\"]{6,}['\"]",
     "hardcoded credential literal"),
    (r"os\.environ\.get\(['\"][A-Z_]+['\"]\s*,\s*['\"][^'\"]{4,}['\"]",
     "env var with non-empty default credential"),
    (r"BEGIN [A-Z ]*PRIVATE KEY", "embedded private key"),
)

# Unsafe patterns shared with code_review.py.
UNSAFE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\beval\s*\(", "eval() used"),
    (r"\bexec\s*\(", "exec() used"),
    (r"os\.system\s*\(", "os.system used"),
    (r"subprocess\.(run|call|Popen)\([^)]*shell\s*=\s*True", "shell=True subprocess"),
)

DEAD_CODE_MARKERS: tuple[str, ...] = ("TODO", "FIXME", "HACK", "XXX")

EXCLUDED_PARTS = frozenset(
    {".venv", "site-packages", "node_modules", "migrations", "__pycache__", "dist", "build"}
)

LARGE_FILE_LINES = 800

PY_EXTENSIONS = frozenset({".py", ".pyi"})
TS_EXTENSIONS = frozenset({".ts", ".tsx"})

AREA_CHECKS: tuple[str, ...] = (
    "architecture",
    "code",
    "security",
    "tests",
    "deployment",
    "documentation",
    "performance",
    "knowledge",
)


def _git(args: list[str]) -> list[str]:
    """Run a git command at the repo root and return stdout lines ([] on error)."""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            return []
        return [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    except (OSError, subprocess.SubprocessError):
        return []


@dataclass
class MissionInfo:
    """Resolved mission metadata (found=False when unknown)."""

    mission_id: str
    found: bool = False
    objective: str = ""
    mission_type: str = ""
    status: str = ""
    recorded_files: list[str] = field(default_factory=list)


def _read_registry() -> dict[str, Any]:
    if not ORCHESTRATOR_REGISTRY.exists():
        return {}
    try:
        import json

        return json.loads(ORCHESTRATOR_REGISTRY.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


def resolve_mission(mission_id: str) -> MissionInfo:
    """Resolve a mission id to its metadata + recorded change-set files."""
    info = MissionInfo(mission_id=mission_id)
    if not mission_id:
        return info

    registry = _read_registry()
    missions = registry.get("missions", {}) if isinstance(registry, dict) else {}
    normalized = mission_id.upper()
    for key, entry in missions.items():
        if key.upper() == normalized:
            info.found = True
            info.objective = str(entry.get("objective", ""))
            info.mission_type = str(entry.get("mission_type", ""))
            info.status = str(entry.get("status", ""))
            files = entry.get("files") or entry.get("changed_files") or []
            info.recorded_files = [str(f) for f in files]
            break
    return info


def changeset_files(
    mission: MissionInfo,
    explicit: tuple[str, ...] = (),
    use_git: bool = False,
) -> list[Path]:
    """Determine the change-set as existing, repo-relative Paths."""
    collected: list[str] = list(mission.recorded_files)
    collected.extend(explicit)

    if use_git or not collected:
        tracked = _git(["diff", "--name-only", "HEAD"])
        porcelain = _git(["status", "--porcelain"])
        untracked = [ln.split(" ", 1)[1].strip() for ln in porcelain
                     if ln.startswith("?? ")]
        collected.extend(tracked)
        collected.extend(untracked)

    seen: set[str] = set()
    paths: list[Path] = []
    for raw in collected:
        rel = raw.strip().replace("\\", "/")
        if not rel or rel in seen:
            continue
        seen.add(rel)
        path = REPO_ROOT / rel
        if path.exists() and path.is_file():
            paths.append(Path(rel))
    return sorted(paths)


def _py_files(paths: list[Path]) -> list[Path]:
    return [p for p in paths if p.suffix in PY_EXTENSIONS and p.name != "__init__.py"]


def _read(path: Path) -> str:
    try:
        return (REPO_ROOT / path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _strip_strings(text: str) -> str:
    strings_re = re.compile(r"""(['"])(?:\\.|(?!\1).)*\1""", re.DOTALL)
    return strings_re.sub("''", text)


def _count_ruff_violations(stdout: str) -> int:
    """Count ruff violations from its output deterministically.

    Ruff ends with `Found N error(s).` / `Found N violation(s).` in every
    format; parse that summary and fall back to counting full-format frame
    lines (`  --> path:line:col`) when the summary is absent.
    """
    match = re.search(r"Found (\d+) (?:errors?|violations?)\.", stdout)
    if match:
        return int(match.group(1))
    return sum(1 for ln in stdout.splitlines() if ln.lstrip().startswith("--> "))


# --------------------------------------------------------------------------
# Scoped checks — each maps to one review area and returns list[ReviewFinding].
# --------------------------------------------------------------------------

def check_architecture(paths: list[Path]) -> list[ReviewFinding]:
    """Layer consistency: routes need services, services must not import routes."""
    findings: list[ReviewFinding] = []

    service_by_route: dict[str, Path] = {}
    for path in paths:
        parts = path.parts
        if len(parts) >= 4 and parts[0] == "backend" and parts[1] == "app":
            if parts[2] == "routes" and path.name.endswith(".py"):
                service_by_route[path.stem] = path
            if parts[2] == "services" and path.name.endswith("_service.py"):
                service_by_route.setdefault(path.stem[: -len("_service")], path)

    for stem in sorted(service_by_route):
        if not (REPO_ROOT / "backend" / "app" / "services" / f"{stem}_service.py").exists():
            findings.append(ReviewFinding(
                "architecture", Severity.MEDIUM, "Route without extracted service",
                detail=f"route/module `{stem}` has no matching service "
                       f"backend/app/services/{stem}_service.py",
                evidence=service_by_route[stem].as_posix(),
                suggested_fix="extract the route logic into a service module",
            ))

    for path in paths:
        if (len(path.parts) >= 3 and path.parts[:2] == ("backend", "app")
                and path.parts[2] != "routes"):
            text = _read(path)
            if "from ..routes" in text or "from .routes" in text or "import routes" in text:
                findings.append(ReviewFinding(
                    "architecture", Severity.HIGH, "Layer inversion — routes imported below routes",
                    detail=f"{path.as_posix()} imports the routes layer",
                    evidence=path.name,
                    suggested_fix="depend on services/interfaces, never on routes",
                ))
    return findings


def check_code(paths: list[Path]) -> list[ReviewFinding]:
    """Ruff, unsafe patterns, and dead-code markers on changed Python files."""
    findings: list[ReviewFinding] = []
    py_files = _py_files(paths)

    if py_files:
        ruff = REPO_ROOT / "backend" / ".venv" / "bin" / "ruff"
        if ruff.exists():
            try:
                proc = subprocess.run(
                    [str(ruff), "check", *[str(REPO_ROOT / p) for p in py_files]],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if proc.returncode != 0:
                    violations = _count_ruff_violations(proc.stdout)
                    findings.append(ReviewFinding(
                        "code", Severity.HIGH, "Ruff violations in change-set",
                        detail=f"ruff found {violations} violation(s) across "
                               f"{len(py_files)} changed file(s)",
                        evidence="; ".join(p.as_posix() for p in py_files[:3]),
                        suggested_fix="run `ruff check --fix` on the change-set before merge",
                    ))
            except (OSError, subprocess.SubprocessError):
                pass

    for path in py_files:
        text = _read(path)
        code = _strip_strings(text)
        for pattern, label in UNSAFE_PATTERNS:
            if re.search(pattern, code):
                findings.append(ReviewFinding(
                    "code", Severity.HIGH, label,
                    detail=f"found in {path.as_posix()}",
                    evidence=path.name,
                    suggested_fix="remove the unsafe construct",
                ))

    marker_count = 0
    for path in paths:
        if path.suffix in PY_EXTENSIONS | TS_EXTENSIONS:
            for marker in DEAD_CODE_MARKERS:
                marker_count += _read(path).count(marker)
    if marker_count:
        findings.append(ReviewFinding(
            "code", Severity.LOW, "Dead-code markers in change-set",
            detail=f"{marker_count} TODO/FIXME/HACK/XXX marker(s) in changed files",
            evidence=paths[0].as_posix(),
            suggested_fix="resolve or ticket each marker before merge",
        ))
    return findings


def check_security(paths: list[Path]) -> list[ReviewFinding]:
    """Hardcoded secrets/credentials in the change-set."""
    findings: list[ReviewFinding] = []
    credential_pattern = SECRET_PATTERNS[0][0]
    for path in paths:
        if path.suffix not in PY_EXTENSIONS and path.suffix not in {".yml", ".yaml", ".toml", ".json"}:
            continue
        if path.suffix in PY_EXTENSIONS and ("test" in path.name or "conftest" in path.name):
            continue
        raw = _read(path)
        code = _strip_strings(raw) if path.suffix in PY_EXTENSIONS else raw
        # Credential-literal assignments must be matched on raw text (the
        # string-stripping pass would erase the literal we are looking for).
        if re.findall(credential_pattern, raw):
            findings.append(ReviewFinding(
                "security", Severity.HIGH, "hardcoded credential literal",
                detail=f"found in {path.as_posix()}",
                evidence=path.name,
                suggested_fix="load credentials from environment or a vault; never commit literals",
            ))
        for pattern, label in SECRET_PATTERNS[1:]:
            matches = re.findall(pattern, code)
            if matches:
                findings.append(ReviewFinding(
                    "security", Severity.HIGH, label,
                    detail=f"{len(matches)} match(es) in {path.as_posix()}",
                    evidence=path.name,
                    suggested_fix="load credentials from environment or a vault; never commit literals",
                ))
    return findings


def _test_candidates(path: Path) -> list[str]:
    """Candidate test paths for a changed file (repo-relative)."""
    name = path.name
    stem = path.stem
    parts = path.parts

    if len(parts) >= 2 and parts[0] == "backend" and parts[1] == "app":
        if name.startswith("test_") or name.endswith("_test.py"):
            return []
        return [f"backend/tests/unit/test_{stem}.py",
                f"backend/tests/test_{stem}.py"]

    if parts[0] == "scripts" and len(parts) >= 3:
        engine = parts[1]
        return [f"backend/tests/unit/test_{engine}_{stem}.py"]

    if parts[0] == "frontend-v3" and len(parts) >= 3 and parts[1] == "src":
        if ".test." in name or ".spec." in name:
            return []
        return [f"frontend-v3/src/__tests__/{stem}.test.ts",
                f"frontend-v3/src/__tests__/{stem}.test.tsx"]

    return []


def check_tests(paths: list[Path]) -> list[ReviewFinding]:
    """A test must exist for each changed production module."""
    findings: list[ReviewFinding] = []
    for path in paths:
        candidates = _test_candidates(path)
        if not candidates:
            continue
        if not any((REPO_ROOT / c).exists() for c in candidates):
            findings.append(ReviewFinding(
                "tests", Severity.MEDIUM, "Changed module lacks a test",
                detail=f"no test found for {path.as_posix()}",
                evidence=path.name,
                suggested_fix="add a regression test alongside the change",
            ))
    return findings


def check_documentation(paths: list[Path]) -> list[ReviewFinding]:
    """Public API / new-module changes should ship with documentation."""
    findings: list[ReviewFinding] = []
    public_change = any(
        len(p.parts) >= 3 and p.parts[:2] in {("backend", "app"), ("frontend-v3", "src")}
        for p in paths
    )
    new_module = any(
        p.parts[0] == ".ai" and len(p.parts) >= 4 and p.parts[2] not in {"registry", "index"}
        for p in paths
    )
    docs_changed = any(p.suffix == ".md" for p in paths)
    adr_changed = any(p.suffix == ".md" and "adr" in p.as_posix().lower() for p in paths)
    if (public_change or new_module) and not docs_changed:
        findings.append(ReviewFinding(
            "documentation", Severity.MEDIUM, "Change-set lacks documentation",
            detail="public API, frontend, or new knowledge module changed without a doc update",
            evidence="; ".join(p.as_posix() for p in paths[:3]),
            suggested_fix="add an ADR or doc update covering the change",
        ))
    if new_module and not adr_changed:
        findings.append(ReviewFinding(
            "documentation", Severity.MEDIUM, "New module lacks an ADR",
            detail="a new .ai/core module was added without an architecture decision record",
            evidence="; ".join(p.as_posix() for p in paths[:3]),
            suggested_fix="record an ADR describing the new module",
        ))
    return findings


def check_deployment(paths: list[Path]) -> list[ReviewFinding]:
    """Infra/deploy changes should be documented (rollback-aware)."""
    findings: list[ReviewFinding] = []
    infra = [p for p in paths
             if "Dockerfile" in p.name or "docker-compose" in p.name
             or p.as_posix().startswith(".github/workflows/")
             or p.name.startswith("deploy") or "deploy" in p.as_posix().lower()]
    docs_changed = any(p.suffix == ".md" for p in paths)
    if infra and not docs_changed:
        findings.append(ReviewFinding(
            "deployment", Severity.MEDIUM, "Deployment change lacks documentation",
            detail=f"{len(infra)} infra/deploy file(s) changed without a doc update",
            evidence=infra[0].as_posix(),
            suggested_fix="document the deployment/rollback impact of the change",
        ))
    return findings


def check_performance(paths: list[Path]) -> list[ReviewFinding]:
    """Flag oversized changed files (maintainability/performance risk)."""
    findings: list[ReviewFinding] = []
    for path in paths:
        if path.suffix not in PY_EXTENSIONS | TS_EXTENSIONS:
            continue
        line_count = _read(path).count("\n") + 1
        if line_count > LARGE_FILE_LINES:
            findings.append(ReviewFinding(
                "performance", Severity.MEDIUM, "Oversized file in change-set",
                detail=f"{path.as_posix()} is {line_count} lines (> {LARGE_FILE_LINES})",
                evidence=path.name,
                suggested_fix="split the file into focused modules",
            ))
    return findings


def check_knowledge(paths: list[Path]) -> list[ReviewFinding]:
    """Engine/architecture changes must be recorded in the registry + index."""
    findings: list[ReviewFinding] = []
    knowledge_change = any(
        p.as_posix().startswith("scripts/")
        or (p.parts[0] == ".ai" and len(p.parts) >= 3)
        or (len(p.parts) >= 2 and p.parts[:2] == ("docs", "architecture"))
        for p in paths
    )
    if knowledge_change:
        registry_updated = any(
            p.as_posix().endswith(("REGISTRY.md", "INDEX.md", "PROJECT_BRAIN.md"))
            for p in paths
        )
        if not registry_updated:
            findings.append(ReviewFinding(
                "knowledge", Severity.MEDIUM, "Registry/index not updated",
                detail="scripts/ or .ai/ changed without updating the knowledge registry/index",
                evidence="; ".join(p.as_posix() for p in paths[:3]),
                suggested_fix="update .ai/core/registry/REGISTRY.md and .ai/core/index/INDEX.md",
            ))
    return findings


AREA_FUNCTION: dict[str, Any] = {
    "architecture": check_architecture,
    "code": check_code,
    "security": check_security,
    "tests": check_tests,
    "deployment": check_deployment,
    "documentation": check_documentation,
    "performance": check_performance,
    "knowledge": check_knowledge,
}


def review_changeset(
    mission_id: str,
    explicit_files: tuple[str, ...] = (),
    use_git: bool = False,
    repo: Path = REPO_ROOT,
) -> tuple[ReviewReport, MissionInfo, list[Path]]:
    """Verify a Builder change-set and produce a scoped ReviewReport."""
    mission = resolve_mission(mission_id)
    paths = changeset_files(mission, explicit=explicit_files, use_git=use_git)

    area_reviews: list[Any] = []
    for area in AREA_CHECKS:
        findings = AREA_FUNCTION[area](paths)
        area_reviews.append(type(
            "AreaReview",
            (),
            {"area": area, "findings": findings,
             "score": score_area(findings), "decision": decide_area(findings)},
        ))

    empty_findings: list[ReviewFinding] = []
    if not paths:
        empty_findings = [ReviewFinding(
            "architecture", Severity.HIGH, "Empty change-set",
            detail=f"no files resolved for mission {mission_id}",
            evidence=mission_id,
            suggested_fix="pass file arguments or use --git to resolve the change-set",
        )]

    from scripts.reviewer.core import AreaReview

    reviews = [AreaReview(
        area=a.area, findings=a.findings, score=a.score, decision=a.decision
    ) for a in area_reviews]
    if empty_findings:
        reviews = [
            AreaReview(
                area="architecture",
                findings=empty_findings,
                score=score_area(empty_findings),
                decision=decide_area(empty_findings),
            ),
            *(a for a in reviews if a.area != "architecture"),
        ]

    report = ReviewReport(
        target=f"changeset:{mission_id}",
        mission_id=mission_id,
        area_reviews=reviews,
        decision=decide_overall(reviews),
        overall_score=overall_score(reviews),
        reviewed_at=utcnow(),
    )
    return report, mission, paths


def write_report(report: ReviewReport, paths: list[Path]) -> Path:
    """Persist the change-set review JSON and render the markdown report."""
    from scripts.reviewer.decision import summary_lines

    data = report.to_dict()
    data["files"] = [str(p) for p in paths]
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    write_json(STATE_DIR / "latest_verify.json", data)

    sections = [
        "# REVIEWER_VERIFY_REPORT.md",
        "",
        "Scoped change-set verdict from GULA-REVIEWER-001 (`reviewer-verify`).",
        "",
        "```",
        *summary_lines(report),
        "```",
        "",
        "## Change-set",
        "",
    ]
    if paths:
        sections.append("| File |")
        sections.append("|---|---|")
        for path in paths:
            sections.append(f"| `{path.as_posix()}` |")
    else:
        sections.append("_no files resolved_")
    sections.append("")
    sections.append("## Area Findings")
    sections.append("")
    for area in report.area_reviews:
        sections.append(f"### {area.area} — {area.decision} (score {area.score:.1f})")
        sections.append("")
        if not area.findings:
            sections.append("_no findings_")
        else:
            sections.append("| Severity | Title | Detail | Evidence | Suggested fix |")
            sections.append("|---|---|---|---|---|")
            for f in area.findings:
                sections.append(
                    f"| {f.severity.value} | {f.title} | {f.detail} | "
                    f"`{f.evidence}` | {f.suggested_fix} |"
                )
        sections.append("")
    sections.append("---")
    sections.append(f"Reviewed at: {report.reviewed_at}")
    sections.append(f"Overall score: {report.overall_score:.1f}/100 — {report.decision}")
    sections.append("")
    REVIEWER_VERIFY_PATH.write_text("\n".join(sections), encoding="utf-8")
    return REVIEWER_VERIFY_PATH


def gate(report: ReviewReport) -> int:
    """0 = pass (PASS / PASS WITH WARNINGS), 1 = reject."""
    return 1 if report.decision == "REJECT" else 0


def self_check() -> list[str]:
    """Self-checks for the Reviewer self-check command."""
    failures: list[str] = []
    if set(AREA_CHECKS) != {"architecture", "code", "security", "tests",
                            "deployment", "documentation", "performance", "knowledge"}:
        failures.append("verify area coverage does not match the 8 review areas")
    mission = resolve_mission("__UNKNOWN__")
    if mission.found:
        failures.append("resolve_mission matched an unknown id")
    return failures
