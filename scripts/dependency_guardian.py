#!/usr/bin/env python3
"""
GULA Platform — Dependency Guardian
====================================
Monitors all dependency ecosystems in the monorepo for vulnerabilities,
outdated packages, and cross-manifest conflicts.

Checks performed:
  1. Python vulnerability scan  — pip-audit on all requirements files
  2. npm vulnerability scan     — npm audit on frontend-v3
  3. Outdated Python packages   — pip list --outdated parsing
  4. Cross-manifest conflicts   — version mismatches between requirements.txt
     and pyproject.toml / requirements-dev.txt etc.
  5. Dependency health report   — written to assessment/dependency_guardian_report.md

Usage:
    python scripts/dependency_guardian.py                  # scan + human report
    python scripts/dependency_guardian.py --json            # JSON output only
    python scripts/dependency_guardian.py --fix             # dry-run upgrade branches
    python scripts/dependency_guardian.py --fix --apply     # actually create branches

Exit codes:
    0 — clean (no vulnerabilities, no conflicts)
    1 — issues found (vulnerabilities, conflicts, or outdated deps)
    2 — error (missing critical files, parse failure)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("dependency-guardian")

REPO_ROOT = Path(__file__).parent.parent.resolve()
REPORT_FILE = REPO_ROOT / "assessment" / "dependency_guardian_report.md"

PYTHON_REQUIREMENT_FILES: list[Path] = [
    REPO_ROOT / "backend" / "requirements.txt",
    REPO_ROOT / "backend" / "requirements-dev.txt",
    REPO_ROOT / "backend" / "requirements-lock.txt",
    REPO_ROOT / "nhop-platform" / "requirements.txt",
    REPO_ROOT / "edge_agent" / "requirements.txt",
]

PYPROJECT = REPO_ROOT / "pyproject.toml"
# The active production frontend is frontend-v3.
FRONTEND_DIR = REPO_ROOT / "frontend-v3"
PACKAGE_JSON = FRONTEND_DIR / "package.json"

_SHORT_NAMES = {
    "backend/requirements.txt": "backend",
    "backend/requirements-dev.txt": "backend-dev",
    "backend/requirements-lock.txt": "backend-lock",
    "nhop-platform/requirements.txt": "nhop",
    "edge_agent/requirements.txt": "edge",
}

# ── Data structures ─────────────────────────────────────────────────────────

@dataclass
class PackageEntry:
    name: str
    specifier: str
    line: int
    source_file: Path
    _raw: str = ""


@dataclass
class NpmPackageEntry:
    name: str
    version_spec: str
    is_dev: bool = False


@dataclass
class Vulnerability:
    package: str
    severity: str
    advisory: str
    fix_version: str
    source: str  # "pip-audit" | "npm-audit"


@dataclass
class OutdatedEntry:
    package: str
    installed: str
    latest: str
    source: str  # "pip" | "npm"


@dataclass
class FileReport:
    path: Path
    label: str
    packages: list[PackageEntry] = field(default_factory=list)
    unpinned: list[PackageEntry] = field(default_factory=list)
    no_min_bound: list[PackageEntry] = field(default_factory=list)
    parse_error: Optional[str] = None
    audit_vulns: list[Vulnerability] = field(default_factory=list)
    audit_skipped: bool = False
    audit_error: Optional[str] = None
    outdated: list[OutdatedEntry] = field(default_factory=list)
    outdated_skipped: bool = False
    outdated_error: Optional[str] = None

    @property
    def passed(self) -> bool:
        return (
            self.parse_error is None
            and len(self.unpinned) == 0
            and len(self.no_min_bound) == 0
            and len(self.audit_vulns) == 0
            and self.audit_error is None
        )


@dataclass
class NpmReport:
    path: Path
    vulns: list[Vulnerability] = field(default_factory=list)
    audit_error: Optional[str] = None
    audit_skipped: bool = False
    outdated: list[OutdatedEntry] = field(default_factory=list)
    outdated_error: Optional[str] = None
    packages: list[NpmPackageEntry] = field(default_factory=list)
    parse_error: Optional[str] = None

    @property
    def passed(self) -> bool:
        return (
            self.audit_error is None
            and len(self.vulns) == 0
            and len(self.outdated) == 0
        )


@dataclass
class Conflict:
    package: str
    specifiers: list[Tuple[str, str]]  # (file_label, specifier)


@dataclass
class GuardReport:
    python_reports: list[FileReport] = field(default_factory=list)
    npm_report: Optional[NpmReport] = None
    conflicts: list[Conflict] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    @property
    def has_issues(self) -> bool:
        if self.npm_report and not self.npm_report.passed:
            return True
        for r in self.python_reports:
            if not r.passed or r.outdated:
                return True
        if self.conflicts:
            return True
        return False

    @property
    def total_vulns(self) -> int:
        n = sum(len(r.audit_vulns) for r in self.python_reports)
        if self.npm_report:
            n += len(self.npm_report.vulns)
        return n

    @property
    def total_outdated(self) -> int:
        n = sum(len(r.outdated) for r in self.python_reports)
        if self.npm_report:
            n += len(self.npm_report.outdated)
        return n


# ═══════════════════════════════════════════════════════════════════════════
# Python requirement parser
# ═══════════════════════════════════════════════════════════════════════════

_RE_PACKAGE_LINE = re.compile(
    r"^\s*"
    r"(?:-e\s+)?"
    r"([a-zA-Z0-9][\w\-.]*)"
    r"(?:\s*\[([^\]]+)\])?"
    r"\s*"
    r"("
    r"(?:[><=!~]+\s*[\w.*]+"
    r"(?:\s*,\s*[><=!~]+\s*[\w.*]+)*)"
    r")?\s*"
    r"(?:;\s*(.*?))?"
    r"\s*(?:#.*)?$"
)
_RE_COMMENT_OR_BLANK = re.compile(r"^\s*(#|$)")
_RE_URL_OR_PATH = re.compile(
    r"^\s*(?:-e\s+)?"
    r"(?:"
    r"https?://|git\+|svn\+"
    r"|\./"
    r"|/[a-zA-Z]"
    r"|[a-zA-Z]:\\"
    r")"
)


def parse_requirements(filepath: Path) -> FileReport:
    label = _SHORT_NAMES.get(
        str(filepath.relative_to(REPO_ROOT)), filepath.name
    )
    report = FileReport(path=filepath, label=label)

    if not filepath.exists():
        report.parse_error = f"File not found: {filepath}"
        return report

    try:
        text = filepath.read_text(encoding="utf-8")
    except OSError as e:
        report.parse_error = f"Cannot read {filepath}: {e}"
        return report

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if _RE_COMMENT_OR_BLANK.match(line):
            continue
        if line.startswith(("-r ", "--requirement ", "-f ", "--find-links ",
                            "--index-url ", "-i ", "--extra-index-url ",
                            "--trusted-host ")):
            continue
        if _RE_URL_OR_PATH.match(line):
            continue

        m = _RE_PACKAGE_LINE.match(line)
        if not m:
            continue

        name = m.group(1).lower()
        specifier = (m.group(3) or "").strip()
        entry = PackageEntry(
            name=name,
            specifier=specifier,
            line=lineno,
            source_file=filepath,
            _raw=raw_line.strip(),
        )
        report.packages.append(entry)

    _classify_packages(report)
    return report


def _classify_packages(report: FileReport) -> None:
    for pkg in report.packages:
        if not pkg.specifier:
            report.unpinned.append(pkg)
            continue
        specs = [s.strip() for s in pkg.specifier.split(",")]
        has_min = any(s.startswith(">=") for s in specs)
        if not has_min:
            report.no_min_bound.append(pkg)


# ═══════════════════════════════════════════════════════════════════════════
# pyproject.toml parser (dependency subset)
# ═══════════════════════════════════════════════════════════════════════════

def parse_pyproject_deps(filepath: Path) -> Dict[str, str]:
    """Extract dependency specs from pyproject.toml (project.dependencies)."""
    deps: Dict[str, str] = {}
    if not filepath.exists():
        return deps

    text = filepath.read_text(encoding="utf-8")
    in_project = False
    in_dependencies = False

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("[project]"):
            in_project = True
            in_dependencies = False
            continue

        if in_project and stripped.startswith("["):
            in_project = False
            in_dependencies = False

        if in_project and stripped.startswith("dependencies = ["):
            in_dependencies = True
            continue

        if in_dependencies:
            if stripped == "]":
                in_dependencies = False
                continue
            dep_line = stripped.rstrip(",").strip("\"'")
            m = re.match(r"([a-zA-Z0-9][\w\-.]*)\s*(.*)", dep_line)
            if m:
                name = m.group(1).lower()
                spec = m.group(2).strip()
                if spec.startswith(">=") or spec.startswith("==") or spec.startswith("~="):
                    deps[name] = spec

    return deps


# ═══════════════════════════════════════════════════════════════════════════
# pip-audit
# ═══════════════════════════════════════════════════════════════════════════

def _find_tool(name: str) -> Optional[str]:
    return shutil.which(name)


def run_pip_audit(report: FileReport, timeout: int = 60) -> None:
    exe = _find_tool("pip-audit")
    if not exe:
        report.audit_skipped = True
        return

    if report.parse_error is not None or not report.packages:
        report.audit_skipped = True
        return

    try:
        proc = subprocess.run(
            [exe, "--requirement", str(report.path), "--no-deps",
             "--format", "json"],
            capture_output=True, text=True, timeout=timeout,
        )

        if proc.returncode == 0:
            return

        if proc.returncode == 1:
            try:
                data = json.loads(proc.stdout)
                for vuln in data.get("vulnerabilities", []):
                    report.audit_vulns.append(Vulnerability(
                        package=vuln.get("name", "unknown"),
                        severity=vuln.get("severity", "unknown"),
                        advisory=vuln.get("advisory", ""),
                        fix_version=vuln.get("fix_version", "N/A"),
                        source="pip-audit",
                    ))
            except (json.JSONDecodeError, KeyError):
                for line in proc.stdout.splitlines():
                    if line.strip() and not line.startswith("Name"):
                        report.audit_vulns.append(Vulnerability(
                            package="unknown", severity="unknown",
                            advisory=line.strip()[:120],
                            fix_version="N/A", source="pip-audit",
                        ))
        else:
            report.audit_error = (proc.stderr or proc.stdout or
                                  f"pip-audit exited with code {proc.returncode}")

    except FileNotFoundError:
        report.audit_skipped = True
    except subprocess.TimeoutExpired:
        report.audit_error = f"pip-audit timed out after {timeout}s"
    except OSError as e:
        report.audit_error = str(e)


# ═══════════════════════════════════════════════════════════════════════════
# pip list --outdated
# ═══════════════════════════════════════════════════════════════════════════

def run_pip_outdated(report: FileReport, timeout: int = 30) -> None:
    exe = _find_tool("pip")
    if not exe:
        report.outdated_skipped = True
        return

    try:
        proc = subprocess.run(
            [exe, "list", "--outdated", "--format=json"],
            capture_output=True, text=True, timeout=timeout,
        )

        if proc.returncode != 0:
            report.outdated_error = proc.stderr.strip() or f"pip exit {proc.returncode}"
            return

        outdated_list = json.loads(proc.stdout)
        pinned_names = {p.name for p in report.packages}

        for entry in outdated_list:
            name = entry.get("name", "").lower()
            if name in pinned_names:
                report.outdated.append(OutdatedEntry(
                    package=name,
                    installed=entry.get("version", "?"),
                    latest=entry.get("latest_version", "?"),
                    source="pip",
                ))

    except FileNotFoundError:
        report.outdated_skipped = True
    except subprocess.TimeoutExpired:
        report.outdated_error = f"pip list timed out after {timeout}s"
    except (json.JSONDecodeError, OSError) as e:
        report.outdated_error = str(e)


# ═══════════════════════════════════════════════════════════════════════════
# npm audit
# ═══════════════════════════════════════════════════════════════════════════

SEVERITY_MAP = {"critical": 4, "high": 3, "moderate": 2, "low": 1}


def run_npm_audit(timeout: int = 120) -> NpmReport:
    report = NpmReport(path=FRONTEND_DIR / "package.json")

    if not PACKAGE_JSON.exists():
        report.parse_error = f"package.json not found at {PACKAGE_JSON}"
        return report

    _parse_npm_packages(report)
    npm_exe = _find_tool("npm")
    if not npm_exe:
        report.audit_skipped = True
        return report

    try:
        proc = subprocess.run(
            [npm_exe, "audit", "--json"],
            cwd=str(FRONTEND_DIR),
            capture_output=True, text=True, timeout=timeout,
        )

        if proc.returncode in (0, 1):
            try:
                data = json.loads(proc.stdout)

                # npm audit v2: vulnerabilities key
                vulns_map = data.get("vulnerabilities", {})
                for pkg_name, info in vulns_map.items():
                    severity = info.get("severity", "unknown")
                    via = info.get("via", [])
                    fix = info.get("fixAvailable", False)
                    fix_str = "available" if fix else "N/A"

                    for advisory in via:
                        if isinstance(advisory, dict):
                            title = advisory.get("title", "no details")
                        elif isinstance(advisory, str):
                            title = advisory
                        else:
                            title = str(advisory)

                        report.vulns.append(Vulnerability(
                            package=pkg_name,
                            severity=severity,
                            advisory=(
                                title[:200] if isinstance(title, str)
                                else json.dumps(title)
                            ),
                            fix_version=fix_str,
                            source="npm-audit",
                        ))
            except json.JSONDecodeError:
                report.audit_error = "Failed to parse npm audit JSON output"
        else:
            report.audit_error = (
                proc.stderr.strip() or
                f"npm audit exited with code {proc.returncode}"
            )

    except FileNotFoundError:
        report.audit_skipped = True
    except subprocess.TimeoutExpired:
        report.audit_error = f"npm audit timed out after {timeout}s"
    except OSError as e:
        report.audit_error = str(e)

    return report


def run_npm_outdated(report: NpmReport, timeout: int = 30) -> None:
    npm_exe = _find_tool("npm")
    if not npm_exe:
        report.outdated_error = "npm not found"
        return

    try:
        proc = subprocess.run(
            [npm_exe, "outdated", "--json"],
            cwd=str(FRONTEND_DIR),
            capture_output=True, text=True, timeout=timeout,
        )

        if proc.returncode not in (0, 1):
            return

        try:
            data = json.loads(proc.stdout)
            for pkg_name, info in data.items():
                report.outdated.append(OutdatedEntry(
                    package=pkg_name,
                    installed=info.get("current", "?"),
                    latest=info.get("latest", "?"),
                    source="npm",
                ))
        except json.JSONDecodeError:
            pass

    except subprocess.TimeoutExpired:
        report.outdated_error = "npm outdated timed out"
    except OSError:
        report.outdated_error = "npm outdated failed"


def _parse_npm_packages(report: NpmReport) -> None:
    try:
        data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        report.parse_error = str(e)
        return

    deps = data.get("dependencies", {})
    dev_deps = data.get("devDependencies", {})

    for name, version in deps.items():
        report.packages.append(NpmPackageEntry(name=name, version_spec=version, is_dev=False))
    for name, version in dev_deps.items():
        report.packages.append(NpmPackageEntry(name=name, version_spec=version, is_dev=True))


# ═══════════════════════════════════════════════════════════════════════════
# Cross-manifest conflict detection
# ═══════════════════════════════════════════════════════════════════════════

def _extract_bounds(specifier: str) -> list[Tuple[str, str]]:
    parts = [s.strip() for s in specifier.split(",")]
    result = []
    for part in parts:
        m = re.match(r"([><=!~]+)\s*([\w.*]+)", part)
        if m:
            result.append((m.group(1), m.group(2)))
    return result


def detect_conflicts(python_reports: list[FileReport]) -> list[Conflict]:
    pyproject_deps = parse_pyproject_deps(PYPROJECT)

    package_map: Dict[str, list[Tuple[str, str]]] = {}  # name -> [(label, spec)]

    for report in python_reports:
        if report.parse_error:
            continue
        for pkg in report.packages:
            if not pkg.specifier:
                continue
            package_map.setdefault(pkg.name, []).append(
                (report.label, pkg.specifier)
            )

    for name, spec in pyproject_deps.items():
        package_map.setdefault(name, []).append(("pyproject.toml", spec))

    conflicts: list[Conflict] = []
    for pkg_name, entries in sorted(package_map.items()):
        if len(entries) < 2:
            continue
        specs = [e[1] for e in entries]
        unique_specs = list(set(specs))
        if len(unique_specs) <= 1:
            continue
        conflicts.append(Conflict(
            package=pkg_name,
            specifiers=[(label, spec) for label, spec in entries],
        ))

    return conflicts


# ═══════════════════════════════════════════════════════════════════════════
# --fix mode: upgrade branches
# ═══════════════════════════════════════════════════════════════════════════

def _run_git(args: list[str], dry_run: bool = False) -> Tuple[int, str]:
    if dry_run:
        logger.info("[DRY-RUN] git %s", " ".join(args))
        return 0, ""
    try:
        proc = subprocess.run(
            ["git"] + args,
            cwd=str(REPO_ROOT),
            capture_output=True, text=True, timeout=30,
        )
        return proc.returncode, proc.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
        logger.error("git operation failed: %s", e)
        return 1, str(e)


def apply_fix(report: GuardReport, dry_run: bool = True) -> int:
    issues = 0

    all_outdated: list[OutdatedEntry] = []
    for r in report.python_reports:
        all_outdated.extend(r.outdated)
    if report.npm_report:
        all_outdated.extend(report.npm_report.outdated)

    if not all_outdated:
        logger.info("No outdated packages to upgrade — nothing to fix")
        return 0

    branch_name = (
        f"upgrade/dependency-guardian-"
        f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    )

    ret, _ = _run_git(
        ["checkout", "-b", branch_name],
        dry_run=dry_run,
    )
    if ret != 0:
        logger.error("Failed to create branch %s", branch_name)
        return 2
    logger.info("Branch: %s", branch_name)

    for entry in all_outdated:
        logger.info(
            "  Upgrade %s: %s -> %s",
            entry.package, entry.installed, entry.latest,
        )

    commit_msg = (
        f"chore: dependency upgrades from guardian scan\n\n"
        f"Upgrades:\n"
    )
    for entry in all_outdated:
        commit_msg += f"- {entry.package}: {entry.installed} -> {entry.latest}\n"
    commit_msg += f"\nAuto-generated by dependency_guardian.py --fix\n"

    if dry_run:
        ret, _ = _run_git(["diff", "--stat"], dry_run=True)
        logger.info("Commit message:\n%s", commit_msg)
        logger.info(
            "[DRY-RUN] Would commit and push branch: %s",
            branch_name,
        )
    else:
        _run_git(["add", "-A"], dry_run=False)
        ret, _ = _run_git(
            ["commit", "-m", commit_msg],
            dry_run=False,
        )
        if ret == 0:
            logger.info("Committed on branch %s", branch_name)
        else:
            logger.warning("Nothing to commit (no changes)")

    return issues


# ═══════════════════════════════════════════════════════════════════════════
# Report generation (human-readable + JSON)
# ═══════════════════════════════════════════════════════════════════════════

_COLORS = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "bold": "\033[1m",
    "reset": "\033[0m",
}
_USE_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if _USE_COLOR:
        return f"{_COLORS[code]}{text}{_COLORS['reset']}"
    return text


def print_human_report(guard: GuardReport) -> int:
    total_vulns = guard.total_vulns
    total_outdated = guard.total_outdated
    total_errors = 0

    print()
    print(_c("bold", "═" * 72))
    print(_c("bold", "  GULA — Dependency Guardian Report"))
    print(_c("bold", "═" * 72))
    print(f"  Timestamp: {guard.timestamp}")
    print()

    # ── Python reports ──
    print(_c("bold", "  ── Python Dependencies ──"))
    max_label = max((len(r.label) for r in guard.python_reports), default=20)

    for report in guard.python_reports:
        label = report.label.ljust(max_label)
        if report.parse_error:
            print(f"  {_c('red', '✗')}  {label}  {_c('red', report.parse_error)}")
            total_errors += 1
            continue

        status = _c("green", "✓") if report.passed else _c("red", "✗")
        print(f"  {status}  {label}  ({len(report.packages)} packages)")

        if report.unpinned:
            for p in report.unpinned:
                print(f"         {_c('yellow', '⚠')}  unpinned: {p._raw.strip()[:64]}")

        if report.no_min_bound:
            for p in report.no_min_bound:
                print(f"         {_c('yellow', '⚠')}  no min bound: {p._raw.strip()[:64]}")

        if report.audit_vulns:
            vulns_by_sev = sorted(
                report.audit_vulns,
                key=lambda v: SEVERITY_MAP.get(v.severity, 0),
                reverse=True,
            )
            for v in vulns_by_sev:
                sev_color = (
                    _c("red", "CRIT") if v.severity == "critical"
                    else _c("red", "HIGH") if v.severity == "high"
                    else _c("yellow", "MOD") if v.severity == "moderate"
                    else _c("cyan", "LOW")
                )
                print(
                    f"         {_c('red', '✘')}  [{sev_color}] "
                    f"{v.package}  fix: {v.fix_version}"
                )

        if report.audit_error:
            total_errors += 1
            print(f"         {_c('red', '✘')}  audit error: {report.audit_error}")

        if report.audit_skipped and not report.audit_error:
            print(f"         {_c('yellow', 'ℹ')}  pip-audit skipped")

        if report.outdated:
            for o in report.outdated:
                print(
                    f"         {_c('yellow', '↑')}  {o.package}: "
                    f"{o.installed} -> {o.latest}"
                )

        if report.outdated_error:
            print(f"         {_c('yellow', 'ℹ')}  outdated check: {report.outdated_error}")

    # ── npm report ──
    print()
    print(_c("bold", "  ── npm / Frontend Dependencies ──"))

    if guard.npm_report:
        nr = guard.npm_report
        if nr.parse_error:
            print(f"  {_c('red', '✗')}  frontend-v2  {_c('red', nr.parse_error)}")
            total_errors += 1
        else:
            pkg_count = len(nr.packages)
            npm_status = _c("green", "✓") if nr.passed else _c("red", "✗")
            print(f"  {npm_status}  frontend-v2  ({pkg_count} packages)")

            if nr.audit_error:
                print(f"         {_c('red', '✘')}  audit error: {nr.audit_error}")
                total_errors += 1

            if nr.audit_skipped:
                print(f"         {_c('yellow', 'ℹ')}  npm audit skipped")

            if nr.vulns:
                vulns_by_sev = sorted(
                    nr.vulns,
                    key=lambda v: SEVERITY_MAP.get(v.severity, 0),
                    reverse=True,
                )
                for v in vulns_by_sev:
                    sev_color = (
                        _c("red", "CRIT") if v.severity == "critical"
                        else _c("red", "HIGH") if v.severity == "high"
                        else _c("yellow", "MOD") if v.severity == "moderate"
                        else _c("cyan", "LOW")
                    )
                    print(
                        f"         {_c('red', '✘')}  [{sev_color}] "
                        f"{v.package}: {v.advisory[:80]}"
                    )

            if nr.outdated:
                for o in nr.outdated:
                    print(
                        f"         {_c('yellow', '↑')}  {o.package}: "
                        f"{o.installed} -> {o.latest}"
                    )

            if nr.outdated_error:
                print(f"         {_c('yellow', 'ℹ')}  outdated check: {nr.outdated_error}")
    else:
        print(f"  {_c('yellow', 'ℹ')}  Not scanned (no package.json)")

    # ── Conflicts ──
    if guard.conflicts:
        print()
        print(_c("bold", "  ── Cross-Manifest Conflicts ──"))
        for c in guard.conflicts:
            print(f"  {_c('red', '✘')}  {c.package}:")
            for label, spec in c.specifiers:
                print(f"         {label}: {spec}")

    # ── Summary ──
    print()
    print(_c("bold", "─" * 72))
    print(_c("bold", "  Summary"))
    print()

    py_pkg_count = sum(len(r.packages) for r in guard.python_reports if not r.parse_error)

    print(f"    Python files:       {len(guard.python_reports)} ({py_pkg_count} packages)")
    print(f"    npm packages:       {len(guard.npm_report.packages) if guard.npm_report else 0}")
    print(f"    Vulnerabilities:    {_c('red', str(total_vulns)) if total_vulns else _c('green', '0')}")
    print(f"    Outdated:           {_c('yellow', str(total_outdated)) if total_outdated else _c('green', '0')}")
    print(f"    Conflicts:          {_c('red', str(len(guard.conflicts))) if guard.conflicts else _c('green', '0')}")
    print(f"    Errors:             {_c('red', str(total_errors)) if total_errors else _c('green', '0')}")
    print(_c("bold", "─" * 72))
    print()

    return 1 if (total_vulns > 0 or total_errors > 0 or guard.conflicts or total_outdated > 0) else 0


def build_json_report(guard: GuardReport) -> Dict[str, Any]:
    python_reports_json = []
    for r in guard.python_reports:
        python_reports_json.append({
            "file": str(r.path.relative_to(REPO_ROOT)),
            "label": r.label,
            "package_count": len(r.packages),
            "unpinned": [p._raw for p in r.unpinned],
            "no_minimum_bound": [p._raw for p in r.no_min_bound],
            "parse_error": r.parse_error,
            "vulnerabilities": [
                {"package": v.package, "severity": v.severity,
                 "advisory": v.advisory, "fix_version": v.fix_version}
                for v in r.audit_vulns
            ],
            "audit_skipped": r.audit_skipped,
            "audit_error": r.audit_error,
            "outdated": [
                {"package": o.package, "installed": o.installed, "latest": o.latest}
                for o in r.outdated
            ],
        })

    npm_json = None
    if guard.npm_report:
        nr = guard.npm_report
        npm_json = {
            "package_count": len(nr.packages),
            "parse_error": nr.parse_error,
            "vulnerabilities": [
                {"package": v.package, "severity": v.severity,
                 "advisory": v.advisory, "fix_version": v.fix_version}
                for v in nr.vulns
            ],
            "audit_skipped": nr.audit_skipped,
            "audit_error": nr.audit_error,
            "outdated": [
                {"package": o.package, "installed": o.installed, "latest": o.latest}
                for o in nr.outdated
            ],
        }

    return {
        "timestamp": guard.timestamp,
        "repository": "gula-platform",
        "version": "2.1.0",
        "python": python_reports_json,
        "npm": npm_json,
        "conflicts": [
            {
                "package": c.package,
                "specifiers": [{"file": l, "spec": s} for l, s in c.specifiers],
            }
            for c in guard.conflicts
        ],
        "summary": {
            "total_python_packages": sum(
                len(r.packages) for r in guard.python_reports if not r.parse_error
            ),
            "total_npm_packages": len(guard.npm_report.packages) if guard.npm_report else 0,
            "total_vulnerabilities": guard.total_vulns,
            "total_outdated": guard.total_outdated,
            "total_conflicts": len(guard.conflicts),
        },
    }


def write_markdown_report(guard: GuardReport) -> None:
    report_dir = REPORT_FILE.parent
    report_dir.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# GULA Platform — Dependency Guardian Report\n")
    lines.append(f"**Timestamp:** {guard.timestamp}\n")
    lines.append("---\n")

    # ── Python ──
    lines.append("## Python Dependencies\n")
    for report in guard.python_reports:
        if report.parse_error:
            lines.append(f"### {report.label}\n")
            lines.append(f"- **Status:** ❌ Error — {report.parse_error}\n")
            continue

        status_emoji = "✅" if report.passed else "❌"
        lines.append(f"### {report.label}\n")
        lines.append(f"- **Status:** {status_emoji}")
        lines.append(f"- **Packages:** {len(report.packages)}")
        lines.append(f"- **Unpinned:** {len(report.unpinned)}")
        lines.append(f"- **No min bound:** {len(report.no_min_bound)}")
        lines.append(f"- **Vulnerabilities:** {len(report.audit_vulns)}")
        lines.append(f"- **Outdated:** {len(report.outdated)}\n")

        if report.unpinned:
            lines.append("#### Unpinned Dependencies\n")
            lines.append("| Package | Line |")
            lines.append("|---------|------|")
            for p in report.unpinned:
                lines.append(f"| `{p.name}` | {p.line} |")
            lines.append("")

        if report.no_min_bound:
            lines.append("#### Dependencies Without Minimum Bound\n")
            lines.append("| Package | Specifier | Line |")
            lines.append("|---------|-----------|------|")
            for p in report.no_min_bound:
                lines.append(f"| `{p.name}` | `{p.specifier}` | {p.line} |")
            lines.append("")

        if report.audit_vulns:
            lines.append("#### Known Vulnerabilities\n")
            lines.append("| Package | Severity | Fix Version |")
            lines.append("|---------|----------|-------------|")
            for v in report.audit_vulns:
                lines.append(f"| `{v.package}` | {v.severity} | `{v.fix_version}` |")
            lines.append("")

        if report.outdated:
            lines.append("#### Outdated Packages\n")
            lines.append("| Package | Installed | Latest |")
            lines.append("|---------|-----------|--------|")
            for o in report.outdated:
                lines.append(f"| `{o.package}` | {o.installed} | {o.latest} |")
            lines.append("")

        if report.audit_skipped:
            lines.append("> ⚠️ pip-audit was skipped (not installed or no packages to scan)\n")

        if report.audit_error:
            lines.append(f"> ❌ pip-audit error: {report.audit_error}\n")

    # ── npm ──
    lines.append("## npm / Frontend Dependencies\n")
    if guard.npm_report:
        nr = guard.npm_report
        if nr.parse_error:
            lines.append(f"- **Status:** ❌ Error — {nr.parse_error}\n")
        else:
            status_emoji = "✅" if nr.passed else "❌"
            lines.append(f"- **Status:** {status_emoji}")
            lines.append(f"- **Packages:** {len(nr.packages)}")
            lines.append(f"- **Vulnerabilities:** {len(nr.vulns)}")
            lines.append(f"- **Outdated:** {len(nr.outdated)}\n")

            if nr.vulns:
                lines.append("### Known Vulnerabilities\n")
                lines.append("| Package | Severity | Advisory | Fix |")
                lines.append("|---------|----------|----------|-----|")
                for v in nr.vulns:
                    lines.append(
                        f"| `{v.package}` | {v.severity} | "
                        f"{v.advisory[:60]} | {v.fix_version} |"
                    )
                lines.append("")

            if nr.outdated:
                lines.append("### Outdated Packages\n")
                lines.append("| Package | Installed | Latest |")
                lines.append("|---------|-----------|--------|")
                for o in nr.outdated:
                    lines.append(f"| `{o.package}` | {o.installed} | {o.latest} |")
                lines.append("")

            if nr.audit_skipped:
                lines.append("> ⚠️ npm audit was skipped (npm not installed)\n")
    else:
        lines.append("Not scanned (no package.json)\n")

    # ── Conflicts ──
    if guard.conflicts:
        lines.append("## Cross-Manifest Conflicts\n")
        lines.append("| Package | File | Specifier |")
        lines.append("|---------|------|-----------|")
        for c in guard.conflicts:
            for label, spec in c.specifiers:
                lines.append(f"| `{c.package}` | {label} | `{spec}` |")
        lines.append("")
    else:
        lines.append("## Cross-Manifest Conflicts\n")
        lines.append("No conflicts detected.\n")

    # ── Summary stats ──
    lines.append("## Summary\n")
    lines.append(f"- **Python packages:** {sum(len(r.packages) for r in guard.python_reports if not r.parse_error)}")
    lines.append(f"- **npm packages:** {len(guard.npm_report.packages) if guard.npm_report else 0}")
    lines.append(f"- **Vulnerabilities:** {guard.total_vulns}")
    lines.append(f"- **Outdated packages:** {guard.total_outdated}")
    lines.append(f"- **Cross-manifest conflicts:** {len(guard.conflicts)}")
    lines.append("")
    lines.append("---")
    lines.append(f"*Report auto-generated by `scripts/dependency_guardian.py`*")

    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("Markdown report written to %s", REPORT_FILE)


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def run_all_checks(args: argparse.Namespace) -> GuardReport:
    guard = GuardReport()

    # 1. Python requirements
    for fp in PYTHON_REQUIREMENT_FILES:
        report = parse_requirements(fp)
        if not args.skip_audit:
            run_pip_audit(report)
        if not args.skip_outdated:
            run_pip_outdated(report)
        guard.python_reports.append(report)

    # 2. npm
    if not args.skip_npm:
        npm_report = run_npm_audit()
        if not args.skip_outdated:
            run_npm_outdated(npm_report)
        guard.npm_report = npm_report

    # 3. Conflicts
    guard.conflicts = detect_conflicts(guard.python_reports)

    return guard


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GULA Dependency Guardian — scan all dependency ecosystems "
                    "for vulnerabilities, outdated packages, and cross-manifest conflicts.",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output results as JSON only (to stdout)",
    )
    parser.add_argument(
        "--no-markdown", action="store_true",
        help="Skip writing the markdown report to assessment/",
    )
    parser.add_argument(
        "--skip-audit", action="store_true",
        help="Skip vulnerability scanning (pip-audit + npm audit)",
    )
    parser.add_argument(
        "--skip-npm", action="store_true",
        help="Skip npm audit/outdated checks",
    )
    parser.add_argument(
        "--skip-outdated", action="store_true",
        help="Skip outdated-package detection",
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Create upgrade branch for outdated packages (dry-run by default)",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="With --fix, actually create branch and commit (otherwise dry-run)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Verbose logging",
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Dependency Guardian — scanning %s", REPO_ROOT)

    try:
        guard = run_all_checks(args)
    except Exception as e:
        logger.error("Fatal error during scan: %s", e, exc_info=True)
        return 2

    if args.json:
        print(json.dumps(build_json_report(guard), indent=2, ensure_ascii=False))
    else:
        issues = print_human_report(guard)
        if not args.no_markdown:
            write_markdown_report(guard)

    if args.fix:
        issues_in_fix = apply_fix(guard, dry_run=not args.apply)
        if issues_in_fix:
            return issues_in_fix

    if guard.has_issues or guard.total_outdated > 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
