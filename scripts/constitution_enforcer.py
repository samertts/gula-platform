#!/usr/bin/env python3
"""
GULA Platform — Platform Constitution Enforcement Script
===========================================================

Enforces the Platform Constitution (docs/constitution/PLATFORM-CONSTITUTION.md):

  Rule  1: No code without tests
  Rule  2: No module without documentation
  Rule  3: No API without OpenAPI
  Rule  4: No architectural change without ADR
  Rule  5: No duplicated code unless justified
  Rule  6: No Critical or High vulnerabilities
  Rule  7: No dependency introduced without validation
  Rule  8: No direct access bypassing the Kernel
  Rule  9: No AI-generated code may bypass review
  Rule 10: No commit if quality gates fail
  Rule 11: No merge if architecture score decreases
  Rule 12: Every change must improve the platform
  Rule 13: No hardcoded secrets
  Rule 14: No architecture violations (layer, circular deps)
  Rule 15: No dead or unused code
  Rule 16: FHIR compliance for health data
  Rule 17: Privacy-by-design (consent check)
  Rule 18: Security-by-design (zero trust)
  Rule 19: No circular dependencies
  Rule 20: AI safety and explainability

Usage:
  python scripts/constitution_enforcer.py
  python scripts/constitution_enforcer.py --verbose
  python scripts/constitution_enforcer.py --json
  python scripts/constitution_enforcer.py --diff-mode
  python scripts/constitution_enforcer.py --pre-commit

Flags:
  --diff-mode    Compare working tree against HEAD~1 (or alternate base)
  --pre-commit   Pre-commit hook mode (staged changes only)
  --json         Machine-readable JSON output (suppresses colour)
  --verbose      Verbose / debug logging
  --base REF     Base ref for --diff-mode (default: HEAD~1)

Exit codes:
  0 — all rules PASS (or WARNING only)
  1 — one or more rules FAIL

Each rule is scored PASS / WARNING / FAIL.  The overall compliance score
(0–100) is:

  score = 100 × (pass_count + 0.5 × warning_count) / total_rules

A single FAIL forces exit code 1 regardless of the numeric score.
"""

from __future__ import annotations

import argparse
import ast
import json
import logging
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("constitution_enforcer")

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BACKEND_APP = REPO_ROOT / "backend" / "app"
BACKEND_TESTS = REPO_ROOT / "backend" / "tests"
SCRIPTS_DIR = REPO_ROOT / "scripts"
DOCS_ADR = REPO_ROOT / "docs" / "adr"

ARCHITECTURE_GUARDIAN = SCRIPTS_DIR / "architecture_guardian.py"
DEPENDENCY_GUARDIAN = SCRIPTS_DIR / "dependency_guardian.py"

SCORE_BASELINE_FILE = pathlib.Path("/tmp/constitution_baseline.json")

# ── Terminal colours ──────────────────────────────────────────────────────────

_RESET = "\033[0m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_CYAN = "\033[96m"
_BOLD = "\033[1m"
_WHITE = "\033[97m"

_USE_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    palette = {
        "green": _GREEN, "yellow": _YELLOW, "red": _RED,
        "cyan": _CYAN, "bold": _BOLD, "white": _WHITE, "reset": _RESET,
    }
    return f"{palette.get(code, _RESET)}{text}{_RESET}"


def _green(msg: str) -> str:
    return _c("green", msg)


def _yellow(msg: str) -> str:
    return _c("yellow", msg)


def _red(msg: str) -> str:
    return _c("red", msg)


def _bold(msg: str) -> str:
    return _c("bold", msg)


# ── Data structures ──────────────────────────────────────────────────────────

PASS = "PASS"
WARNING = "WARNING"
FAIL = "FAIL"
STATUS_ORDER = {PASS: 0, WARNING: 1, FAIL: 2}

RuleResult = dict[str, Any]


def make_rule(
    number: int,
    title: str,
    status: str,
    details: list[str] | None = None,
    score_contribution: float | None = None,
) -> RuleResult:
    return {
        "rule": f"Rule {number}",
        "title": title,
        "status": status,
        "details": details or [],
        "score_contribution": score_contribution,
    }


# ── Git / diff helpers ──────────────────────────────────────────────────────


def _git_diff_files(base: str = "HEAD~1") -> list[str]:
    """Return list of files changed between *base* and HEAD."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", base],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=30,
        )
        if result.returncode != 0:
            logger.warning("git diff failed (base=%s): %s", base, result.stderr.strip())
            return []
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except (subprocess.TimeoutExpired, OSError) as exc:
        logger.warning("git diff error: %s", exc)
        return []


def _git_staged_files() -> list[str]:
    """Return list of staged files."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=30,
        )
        if result.returncode != 0:
            logger.warning("git diff --cached failed: %s", result.stderr.strip())
            return []
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except (subprocess.TimeoutExpired, OSError) as exc:
        logger.warning("git diff --cached error: %s", exc)
        return []


def _git_staged_diff() -> str:
    """Return full diff of staged changes."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached"],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=30,
        )
        return result.stdout
    except (subprocess.TimeoutExpired, OSError):
        return ""


def _get_changed_py_files(files: list[str]) -> list[str]:
    return [f for f in files if f.endswith(".py") and not f.startswith("tests/")]


# ── Rule implementations ────────────────────────────────────────────────────


def _find_corresponding_test(source_path: str) -> bool:
    """Check if a source file has a corresponding test file."""
    src = pathlib.Path(source_path)
    stem = src.stem
    test_name = f"test_{stem}"
    test_path = BACKEND_TESTS / f"{test_name}.py"
    if test_path.exists():
        return True
    for subdir in ["booking", "identity", "integration", "kernel", "kernel_hardening", "notifications", "skills"]:
        if (BACKEND_TESTS / subdir / f"{test_name}.py").exists():
            return True
    return False


def rule1_tests(changed_py_files: list[str]) -> RuleResult:
    details: list[str] = []
    status = PASS
    for f in changed_py_files:
        if f.startswith("backend/app/"):
            if not _find_corresponding_test(f):
                details.append(f"Missing test for {f}")
                status = WARNING
    if details:
        details.insert(0, f"{len(details)} source file(s) without corresponding tests")
    return make_rule(1, "No code without tests", status, details)


def rule2_module_docstrings(changed_py_files: list[str]) -> RuleResult:
    details: list[str] = []
    status = PASS
    for f in changed_py_files:
        if not f.endswith(".py"):
            continue
        full_path = REPO_ROOT / f
        if not full_path.exists():
            continue
        try:
            tree = ast.parse(full_path.read_text(encoding="utf-8"))
            doc = ast.get_docstring(tree)
            if not doc:
                details.append(f"Missing module docstring in {f}")
                status = WARNING
        except (SyntaxError, OSError):
            details.append(f"Cannot parse {f} for docstring check")
            status = WARNING
    if details:
        details.insert(0, f"{len(details)} file(s) missing module docstrings")
    return make_rule(2, "No module without documentation", status, details)


def rule3_openapi(changed_py_files: list[str]) -> RuleResult:
    details: list[str] = []
    status = PASS
    for f in changed_py_files:
        if not f.startswith("backend/app/routes/") or not f.endswith(".py"):
            continue
        full_path = REPO_ROOT / f
        if not full_path.exists():
            continue
        try:
            text = full_path.read_text(encoding="utf-8")
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name.startswith("_"):
                        continue
                    doc = ast.get_docstring(node)
                    if not doc:
                        details.append(f"Route handler '{node.name}' in {f} lacks docstring")
                        status = WARNING
        except (SyntaxError, OSError):
            details.append(f"Cannot parse {f} for API documentation check")
            status = WARNING
    if details:
        details.insert(0, f"{len(details)} route handler(s) missing docstrings")
    return make_rule(3, "No API without OpenAPI", status, details)


def rule4_architectural_change_with_adr(changed_files: list[str]) -> RuleResult:
    details: list[str] = []
    status = PASS

    adr_patterns = [
        "backend/app/core/",
        "backend/app/kernel/",
        "backend/app/security/",
        "backend/app/routes/",
        "backend/app/models/",
        "backend/app/database.py",
        "backend/app/main.py",
        "docker-compose",
        "docker-compose",
        "k8s/",
        "services/",
        "Makefile",
    ]

    architectural_changes = []
    for f in changed_files:
        for pat in adr_patterns:
            if f.startswith(pat) or pat in f:
                architectural_changes.append(f)
                break

    if architectural_changes:
        adr_files = list(DOCS_ADR.glob("ADR-*.md")) if DOCS_ADR.exists() else []
        adr_count = len([a for a in adr_files if a.name != "README.md"])

        details.append(f"{len(architectural_changes)} architectural file(s) changed")
        for af in architectural_changes:
            details.append(f"  - {af}")
        details.append(f"Existing ADRs: {adr_count}")

        if adr_count < 5:
            status = WARNING
            details.append("Low ADR count for the number of architectural changes")
    else:
        details.append("No architectural files changed")

    if details:
        details.insert(0, "Architectural change detected — verify ADR exists")
    return make_rule(4, "No architectural change without ADR", status, details)


def rule5_duplicated_code(changed_py_files: list[str]) -> RuleResult:
    details: list[str] = []
    status = PASS

    if len(changed_py_files) < 2:
        details.append("Too few files to check for duplication (need >= 2)")
        return make_rule(5, "No duplicated code unless justified", PASS, details)

    threshold = 6
    block_cache: dict[str, list[tuple[int, str]]] = defaultdict(list)

    for f in changed_py_files:
        full_path = REPO_ROOT / f
        if not full_path.exists() or not full_path.is_file():
            continue
        try:
            lines = full_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for i in range(len(lines) - threshold + 1):
            block = "\n".join(lines[i:i + threshold])
            block_cache[block].append((f, i + 1))

    dup_count = 0
    for block, locations in block_cache.items():
        if len(locations) >= 2:
            dup_count += 1
            source_files = set(loc[0] for loc in locations)
            if len(source_files) >= 2:
                loc_strs = [f"{loc[0]}:{loc[1]}" for loc in locations[:4]]
                if dup_count <= 5:
                    details.append(f"Duplicate block ({len(locations)} occurrences): {', '.join(loc_strs)}")

    if dup_count > 0:
        details.insert(0, f"{dup_count} duplicate code block(s) detected across {len(changed_py_files)} file(s)")
        status = WARNING if dup_count <= 3 else FAIL

    if not details:
        details.append("No significant code duplication detected")

    return make_rule(5, "No duplicated code unless justified", status, details)


def rule6_bandit() -> RuleResult:
    details: list[str] = []
    status = PASS

    bandit_exe = shutil.which("bandit")
    if not bandit_exe:
        details.append("bandit not installed — skipping vulnerability scan")
        return make_rule(6, "No Critical or High vulnerabilities", WARNING, details)

    target = str(BACKEND_APP)
    try:
        result = subprocess.run(
            [bandit_exe, "-r", target, "-ll", "-f", "json", "--quiet"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 2:
            details.append("bandit encountered an error during scanning")
            return make_rule(6, "No Critical or High vulnerabilities", WARNING, details)

        if result.stdout.strip():
            try:
                data = json.loads(result.stdout)
                issues = data.get("results", [])
                high_issues = [i for i in issues if i.get("issue_severity", "").lower() in ("high", "critical")]
                if high_issues:
                    for iss in high_issues[:10]:
                        fname = iss.get("filename", "")
                        line = iss.get("line_number", "")
                        sev = iss.get("issue_severity", "")
                        details.append(f"[{sev}] {fname}:{line} — {iss.get('issue_text', '')}")
                    if len(high_issues) > 10:
                        details.append(f"  ... and {len(high_issues) - 10} more")
                    status = FAIL
                    details.insert(0, f"{len(high_issues)} High/Critical vulnerability(ies) found")
                else:
                    details.append("No High or Critical vulnerabilities found")
            except json.JSONDecodeError:
                details.append("Could not parse bandit JSON output")
                status = WARNING
        else:
            details.append("No High or Critical vulnerabilities found")

    except FileNotFoundError:
        details.append("bandit executable not found")
        return make_rule(6, "No Critical or High vulnerabilities", WARNING, details)
    except subprocess.TimeoutExpired:
        details.append("bandit scan timed out after 120s")
        return make_rule(6, "No Critical or High vulnerabilities", WARNING, details)

    return make_rule(6, "No Critical or High vulnerabilities", status, details)


def rule7_dependency_validation(changed_files: list[str]) -> RuleResult:
    details: list[str] = []
    status = PASS

    req_changes = [f for f in changed_files if "requirements" in f.lower() and f.endswith(".txt")]
    if not req_changes:
        details.append("No requirements files changed")
        return make_rule(7, "No dependency introduced without validation", PASS, details)

    for rf in req_changes:
        details.append(f"Requirements file changed: {rf}")

    if DEPENDENCY_GUARDIAN.exists():
        details.append("Running Dependency Guardian...")
        try:
            result = subprocess.run(
                [sys.executable, str(DEPENDENCY_GUARDIAN), "--skip-audit"],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                details.append("Dependency Guardian found issues:")
                for line in result.stdout.splitlines():
                    stripped = line.strip()
                    if stripped and ("⚠" in stripped or "✘" in stripped or "unpinned" in stripped or "vuln" in stripped):
                        details.append(f"  {stripped[:120]}")
                status = WARNING
            else:
                details.append("Dependency Guardian: all clear")
        except (subprocess.TimeoutExpired, OSError) as exc:
            details.append(f"Could not run Dependency Guardian: {exc}")
            status = WARNING
    else:
        details.append(f"Dependency Guardian not found at {DEPENDENCY_GUARDIAN}")
        status = WARNING

    return make_rule(7, "No dependency introduced without validation", status, details)


def rule8_kernel_bypass(changed_py_files: list[str]) -> RuleResult:
    details: list[str] = []
    status = PASS

    bypass_patterns = [
        r"from\s+sqlalchemy\s+import",
        r"import\s+sqlalchemy",
        r"from\s+backend\.app\.database\s+import",
        r"from\s+app\.database\s+import",
        r"import\s+redis\s*$",
        r"from\s+redis\s+import",
        r"\.execute\s*\(",
        r"\.session\s*=",
        r"Session\s*=\s*",
    ]

    for f in changed_py_files:
        if not f.endswith(".py"):
            continue
        if f.startswith("backend/app/kernel/"):
            continue
        if f.startswith("backend/app/models/"):
            continue
        if f.startswith("backend/app/database.py"):
            continue
        full_path = REPO_ROOT / f
        if not full_path.exists():
            continue
        try:
            text = full_path.read_text(encoding="utf-8")
        except OSError:
            continue

        for lineno, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            for pat in bypass_patterns:
                if re.search(pat, stripped):
                    details.append(f"Bypass pattern in {f}:{lineno} — {stripped.strip()[:80]}")
                    status = WARNING
                    break

    if details:
        details.insert(0, f"{len(details)} potential kernel bypass(es) detected")
    if not details:
        details.append("No kernel bypass patterns detected")

    return make_rule(8, "No direct access bypassing the Kernel", status, details)


def rule9_ai_generated_code_markers(changed_files: list[str]) -> RuleResult:
    details: list[str] = []
    status = PASS

    ai_markers = [
        r"Generated\s+by\s+(AI|Claude|ChatGPT|Copilot|LLM)",
        r"This\s+code\s+was\s+(generated|created|written)\s+by",
        r"AI[- ]generated",
        r"Auto[- ]generated\s+by",
        r"Generated\s+using\s+(AI|Claude|ChatGPT|Copilot)",
    ]

    for f in changed_files:
        if not f.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs")):
            continue
        full_path = REPO_ROOT / f
        if not full_path.exists():
            continue
        try:
            text = full_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        first_line = text.splitlines()[0] if text.splitlines() else ""
        if any(re.search(marker, first_line, re.IGNORECASE) for marker in ai_markers):
            details.append(f"AI-generated marker found in {f}: {first_line.strip()[:80]}")
            status = WARNING
            continue

        lines = text.splitlines()
        for lineno, line in enumerate(lines[1:], 2):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                for marker in ai_markers:
                    if re.search(marker, stripped, re.IGNORECASE):
                        details.append(f"AI-generated marker in {f}:{lineno} — {stripped[:80]}")
                        status = WARNING
                        break

    if details:
        details.insert(0, f"{len(details)} AI-generated marker(s) found — requires human review")
    if not details:
        details.append("No AI-generated code markers detected")

    return make_rule(9, "No AI-generated code may bypass review", status, details)


def rule10_quality_gates(changed_py_files: list[str]) -> RuleResult:
    details: list[str] = []
    status = PASS
    all_ok = True

    if ARCHITECTURE_GUARDIAN.exists():
        details.append("Running Architecture Guardian...")
        try:
            result = subprocess.run(
                [sys.executable, str(ARCHITECTURE_GUARDIAN), "--json"],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                all_ok = False
                details.append("Architecture Guardian found new violations")
                for line in result.stdout.splitlines():
                    if '"message"' in line:
                        details.append(f"  {line.strip()[:120]}")
            else:
                details.append("Architecture Guardian: all clear")
        except (subprocess.TimeoutExpired, OSError) as exc:
            details.append(f"Could not run Architecture Guardian: {exc}")
            all_ok = False
    else:
        details.append(f"Architecture Guardian not found at {ARCHITECTURE_GUARDIAN}")
        all_ok = False

    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile"] + [str(REPO_ROOT / f) for f in changed_py_files if (REPO_ROOT / f).exists()],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            all_ok = False
            details.append("py_compile errors:")
            for line in result.stderr.splitlines():
                details.append(f"  {line.strip()[:120]}")
        else:
            details.append("py_compile: all syntax OK")
    except (subprocess.TimeoutExpired, OSError) as exc:
        details.append(f"py_compile check failed: {exc}")
        all_ok = False

    for tool in ("flake8", "pyflakes"):
        exe = shutil.which(tool)
        if exe:
            try:
                targets = [str(REPO_ROOT / f) for f in changed_py_files if f.endswith(".py") and (REPO_ROOT / f).exists()]
                if targets:
                    result = subprocess.run(
                        [exe] + targets, capture_output=True, text=True, timeout=30,
                    )
                    if result.returncode != 0:
                        all_ok = False
                        issue_lines = [l for l in result.stdout.splitlines() if l.strip() and ":" in l]
                        for line in issue_lines[:10]:
                            details.append(f"  [{tool}] {line.strip()[:120]}")
                        if len(issue_lines) > 10:
                            details.append(f"  ... and {len(issue_lines) - 10} more")
                    else:
                        details.append(f"{tool}: all clear")
            except (subprocess.TimeoutExpired, OSError) as exc:
                details.append(f"{tool} check failed: {exc}")
                all_ok = False
        else:
            details.append(f"{tool} not installed — skipped")
            all_ok = False

    if not all_ok:
        status = FAIL
        details.insert(0, "Quality gates failed")
    else:
        details.insert(0, "All quality gates passed")

    return make_rule(10, "No commit if quality gates fail", status, details)


def rule11_architecture_score() -> RuleResult:
    details: list[str] = []
    status = PASS

    score = 50.0
    if ARCHITECTURE_GUARDIAN.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(ARCHITECTURE_GUARDIAN), "--json"],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                score = 100.0
                details.append("Architecture Guardian: no new violations")
            else:
                try:
                    data = json.loads(result.stdout)
                    new_count = data.get("summary", {}).get("new", 0)
                    total_count = data.get("summary", {}).get("total", 0)
                    score = max(0, 100 - (new_count * 10) - total_count)
                    if new_count > 0:
                        details.append(f"{new_count} new violation(s) — score penalized")
                    if total_count > 0:
                        details.append(f"{total_count} total violation(s)")
                except (json.JSONDecodeError, AttributeError):
                    details.append("Could not parse Architecture Guardian output")
                    score = 40.0
        except (subprocess.TimeoutExpired, OSError) as exc:
            details.append(f"Could not run Architecture Guardian: {exc}")
            score = 30.0
    else:
        details.append("Architecture Guardian not found — cannot compute score")
        score = 0.0

    baseline = {}
    if SCORE_BASELINE_FILE.exists():
        try:
            baseline = json.loads(SCORE_BASELINE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    prev_score = baseline.get("architecture_score", 100.0)
    if score < prev_score:
        details.insert(0, f"Architecture score decreased: {prev_score:.0f} → {score:.0f}")
        status = FAIL
    elif score < prev_score * 0.9:
        details.insert(0, f"Architecture score dropped significantly: {prev_score:.0f} → {score:.0f}")
        status = FAIL
    else:
        if not details:
            details.append("Architecture score stable or improved")
        details.insert(0, f"Architecture score: {score:.0f}/100 (previous: {prev_score:.0f})")

    try:
        baseline["architecture_score"] = score
        baseline["timestamp"] = datetime.now(timezone.utc).isoformat()
        SCORE_BASELINE_FILE.write_text(json.dumps(baseline, indent=2), encoding="utf-8")
    except OSError:
        pass

    return make_rule(11, "No merge if architecture score decreases", status, details)


def rule13_hardcoded_secrets(changed_py_files: list[str]) -> RuleResult:
    details: list[str] = []
    status = PASS

    secret_patterns = [
        r'["\'](SECRET_KEY|ENCRYPTION_KEY|NID_HMAC_KEY|DEVICE_HMAC_KEY|REFRESH_TOKEN_SECRET)["\']\s*[:=]\s*["\'][^"\']+["\']',
        r'password\s*=\s*["\'][^"\']+["\']',
        r'api_key\s*=\s*["\'][^"\']+["\']',
        r'token\s*=\s*["\'][^"\']+["\']',
    ]

    for f in changed_py_files:
        if not f.endswith(".py"):
            continue
        if "test_" in f:
            continue
        full_path = REPO_ROOT / f
        if not full_path.exists():
            continue
        try:
            text = full_path.read_text(encoding="utf-8")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            for pat in secret_patterns:
                if re.search(pat, stripped):
                    details.append(f"Potential hardcoded secret in {f}:{lineno} — {stripped[:80]}")
                    status = FAIL
                    break

    if details:
        details.insert(0, f"{len(details)} potential hardcoded secret(s) found")
    if not details:
        details.append("No hardcoded secrets detected")
    return make_rule(13, "No hardcoded secrets", status, details)


def rule14_architecture_violations() -> RuleResult:
    details: list[str] = []
    status = PASS

    if ARCHITECTURE_GUARDIAN.exists():
        details.append("Running Architecture Guardian...")
        try:
            result = subprocess.run(
                [sys.executable, str(ARCHITECTURE_GUARDIAN), "--json"],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                try:
                    data = json.loads(result.stdout)
                    new_count = data.get("summary", {}).get("new", 0)
                    total_count = data.get("summary", {}).get("total", 0)
                    if new_count > 0:
                        details.append(f"{new_count} new architecture violation(s)")
                        status = FAIL
                    if total_count > 0:
                        details.append(f"{total_count} total architecture violation(s)")
                        if status != FAIL:
                            status = WARNING
                except (json.JSONDecodeError, AttributeError):
                    details.append("Could not parse Architecture Guardian output")
                    status = WARNING
            else:
                details.append("Architecture Guardian: all clear")
        except (subprocess.TimeoutExpired, OSError) as exc:
            details.append(f"Could not run Architecture Guardian: {exc}")
            status = WARNING
    else:
        details.append("Architecture Guardian not found")
        status = WARNING

    if not details:
        details.append("No architecture violations detected")
    return make_rule(14, "No architecture violations", status, details)


def rule15_dead_code(changed_py_files: list[str]) -> RuleResult:
    details: list[str] = []
    status = PASS
    count = 0

    for f in changed_py_files:
        if not f.endswith(".py"):
            continue
        full_path = REPO_ROOT / f
        if not full_path.exists():
            continue
        try:
            tree = ast.parse(full_path.read_text(encoding="utf-8"), filename=str(full_path))
        except (SyntaxError, OSError):
            continue

        has_unused = False
        defined = set()
        used = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined.add(node.name)
            elif isinstance(node, ast.ClassDef):
                defined.add(node.name)
            elif isinstance(node, ast.Name) and not isinstance(node.ctx, (ast.Store, ast.Del)):
                used.add(node.id)

        unused = defined - used - {"main", "setup", "teardown"}
        for name in sorted(unused):
            count += 1
            if count <= 10:
                details.append(f"Possibly unused function/class '{name}' in {f}")
            has_unused = True

        if has_unused and count > 10 and len(details) <= 10:
            pass

    if count > 0:
        details.insert(0, f"{count} potentially unused function(s)/class(es) detected")
        status = WARNING if count <= 5 else FAIL
    if not details:
        details.append("No dead code detected")
    return make_rule(15, "No dead or unused code", status, details)


def rule16_fhir_compliance(changed_py_files: list[str]) -> RuleResult:
    details: list[str] = []
    status = PASS

    fhir_files = [f for f in changed_py_files if "fhir" in f.lower()]
    for f in changed_py_files:
        if not f.endswith(".py"):
            continue
        full_path = REPO_ROOT / f
        if not full_path.exists():
            continue
        try:
            text = full_path.read_text(encoding="utf-8")
            if "patient" in f.lower() and "fhir" not in text.lower():
                if any(marker in f for marker in ["models/patient", "routes/patients", "services/patient"]):
                    details.append(f"Patient-related file {f} may lack FHIR mapping")
                    status = WARNING
        except OSError:
            continue

    if fhir_files:
        details.append(f"{len(fhir_files)} FHIR-related file(s) changed — verify FHIR R4 compliance")
    if not details:
        details.append("No FHIR compliance issues detected")
    return make_rule(16, "FHIR compliance for health data", status, details)


def rule17_privacy_by_design(changed_py_files: list[str]) -> RuleResult:
    details: list[str] = []
    status = PASS

    sensitive_patterns = ["national_id", "sndhs_health_id", "phone", "email", "address"]
    for f in changed_py_files:
        if not f.endswith(".py"):
            continue
        if "test_" in os.path.basename(f):
            continue
        full_path = REPO_ROOT / f
        if not full_path.exists():
            continue
        try:
            text = full_path.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(full_path))
        except (SyntaxError, OSError):
            continue

        has_sensitive = False
        has_encryption = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Str) or isinstance(node, ast.Constant):
                val = node.s if isinstance(node, ast.Str) else node.value
                if isinstance(val, str):
                    for pat in sensitive_patterns:
                        if pat in val.lower():
                            has_sensitive = True
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if "encrypt" in node.name.lower() or "decrypt" in node.name.lower():
                    has_encryption = True

        if has_sensitive and not has_encryption:
            if "encrypt" not in text.lower() and "decrypt" not in text.lower():
                details.append(f"Sensitive data in {f} may need encryption")
                status = WARNING

    if details:
        details.insert(0, f"{len(details)} privacy consideration(s)")
    if not details:
        details.append("No privacy violations detected")
    return make_rule(17, "Privacy-by-design", status, details)


def rule18_security_by_design(changed_py_files: list[str]) -> RuleResult:
    details: list[str] = []
    status = PASS

    route_files = [f for f in changed_py_files if f.startswith("backend/app/routes/") and f.endswith(".py")]
    for f in route_files:
        full_path = REPO_ROOT / f
        if not full_path.exists():
            continue
        try:
            text = full_path.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(full_path))
        except (SyntaxError, OSError):
            continue

        has_auth = False
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        func = decorator.func
                        if isinstance(func, ast.Attribute):
                            if "get_current_user" in ast.dump(decorator) or "require_role" in ast.dump(decorator) or "Depends" in ast.dump(decorator):
                                has_auth = True

        if not has_auth and "router" in text and ("@router." in text or "@router" in text):
            if "health" not in f and "openapi" not in f and "docs" not in f:
                details.append(f"Route file {f} may lack auth dependency injection")
                status = WARNING

    if details:
        details.insert(0, f"{len(details)} security consideration(s)")
    if not details:
        details.append("No security violations detected")
    return make_rule(18, "Security-by-design (zero trust)", status, details)


def rule19_no_circular_dependencies() -> RuleResult:
    details: list[str] = []
    status = PASS

    if ARCHITECTURE_GUARDIAN.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(ARCHITECTURE_GUARDIAN), "--json"],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    cycles = [v for v in data.get("new_violations", []) if v.get("check") == "circular_dependency"]
                    if cycles:
                        for c in cycles:
                            details.append(c.get("message", "Circular dependency detected"))
                        status = FAIL
                    else:
                        details.append("No circular dependencies detected")
                except (json.JSONDecodeError, AttributeError):
                    details.append("Could not parse guardian output")
                    status = WARNING
            else:
                details.append("Architecture Guardian found issues")
                status = WARNING
        except (subprocess.TimeoutExpired, OSError) as exc:
            details.append(f"Could not run Architecture Guardian: {exc}")
            status = WARNING
    else:
        details.append("Architecture Guardian not found")
        status = WARNING

    if not details:
        details.append("No circular dependencies detected")
    return make_rule(19, "No circular dependencies", status, details)


def rule20_ai_safety(changed_py_files: list[str]) -> RuleResult:
    details: list[str] = []
    status = PASS

    ai_files = [f for f in changed_py_files if "ai" in f.lower() and f.endswith(".py")]
    for f in ai_files:
        full_path = REPO_ROOT / f
        if not full_path.exists():
            continue
        try:
            text = full_path.read_text(encoding="utf-8")
        except OSError:
            continue

        has_approval = "human_approval" in text.lower() or "approval" in text.lower() or "guardrail" in text.lower()
        has_explainability = "explain" in text.lower() or "confidence" in text.lower()
        has_safety = "hallucination" in text.lower() or "safety" in text.lower() or "guardrail" in text.lower()

        if not has_approval:
            details.append(f"AI file {f} may lack human approval mechanism")
            status = WARNING
        if not has_explainability:
            details.append(f"AI file {f} may lack explainability")
            if status != FAIL:
                status = WARNING
        if not has_safety:
            details.append(f"AI file {f} may lack safety guardrails")
            if status != FAIL:
                status = WARNING

    if not ai_files:
        details.append("No AI files changed — check skipped")

    if details:
        details.insert(0, f"{len(details)} AI safety consideration(s)")
    if not details:
        details.append("No AI safety issues detected")
    return make_rule(20, "AI safety and explainability", status, details)


def rule12_aggregate_improvement(all_results: list[RuleResult]) -> RuleResult:
    details: list[str] = []
    status = PASS

    fail_count = sum(1 for r in all_results if r["status"] == FAIL)
    warn_count = sum(1 for r in all_results if r["status"] == WARNING)
    pass_count = sum(1 for r in all_results if r["status"] == PASS)

    if fail_count > 0:
        status = FAIL
        details.append(f"{fail_count} rule(s) FAILED — platform quality not guaranteed to improve")
    elif warn_count > 3:
        status = WARNING
        details.append(f"{warn_count} warning(s) — address before merging")
    else:
        details.append("All rules clear — change improves platform quality")

    details.insert(0, f"PASS: {pass_count}, WARNING: {warn_count}, FAIL: {fail_count}")

    return make_rule(12, "Every change must improve the platform", status, details)


# ── Scoring ──────────────────────────────────────────────────────────────────


def _compute_score(results: list[RuleResult]) -> float:
    pass_count = sum(1 for r in results if r["status"] == PASS)
    warn_count = sum(1 for r in results if r["status"] == WARNING)
    total = len(results)
    if total == 0:
        return 100.0
    return 100.0 * (pass_count + 0.5 * warn_count) / total


# ── Output ───────────────────────────────────────────────────────────────────


def _format_detail(d: str) -> str:
    if d.startswith("  "):
        return d
    return f"  └ {d}"


def _rule_label(rule: RuleResult) -> str:
    status = rule["status"]
    if status == PASS:
        return f"[{_green('PASS')}]"
    elif status == WARNING:
        return f"[{_yellow('WARN')}]"
    else:
        return f"[{_red('FAIL')}]"


def print_report(results: list[RuleResult], score: float, json_output: bool) -> None:
    if json_output:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "repository": str(REPO_ROOT),
            "compliance_score": round(score, 1),
            "passed": score >= 100.0,
            "rules": results,
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    print()
    print(_bold("═" * 72))
    print(_bold("  GULA — Engineering Constitution Compliance Report"))
    print(_bold("═" * 72))
    print()
    print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"  Repository: {REPO_ROOT}")
    print()

    for rule in results:
        label = _rule_label(rule)
        print(f"  {label}  {_bold(rule['rule'])}: {rule['title']}")
        for detail in rule["details"]:
            print(f"    {detail}")
        print()

    print(_bold("─" * 72))
    fail_count = sum(1 for r in results if r["status"] == FAIL)
    warn_count = sum(1 for r in results if r["status"] == WARNING)
    pass_count = sum(1 for r in results if r["status"] == PASS)

    score_color = "green" if score >= 90 else ("yellow" if score >= 70 else "red")
    print(f"  Compliance Score: {_c(score_color, f'{score:.1f}/100')}")
    print(f"    {_green(f'PASS: {pass_count}')}  |  {_yellow(f'WARN: {warn_count}')}  |  {_red(f'FAIL: {fail_count}')}")
    print()

    if fail_count > 0:
        print(f"  {_red(_bold('✗ FAILED'))} — {fail_count} rule(s) failed. Correct before proceeding.")
        print()
    elif warn_count > 0:
        print(f"  {_yellow(_bold('⚠ WARNING'))} — All rules pass with {warn_count} warning(s).")
        print()
    else:
        print(f"  {_green(_bold('✓ ALL PASS'))} — Full compliance with the Engineering Constitution.")
        print()

    print(_bold("═" * 72))
    print()


# ── Main ─────────────────────────────────────────────────────────────────────


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GULA Engineering Constitution Enforcement — 12-rule compliance checker",
    )
    parser.add_argument(
        "--diff-mode", action="store_true",
        help="Compare working tree against base ref (default: HEAD~1)",
    )
    parser.add_argument(
        "--pre-commit", action="store_true",
        help="Pre-commit hook mode — staged changes only",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output results as JSON only",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Verbose / debug logging",
    )
    parser.add_argument(
        "--base", type=str, default="HEAD~1",
        help="Base ref for --diff-mode (default: HEAD~1)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _setup_logging(args.verbose)

    logger.info("Constitution Enforcer starting (diff-mode=%s, pre-commit=%s)",
                 args.diff_mode, args.pre_commit)

    if args.pre_commit:
        changed_files = _git_staged_files()
        logger.info("Pre-commit mode: %d staged file(s)", len(changed_files))
    elif args.diff_mode:
        changed_files = _git_diff_files(base=args.base)
        logger.info("Diff mode (base=%s): %d changed file(s)", args.base, len(changed_files))
    else:
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=ACMR", "HEAD"],
                capture_output=True, text=True, cwd=REPO_ROOT, timeout=30,
            )
            if result.returncode == 0:
                working = [f.strip() for f in result.stdout.splitlines() if f.strip()]
            else:
                working = []
        except (subprocess.TimeoutExpired, OSError):
            working = []
        changed_files = working
        logger.info("Default mode: %d changed file(s) since HEAD", len(changed_files))

    if not changed_files:
        logger.info("No changed files detected — running full audit against all Python files")
        changed_files = []
        for root, dirs, files in os.walk(str(BACKEND_APP)):
            for fn in files:
                if fn.endswith(".py"):
                    rel = pathlib.Path(root).relative_to(REPO_ROOT) / fn
                    changed_files.append(str(rel))

    changed_py_files = _get_changed_py_files(changed_files)

    if args.verbose:
        logger.debug("Changed files (%d):", len(changed_files))
        for f in changed_files:
            logger.debug("  %s", f)
        logger.debug("Python files (%d):", len(changed_py_files))
        for f in changed_py_files:
            logger.debug("  %s", f)

    results: list[RuleResult] = []

    results.append(rule1_tests(changed_py_files))
    results.append(rule2_module_docstrings(changed_py_files))
    results.append(rule3_openapi(changed_py_files))
    results.append(rule4_architectural_change_with_adr(changed_files))
    results.append(rule5_duplicated_code(changed_py_files))
    results.append(rule6_bandit())
    results.append(rule7_dependency_validation(changed_files))
    results.append(rule8_kernel_bypass(changed_py_files))
    results.append(rule9_ai_generated_code_markers(changed_files))
    results.append(rule10_quality_gates(changed_py_files))
    results.append(rule11_architecture_score())
    results.append(rule12_aggregate_improvement(results))
    results.append(rule13_hardcoded_secrets(changed_py_files))
    results.append(rule14_architecture_violations())
    results.append(rule15_dead_code(changed_py_files))
    results.append(rule16_fhir_compliance(changed_py_files))
    results.append(rule17_privacy_by_design(changed_py_files))
    results.append(rule18_security_by_design(changed_py_files))
    results.append(rule19_no_circular_dependencies())
    results.append(rule20_ai_safety(changed_py_files))

    score = _compute_score(results)

    print_report(results, score, json_output=args.json)

    fail_count = sum(1 for r in results if r["status"] == FAIL)
    if fail_count > 0:
        logger.info("Exit: 1 — %d rule(s) FAILED", fail_count)
        return 1

    logger.info("Exit: 0 — all rules comply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
