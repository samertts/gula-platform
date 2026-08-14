#!/usr/bin/env python3
"""
GULA Quality Gate
=================
Runs all validation tools and enforces minimum thresholds.
Exit code: 0 = PASS, 1 = WARNING, 2 = FAIL
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

_RESET = "\033[0m"
_RED = "\033[91m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_CYAN = "\033[96m"
_BOLD = "\033[1m"
_MAGENTA = "\033[95m"

_USE_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    palette = {
        "red": _RED, "green": _GREEN, "yellow": _YELLOW,
        "cyan": _CYAN, "bold": _BOLD, "magenta": _MAGENTA, "reset": _RESET,
    }
    return f"{palette.get(code, _RESET)}{text}{_RESET}"


PASS = "PASS"
WARNING = "WARNING"
FAIL = "FAIL"


def _run_script(
    script_name: str,
    args: list[str] | None = None,
    timeout: int = 120,
) -> subprocess.CompletedProcess:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        return subprocess.CompletedProcess(
            [str(script_path)], -1, "", f"script not found: {script_name}",
        )
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=REPO_ROOT)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, -1, "", "timed out")
    except FileNotFoundError:
        return subprocess.CompletedProcess(cmd, -1, "", "python not found")


def _check_git_staged_secrets() -> tuple[str, list[str]]:
    """Check for basic secret patterns in git staged files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True, timeout=15, cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        return PASS, ["not a git repository or no staged files"]

    staged = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    if not staged:
        return PASS, ["no staged files to check"]

    secret_patterns = [
        (r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----", "private key"),
        (r"AKIA[0-9A-Z]{16}", "AWS access key"),
        (r"(password|passwd|pwd)\s*[:=]\s*['\"]?(?!(changeme|your|placeholder|\$))[^'\"\s]{8,}", "possible password"),
        (r"ghp_[0-9a-zA-Z]{36}", "GitHub token"),
        (r"sk-[0-9a-zA-Z]{32,}", "OpenAI API key"),
        (r"xox[baprs]-[0-9a-zA-Z]{10,}", "Slack token"),
    ]

    findings: list[str] = []
    for sf in staged:
        try:
            content = (REPO_ROOT / sf).read_text(errors="replace")
            for pattern, desc in secret_patterns:
                if re.search(pattern, content):
                    findings.append(f"{sf}: found {desc}")
        except (OSError, IOError):
            pass

    if findings:
        return FAIL, findings
    return PASS, ["no secrets detected in staged files"]


def _check_python_syntax(changed_only: bool = False, staged_only: bool = False) -> tuple[str, list[str]]:
    """Check Python syntax on changed or all .py files."""
    if changed_only:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, timeout=15, cwd=REPO_ROOT,
        )
        files = [
            l.strip() for l in result.stdout.splitlines()
            if l.strip().endswith(".py") and (REPO_ROOT / l.strip()).exists()
        ]
    elif staged_only:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, timeout=15, cwd=REPO_ROOT,
        )
        files = [
            l.strip() for l in result.stdout.splitlines()
            if l.strip().endswith(".py") and (REPO_ROOT / l.strip()).exists()
        ]
    else:
        files = list(REPO_ROOT.rglob("*.py"))
        files = [str(f.relative_to(REPO_ROOT)) for f in files if "__pycache__" not in str(f)]

    if not files:
        return PASS, ["no Python files to check"]

    errors: list[str] = []
    for f in files:
        fpath = REPO_ROOT / f
        try:
            compile(fpath.read_text(errors="replace"), str(fpath), "exec")
        except SyntaxError as e:
            errors.append(f"{f}: {e}")

    if errors:
        return FAIL, errors
    return PASS, [f"syntax OK for {len(files)} file(s)"]


def _check_migrations_immutable(staged_only: bool = False) -> tuple[str, list[str]]:
    """Check that migration files are not modified (immutable rule)."""
    if staged_only:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, timeout=15, cwd=REPO_ROOT,
        )
    else:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True, text=True, timeout=15, cwd=REPO_ROOT,
        )

    if result.returncode != 0:
        return PASS, ["not a git repository, skipping migration check"]

    changed = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    immutable_base = "20250322_0000_create_base_schema.py"
    migration_changes = [
        f for f in changed
        if "migrations/versions/" in f and (immutable_base in f or f.endswith(".py"))
    ]

    base_changes = [f for f in migration_changes if immutable_base in f]
    if base_changes:
        return FAIL, [f"immutable migration modified: {', '.join(base_changes)}"]

    if migration_changes:
        return PASS, [f"new/modified migration(s) detected (expected for new revisions): {', '.join(migration_changes)}"]

    return PASS, ["no migration files changed"]


def _load_json_cache(path: pathlib.Path) -> dict | None:
    if path.exists() and path.stat().st_size > 0:
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return None


def _check_compliance(thresh_warn: int = 60, thresh_fail: int = 30, bypass: bool = False) -> tuple[str, list[str]]:
    if bypass:
        return PASS, ["skipped (bypass)"]

    script_name = "architecture_compliance_engine.py"
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        return WARNING, [f"{script_name} not found"]

    cached = _load_json_cache(REPO_ROOT / "docs/metrics/compliance_cache.json")
    if cached is not None:
        data = cached
    else:
        proc = _run_script(script_name, ["--json", "--exclude-dirs", "tests,migrations,__pycache__"], timeout=120)
        if proc.returncode == -1:
            return WARNING, [f"{script_name}: {proc.stderr}"]

        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return WARNING, [f"{script_name}: could not parse output"]

    score = data.get("score", 0)
    if not isinstance(score, (int, float)):
        score = 0
    score = int(score)

    details: list[str] = [f"architecture compliance score: {score}/100"]
    if score >= thresh_warn:
        return PASS, details
    if score >= thresh_fail:
        return WARNING, details
    return FAIL, details


def _check_scorecard(thresh: int = 65, bypass: bool = False) -> tuple[str, list[str]]:
    if bypass:
        return PASS, ["skipped (bypass)"]

    script_name = "repository_scorecard.py"
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        return WARNING, [f"{script_name} not found"]

    cached = _load_json_cache(REPO_ROOT / "docs/metrics/scorecard_cache.json")
    if cached is not None:
        data = cached
    else:
        proc = _run_script(script_name, ["--json"], timeout=120)
        if proc.returncode == -1:
            return WARNING, [f"{script_name}: {proc.stderr}"]

        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return WARNING, [f"{script_name}: could not parse output"]

    score = data.get("overall_score", 0)
    if not isinstance(score, (int, float)):
        score = 0
    score = int(score)

    grade = data.get("grade", "?")
    details: list[str] = [f"repository scorecard: {score}/100 (grade {grade})"]
    if score >= 75:
        return PASS, details
    if score >= thresh:
        return WARNING, details
    return FAIL, details


def _check_technical_debt(bypass: bool = False) -> tuple[str, list[str]]:
    if bypass:
        return PASS, ["skipped (bypass)"]

    registry_json = REPO_ROOT / "docs" / "technical-debt" / "registry.json"
    if registry_json.exists() and registry_json.stat().st_size > 0:
        try:
            data = json.loads(registry_json.read_text())
        except (json.JSONDecodeError, OSError):
            data = None
    else:
        data = None

    if data is None:
        script_name = "technical_debt_registry.py"
        script_path = SCRIPTS_DIR / script_name
        if not script_path.exists():
            return WARNING, [f"{script_name} not found"]
        proc = _run_script(script_name, ["--json", "--refresh"], timeout=120)
        if proc.returncode == -1:
            return WARNING, [f"{script_name}: {proc.stderr}"]
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return WARNING, [f"{script_name}: could not parse output"]

    meta = data.get("meta", {})
    by_priority = meta.get("by_priority", {})
    p0 = by_priority.get("P0", 0)
    p1 = by_priority.get("P1", 0)
    total = meta.get("total_items", 0)

    details: list[str] = [f"technical debt: {total} items (P0={p0}, P1={p1})"]

    if p0 > 0:
        return FAIL, [f"{detail}" for detail in details] + ["P0 items found — blocking"]

    if p1 > 5:
        return WARNING, [f"{detail}" for detail in details] + [f"P1 count ({p1}) exceeds warning threshold (5)"]

    return PASS, details


def _check_enterprise_metrics(quality_thresh: int = 500, bypass: bool = False) -> tuple[str, list[str]]:
    if bypass:
        return PASS, ["skipped (bypass)"]

    cached = _load_json_cache(REPO_ROOT / "docs/metrics/enterprise_metrics_cache.json")
    if cached is not None:
        data = cached
    else:
        script_name = "enterprise_metrics.py"
        script_path = SCRIPTS_DIR / script_name
        if not script_path.exists():
            return WARNING, [f"{script_name} not found"]
        proc = _run_script(script_name, ["--json"], timeout=120)
        if proc.returncode == -1:
            return WARNING, [f"{script_name}: {proc.stderr}"]
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return WARNING, [f"{script_name}: could not parse output"]

    qi = data.get("quality_index", {})
    total = qi.get("total", 0)
    mx = qi.get("max", 1000)
    grade = qi.get("grade", "?")

    details: list[str] = [f"quality index: {total}/{mx} (grade {grade})"]
    if total >= quality_thresh:
        return PASS, details
    return FAIL, details


CheckResult = tuple[str, list[str]]


def _safe_result_summary(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expose only fixed check metadata; never write check details to CI logs."""
    return [
        {
            "name": str(result.get("name", "unknown")),
            "status": str(result.get("status", WARNING)),
            "detail_count": int(result.get("detail_count", 0)),
        }
        for result in results
    ]


def run_checks(
    checks: list[tuple[str, Any, Any]],
    strict: bool = False,
    ci: bool = False,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for name, func, bypass_flag in checks:
        status, details = func(bypass=bypass_flag)
        if strict and status == WARNING:
            status = FAIL
        results.append({
            "name": name,
            "status": status,
            "detail_count": len(details),
        })
    return results


CHECK_ARCHITECTURE = "architecture"
CHECK_SCORECARD = "scorecard"
CHECK_DEBT = "debt"
CHECK_METRICS = "metrics"
CHECK_SECRETS = "secrets"
CHECK_SYNTAX = "syntax"
CHECK_MIGRATIONS = "migrations"
ALL_CHECKS = {
    CHECK_ARCHITECTURE, CHECK_SCORECARD, CHECK_DEBT, CHECK_METRICS,
    CHECK_SECRETS, CHECK_SYNTAX, CHECK_MIGRATIONS,
}


def format_results(
    results: list[dict[str, Any]],
    ci: bool = False,
) -> str:
    if ci:
        overall = PASS
        for r in results:
            if r["status"] == FAIL:
                overall = FAIL
                break
            if r["status"] == WARNING:
                overall = WARNING

        return json.dumps({
            "overall": overall,
            "checks": _safe_result_summary(results),
        }, indent=2)

    lines: list[str] = []
    lines.append("")
    lines.append(f"  {_c('bold', '╔════════════════════════════════════════════════════╗')}")
    lines.append(f"  {_c('bold', '║          GULA Quality Gate                          ║')}")
    lines.append(f"  {_c('bold', '╚════════════════════════════════════════════════════╝')}")
    lines.append("")

    max_name_len = max(len(r["name"]) for r in results) if results else 10

    for r in results:
        status = r["status"]
        if status == PASS:
            badge = _c("green", "  PASS  ")
        elif status == WARNING:
            badge = _c("yellow", " WARNING ")
        else:
            badge = _c("red", "  FAIL  ")

        lines.append(f"  {badge}  {r['name']:{max_name_len}}")
        lines.append(f"         details recorded: {r.get('detail_count', 0)}")
        lines.append("")

    lines.append(f"  {_c('bold', '─' * 56)}")
    overall = PASS
    for r in results:
        if r["status"] == FAIL:
            overall = FAIL
            break
        if r["status"] == WARNING:
            overall = WARNING

    if overall == PASS:
        lines.append(f"  {_c('green', '✔ OVERALL: PASS')} — all checks passed")
    elif overall == WARNING:
        lines.append(f"  {_c('yellow', '⚠ OVERALL: WARNING')} — some checks need attention")
    else:
        lines.append(f"  {_c('red', '✖ OVERALL: FAIL')} — one or more checks failed")
    lines.append("")

    return "\n".join(lines)


def determine_exit_code(results: list[dict[str, Any]], strict: bool) -> int:
    for r in results:
        if r["status"] == FAIL:
            return 2
    if strict:
        for r in results:
            if r["status"] == WARNING:
                return 2
    for r in results:
        if r["status"] == WARNING:
            return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="GULA Quality Gate — unified validation and CI gating",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Treat warnings as failures",
    )
    parser.add_argument(
        "--ci", action="store_true",
        help="CI-friendly output (JSON + exit code only)",
    )
    parser.add_argument(
        "--stage", action="store_true",
        help="Check only git-staged files (for pre-commit)",
    )
    parser.add_argument(
        "--bypass", type=str, default="",
        help="Comma-separated checks to skip",
    )
    args = parser.parse_args(argv)

    if args.ci:
        global _USE_COLOR
        _USE_COLOR = False

    bypass_set = set(s.strip() for s in args.bypass.split(",") if s.strip())
    invalid = bypass_set - ALL_CHECKS
    if invalid:
        print("error: unknown quality-gate checks requested", file=sys.stderr)
        print("Use only checks defined by the CI configuration.", file=sys.stderr)
        return 2

    def b(name: str) -> bool:
        return name in bypass_set

    checks: list[tuple[str, Any, Any]] = [
        (CHECK_ARCHITECTURE, _check_compliance, b(CHECK_ARCHITECTURE)),
        (CHECK_SCORECARD, _check_scorecard, b(CHECK_SCORECARD)),
        (CHECK_DEBT, _check_technical_debt, b(CHECK_DEBT)),
        (CHECK_METRICS, _check_enterprise_metrics, b(CHECK_METRICS)),
        (CHECK_SECRETS, lambda bypass=False: (PASS, ["skipped (bypass)"]) if bypass else _check_git_staged_secrets(), b(CHECK_SECRETS)),
        (CHECK_SYNTAX, lambda bypass=False: (PASS, ["skipped (bypass)"]) if bypass else _check_python_syntax(
            changed_only=not args.stage,
            staged_only=args.stage,
        ), b(CHECK_SYNTAX)),
        (CHECK_MIGRATIONS, lambda bypass=False: (PASS, ["skipped (bypass)"]) if bypass else _check_migrations_immutable(
            staged_only=args.stage,
        ), b(CHECK_MIGRATIONS)),
    ]

    results = run_checks(checks, strict=args.strict, ci=args.ci)
    output = format_results(results, ci=args.ci)
    sys.stdout.write(output)
    sys.stdout.write("\n")

    return determine_exit_code(results, args.strict)


if __name__ == "__main__":
    sys.exit(main())
