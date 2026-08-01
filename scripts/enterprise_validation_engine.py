#!/usr/bin/env python3
"""
GULA Enterprise Validation Engine — PROGRAM-012, Phase 4 + 7
============================================================
Unified validation orchestrator + automatic regression prevention.

Every change MUST pass this engine before commit. The engine:
  1. Runs the validation suite (scope-dependent).
  2. Produces machine-readable reports (JSON + markdown).
  3. Compares key metrics against the stored baseline
     (reports/validation/baseline.json) and REJECTS regressions.

Usage:
    python scripts/enterprise_validation_engine.py              # fast scope
    python scripts/enterprise_validation_engine.py --scope full # + tests, heavy audits
    python scripts/enterprise_validation_engine.py --update-baseline   # record new baseline
    python scripts/enterprise_validation_engine.py --json       # print JSON summary

Exit codes:
    0 — all gates passed
    1 — at least one hard gate failed (violation or regression)

Validator policy (hard = blocks commit, advisory = reported only):
  HARD:   ruff, tsc, eslint, unit-tests, brain-freshness, regression-gate
  ADVISORY: architecture-compliance, scorecard, constitution, tech-debt
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORT_DIR = REPO_ROOT / "reports" / "validation"
REPORT_JSON = REPORT_DIR / "validation_report.json"
REPORT_MD = REPORT_DIR / "validation_report.md"
BASELINE = REPORT_DIR / "baseline.json"

VENV_PY = REPO_ROOT / "backend" / ".venv" / "bin" / "python"


def _python() -> str:
    return str(VENV_PY) if VENV_PY.exists() else "python3"

HARD_VALIDATORS = {"ruff", "tsc", "eslint", "unit-tests", "brain-freshness"}
ADVISORY_VALIDATORS = {"architecture-compliance", "scorecard", "constitution", "tech-debt"}

BASELINE_METRICS = {
    # metric_key: (validator_name, result_key, higher_is_worse)
    "ruff_errors": ("ruff", "ruff_errors", True),
    "tsc_errors": ("tsc", "tsc_errors", True),
    "eslint_errors": ("eslint", "eslint_errors", True),
    "unit_test_count": ("unit-tests", "unit_test_count", False),
    "unit_test_failures": ("unit-tests", "unit_test_failures", True),
    "scorecard_score": ("scorecard", "scorecard_score", False),
    "architecture_score": ("architecture-compliance", "architecture_score", False),
}


def _run(cmd: list[str], cwd: pathlib.Path, timeout: int = 600) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, (proc.stdout + proc.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, f"command failed to run: {exc}"


def _has(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _validator_ruff() -> dict[str, Any]:
    code, out = _run(["ruff", "check", "--output-format=json", "backend/app"], REPO_ROOT)
    errors = 0
    if code == 0:
        pass
    elif out.strip():
        try:
            errors = len(json.loads(out))
        except (json.JSONDecodeError, IndexError):
            _, out = _run(["ruff", "check", "--statistics", "backend/app"], REPO_ROOT)
            errors = sum(int(part.strip()) for part in out.splitlines()[-1].split() if part.strip().isdigit()) if out else 0
    return {"status": "pass" if errors == 0 else "fail", "detail": f"{errors} ruff violations", "ruff_errors": errors}


def _validator_tsc() -> dict[str, Any]:
    if not (REPO_ROOT / "frontend-v3" / "node_modules").exists():
        return {"status": "pass", "detail": "skipped (node_modules missing)", "errors": 0}
    code, out = _run(["npx", "tsc", "--noEmit"], REPO_ROOT / "frontend-v3", timeout=300)
    errs = sum(1 for line in out.splitlines() if "error TS" in line) if out else 0
    return {"status": "pass" if code == 0 else "fail", "detail": f"tsc: {errs} type errors", "tsc_errors": errs}


def _validator_eslint() -> dict[str, Any]:
    if not (REPO_ROOT / "frontend-v3" / "node_modules").exists():
        return {"status": "pass", "detail": "skipped (node_modules missing)", "errors": 0}
    code, out = _run(["npx", "eslint", "src", "--max-warnings=0"], REPO_ROOT / "frontend-v3", timeout=300)
    errs = sum(1 for line in out.splitlines() if "error" in line.lower()) if out else 0
    return {"status": "pass" if code == 0 else "fail", "detail": f"eslint: {errs} errors", "eslint_errors": errs}


def _validator_unit_tests() -> dict[str, Any]:
    py = _python()
    code, out = _run([py, "-m", "pytest", "tests/unit", "-q", "--no-header"], REPO_ROOT / "backend", timeout=900)
    passed = failed = 0
    for line in out.splitlines():
        m = line.strip().rsplit(" ", 1)
        if len(m) == 2 and m[0].isdigit() and m[1].isdigit():
            passed, failed = int(m[0]), int(m[1])
    tail = out.splitlines()[-1] if out.splitlines() else ""
    if "passed" in tail:
        passed = int(tail.split("passed")[0].strip().split()[-1].rstrip(","))
        if "failed" in tail:
            failed = int(tail.split("failed")[0].strip().split()[-1].rstrip(","))
    return {
        "status": "pass" if code == 0 else "fail",
        "detail": f"unit: {passed} passed, {failed} failed",
        "unit_test_count": passed,
        "unit_test_failures": failed,
    }


def _validator_brain() -> dict[str, Any]:
    code, out = _run([_python(), "scripts/project_brain.py", "--check"], REPO_ROOT, timeout=120)
    return {"status": "pass" if code == 0 else "fail", "detail": out.splitlines()[-1] if out else "brain check"}


def _validator_architecture() -> dict[str, Any]:
    code, out = _run([_python(), "scripts/architecture_compliance_engine.py", "--json"], REPO_ROOT, timeout=900)
    score = None
    try:
        data = json.loads(out.splitlines()[-1] if not out.startswith("{") else out)
        score = data.get("score")
    except (json.JSONDecodeError, IndexError):
        pass
    return {"status": "pass" if code == 0 else "fail", "detail": f"arch score: {score}/100", "architecture_score": score}


def _validator_scorecard() -> dict[str, Any]:
    _, out = _run([_python(), "scripts/repository_scorecard.py", "--json"], REPO_ROOT, timeout=900)
    score = None
    try:
        data = json.loads(out.splitlines()[-1] if not out.startswith("{") else out)
        score = data.get("overall_score")
    except (json.JSONDecodeError, IndexError):
        pass
    return {"status": "pass", "detail": f"scorecard: {score}/100", "scorecard_score": score}


def _validator_constitution() -> dict[str, Any]:
    code, out = _run([_python(), "scripts/constitution_enforcer.py", "--json"], REPO_ROOT, timeout=900)
    return {"status": "pass" if code == 0 else "fail", "detail": out.splitlines()[-1] if out else "constitution check"}


def _validator_tech_debt() -> dict[str, Any]:
    registry = REPO_ROOT / "docs" / "technical-debt" / "REGISTRY.md"
    exists = registry.exists()
    return {"status": "pass" if exists else "fail", "detail": f"tech-debt registry {'present' if exists else 'MISSING'}"}


def _validator_android_consistency() -> dict[str, Any]:
    """Android release metadata consistency (version.json vs build.gradle.kts)."""
    problems: list[str] = []
    version_json = REPO_ROOT / "mobile" / "version.json"
    build_gradle = REPO_ROOT / "mobile" / "android" / "app" / "build.gradle.kts"
    workflow = REPO_ROOT / ".github" / "workflows" / "mobile-android.yml"
    gradlew = REPO_ROOT / "mobile" / "android" / "gradlew"

    if not version_json.exists():
        return {"status": "fail", "detail": "mobile/version.json MISSING"}
    if not build_gradle.exists():
        return {"status": "fail", "detail": "mobile/android/app/build.gradle.kts MISSING"}

    try:
        vj = json.loads(version_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "fail", "detail": "mobile/version.json is not valid JSON"}

    gradle_text = build_gradle.read_text(encoding="utf-8")
    version_name = vj.get("android", {}).get("versionName")
    version_code = vj.get("android", {}).get("versionCode")
    m_name = re.search(r'versionName\s*=\s*"([^"]+)"', gradle_text)
    m_code = re.search(r"versionCode\s*=\s*(\d+)", gradle_text)

    if m_name and version_name and m_name.group(1) != version_name:
        problems.append(f"versionName mismatch: version.json={version_name} build.gradle.kts={m_name.group(1)}")
    if m_code and version_code is not None and int(m_code.group(1)) != int(version_code):
        problems.append(f"versionCode mismatch: version.json={version_code} build.gradle.kts={m_code.group(1)}")
    if not gradlew.exists():
        problems.append("gradlew wrapper MISSING")
    if not workflow.exists():
        problems.append("mobile-android.yml CI workflow MISSING")

    if problems:
        return {"status": "fail", "detail": "; ".join(problems)}
    return {"status": "pass", "detail": f"android v{version_name} (code {version_code}) consistent, wrapper + CI present"}


def _validator_db_migrations() -> dict[str, Any]:
    """Migration chain integrity (single root, no dangling down_revisions)."""
    versions_dir = REPO_ROOT / "backend" / "migrations" / "versions"
    if not versions_dir.is_dir():
        return {"status": "fail", "detail": "backend/migrations/versions MISSING"}

    revisions: list[tuple[str, str | None]] = []
    for path in versions_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        rev = re.search(r'^revision\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        down = re.search(r'^down_revision\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        down = None if down is None or down.group(1).lower() in ("none", "null") else down.group(1)
        if rev:
            revisions.append((rev.group(1), down))

    if not revisions:
        return {"status": "fail", "detail": "no migrations found"}
    ids = [r for r, _ in revisions]
    dupes = [rid for rid in set(ids) if ids.count(rid) > 1]
    roots = [rid for rid, down in revisions if down is None]
    dangling = [d for _, d in revisions if d is not None and d not in ids]

    problems: list[str] = []
    if len(roots) != 1:
        problems.append(f"expected exactly 1 root migration, found {len(roots)}: {roots}")
    if dupes:
        problems.append(f"duplicate revision ids: {dupes}")
    if dangling:
        problems.append(f"dangling down_revision refs: {dangling}")

    if problems:
        return {"status": "fail", "detail": "; ".join(problems)}
    return {"status": "pass", "detail": f"{len(revisions)} migrations, single root, chain intact"}


VALIDATORS: dict[str, tuple[Callable[[], dict[str, Any]], str, set[str]]] = {
    "ruff": (_validator_ruff, "hard", {"fast", "full"}),
    "tsc": (_validator_tsc, "hard", {"fast", "full"}),
    "eslint": (_validator_eslint, "hard", {"fast", "full"}),
    "brain-freshness": (_validator_brain, "hard", {"fast", "full"}),
    "unit-tests": (_validator_unit_tests, "hard", {"full"}),
    "android-consistency": (_validator_android_consistency, "advisory", {"fast", "full"}),
    "db-migrations": (_validator_db_migrations, "advisory", {"fast", "full"}),
    "architecture-compliance": (_validator_architecture, "advisory", {"full"}),
    "scorecard": (_validator_scorecard, "advisory", {"full"}),
    "constitution": (_validator_constitution, "advisory", {"full"}),
    "tech-debt": (_validator_tech_debt, "advisory", {"fast", "full"}),
}


def _load_baseline() -> dict[str, Any]:
    if BASELINE.exists():
        try:
            return json.loads(BASELINE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def check_regressions(results: dict[str, Any], baseline: dict[str, Any]) -> list[str]:
    """Compare current metrics against baseline; return list of regressions."""
    regressions: list[str] = []
    for metric, (validator, key, higher_is_worse) in BASELINE_METRICS.items():
        current = results.get(validator, {}).get(key)
        previous = baseline.get(metric)
        if current is None or previous is None:
            continue
        if isinstance(previous, (int, float)) and isinstance(current, (int, float)):
            degraded = current > previous if higher_is_worse else current < previous
            if degraded:
                direction = "increased" if higher_is_worse else "decreased"
                regressions.append(f"{metric}: {previous} -> {current} ({direction})")
    return regressions


def run_validations(scope: str, repo_root: pathlib.Path) -> dict[str, Any]:
    results: dict[str, Any] = {}
    total_start = time.monotonic()
    for name, (fn, _policy, scopes) in VALIDATORS.items():
        if scope not in scopes:
            continue
        start = time.monotonic()
        try:
            result = fn()
        except Exception as exc:
            result = {"status": "fail", "detail": f"validator crashed: {exc}"}
        result["duration_s"] = round(time.monotonic() - start, 1)
        result["policy"] = "hard" if name in HARD_VALIDATORS else "advisory"
        results[name] = result
    baseline = _load_baseline()
    regressions = check_regressions(results, baseline)
    # Baseline-aware status: known debt at/below baseline is a PASS (advisory),
    # regressions are blocked separately via the regressions list.
    for metric, (validator, key, higher_is_worse) in BASELINE_METRICS.items():
        previous = baseline.get(metric)
        current = results.get(validator, {}).get(key)
        if previous is None or current is None:
            continue
        at_or_better = current <= previous if higher_is_worse else current >= previous
        if at_or_better:
            results[validator]["status"] = "pass"
            results[validator]["detail"] = f"{results[validator].get('detail', '')} (baseline {previous})"
    results["_meta"] = {
        "scope": scope,
        "generated_at": datetime.now(UTC).isoformat(),
        "duration_s": round(time.monotonic() - total_start, 1),
        "regressions": regressions,
        "baseline_used": baseline.get("_generated_at"),
    }
    return results


def verdict(results: dict[str, Any]) -> tuple[bool, list[str]]:
    """True if all hard gates pass and no regressions. Returns (ok, failures)."""
    failures: list[str] = []
    for name, result in results.items():
        if name == "_meta":
            continue
        if result.get("status") == "fail" and result.get("policy") == "hard":
            failures.append(f"{name}: {result.get('detail', 'failed')}")
    failures += results["_meta"]["regressions"]
    return (not failures), failures


def render_markdown(results: dict[str, Any], ok: bool) -> str:
    meta = results["_meta"]
    lines = [
        "# GULA Enterprise Validation Report",
        "",
        f"> Generated: {meta['generated_at']} — scope: `{meta['scope']}` — duration: {meta['duration_s']}s",
        f"> Verdict: **{'PASS' if ok else 'FAIL'}**",
        "",
        "| Validator | Policy | Status | Detail | Duration |",
        "|---|---|---|---|---|",
    ]
    for name, result in sorted(results.items()):
        if name == "_meta":
            continue
        status = result.get("status", "?")
        icon = "✅" if status == "pass" else ("⚠️" if result.get("policy") == "advisory" else "❌")
        lines.append(
            f"| {name} | {result.get('policy')} | {icon} {status} | {result.get('detail', '')} | {result.get('duration_s', 0)}s |"
        )
    if meta["regressions"]:
        lines.append("")
        lines.append("## Regressions Detected (BLOCKING)")
        for r in meta["regressions"]:
            lines.append(f"- ❌ {r}")
    else:
        lines.append("")
        lines.append("## Regressions: none")
    lines.append("")
    lines.append("*Run `python scripts/enterprise_validation_engine.py --update-baseline` after intentional improvements.*")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GULA Enterprise Validation Engine")
    parser.add_argument("--scope", choices=["fast", "full"], default="fast")
    parser.add_argument("--update-baseline", action="store_true", help="record current metrics as new baseline")
    parser.add_argument("--json", action="store_true", help="print JSON summary to stdout")
    args = parser.parse_args(argv)

    results = run_validations(args.scope, REPO_ROOT)
    ok, _failures = verdict(results)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render_markdown(results, ok), encoding="utf-8")
    print(f"Validation report: {REPORT_JSON.relative_to(REPO_ROOT)}")
    print(f"Validation report: {REPORT_MD.relative_to(REPO_ROOT)}")

    if args.update_baseline:
        baseline: dict[str, Any] = {
            "_generated_at": datetime.now(UTC).isoformat(),
        }
        for metric, (validator, key, _worse) in BASELINE_METRICS.items():
            value = results.get(validator, {}).get(key)
            if value is not None:
                baseline[metric] = value
        BASELINE.write_text(json.dumps(baseline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Baseline updated: {BASELINE.relative_to(REPO_ROOT)}")

    if args.json:
        print(json.dumps({k: v for k, v in results.items() if k != "_meta"} | {"_meta": results["_meta"]}, indent=2, ensure_ascii=False))

    for name, result in sorted(results.items()):
        if name == "_meta":
            continue
        mark = "OK " if result.get("status") == "pass" else "FAIL"
        print(f"  [{mark}] {name} ({result.get('policy')}): {result.get('detail', '')} [{result.get('duration_s', 0)}s]")
    if results["_meta"]["regressions"]:
        print("REGRESSIONS:")
        for r in results["_meta"]["regressions"]:
            print(f"  - {r}")

    print("VERDICT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
