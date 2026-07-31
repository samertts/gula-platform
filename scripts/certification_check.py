#!/usr/bin/env python3
"""
GULA Enterprise Readiness Certification Check
==============================================
Final audit — runs all tools and produces certification decision.

Runs:
  1. Architecture Compliance Engine
  2. Repository Scorecard
  3. Enterprise Metrics
  4. Quality Gate
  5. Technical Debt Registry

Computes certification level based on:
  - Quality Index >= 900 = PLATINUM
  - Quality Index >= 800 = GOLD
  - Quality Index >= 700 = SILVER
  - Quality Index >= 600 = BRONZE
  - Below 600          = NOT CERTIFIED

Additional criteria:
  - P0 debt items must be 0 for any certification
  - Architecture compliance must be >= 50 for Silver+
  - Test coverage must be >= 60% for Gold+

Usage:
  python scripts/certification_check.py              # colorized terminal report
  python scripts/certification_check.py --json       # machine-readable JSON
  python scripts/certification_check.py --focus arch # run specific checks only
  python scripts/certification_check.py --ci         # CI-friendly output (exit code)

Exit codes:
  0 — Certified (BRONZE or higher)
  1 — Certifiable with conditions
  2 — Not certified
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from datetime import UTC, datetime
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

_RESET = "\033[0m"
_RED = "\033[91m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_CYAN = "\033[96m"
_MAGENTA = "\033[95m"
_BOLD = "\033[1m"
_WHITE = "\033[97m"
_BG_RED = "\033[41m"
_BG_GREEN = "\033[42m"
_BG_YELLOW = "\033[43m"
_BG_BLUE = "\033[44m"

_USE_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    palette = {
        "red": _RED, "green": _GREEN, "yellow": _YELLOW, "cyan": _CYAN,
        "bold": _BOLD, "magenta": _MAGENTA, "white": _WHITE, "reset": _RESET,
        "bg_red": _BG_RED, "bg_green": _BG_GREEN, "bg_yellow": _BG_YELLOW,
        "bg_blue": _BG_BLUE,
    }
    return f"{palette.get(code, _RESET)}{text}{_RESET}"


CERT_LEVELS = {
    "PLATINUM": {"min_qi": 900, "min_arch": 80, "min_coverage": 80, "p0_max": 0, "order": 5},
    "GOLD": {"min_qi": 800, "min_arch": 60, "min_coverage": 60, "p0_max": 0, "order": 4},
    "SILVER": {"min_qi": 700, "min_arch": 50, "min_coverage": 0, "p0_max": 0, "order": 3},
    "BRONZE": {"min_qi": 600, "min_arch": 0, "min_coverage": 0, "p0_max": 0, "order": 2},
    "NOT CERTIFIED": {"min_qi": 0, "min_arch": 0, "min_coverage": 0, "p0_max": 999, "order": 1},
}


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


class CertificationResult:
    def __init__(self) -> None:
        self.quality_index: int = 0
        self.quality_index_max: int = 1000
        self.quality_grade: str = "F"
        self.arch_compliance_score: float = 0.0
        self.test_coverage_pct: int = 0
        self.p0_count: int = 0
        self.p1_count: int = 0
        self.total_debt_items: int = 0
        self.total_debt_hours: float = 0.0
        self.scorecard_overall: int = 0
        self.scorecard_grade: str = "F"
        self.quality_gate_status: str = "FAIL"
        self.certification_level: str = "NOT CERTIFIED"
        self.certification_order: int = 0
        self.reasons: list[str] = []
        self.conditions: list[str] = []
        self.component_scores: dict[str, int] = {}
        self.check_results: dict[str, dict[str, Any]] = {}
        self.tool_outputs: dict[str, Any] = {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "repository": str(REPO_ROOT),
            "certification": {
                "level": self.certification_level,
                "order": self.certification_order,
            },
            "quality_index": {
                "total": self.quality_index,
                "max": self.quality_index_max,
                "grade": self.quality_grade,
                "components": self.component_scores,
            },
            "scorecard": {
                "overall": self.scorecard_overall,
                "grade": self.scorecard_grade,
            },
            "architecture": {
                "compliance_score": self.arch_compliance_score,
            },
            "test_coverage": self.test_coverage_pct,
            "technical_debt": {
                "total_items": self.total_debt_items,
                "total_hours": self.total_debt_hours,
                "p0_count": self.p0_count,
                "p1_count": self.p1_count,
            },
            "quality_gate": self.quality_gate_status,
            "reasons": self.reasons,
            "conditions": self.conditions,
            "checks": self.check_results,
        }


def run_compliance_engine() -> dict[str, Any]:
    cache_path = REPO_ROOT / "docs" / "metrics" / "compliance_cache.json"
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    proc = _run_script("architecture_compliance_engine.py", ["--json", "--exclude-dirs", "tests,migrations,__pycache__"], timeout=120)
    if proc.returncode == -1:
        return {"score": 0, "results": [], "error": proc.stderr}
    if not proc.stdout.strip():
        return {"score": 0, "results": [], "error": "no output"}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = json.loads(proc.stdout)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(proc.stdout)
        return data
    except json.JSONDecodeError:
        return {"score": 0, "results": [], "error": "json parse failed"}


def run_scorecard() -> dict[str, Any]:
    cache_path = REPO_ROOT / "docs" / "metrics" / "scorecard_cache.json"
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    proc = _run_script("repository_scorecard.py", ["--json"], timeout=120)
    if proc.returncode == -1:
        return {"overall_score": 0, "grade": "F", "axes": [], "error": proc.stderr}
    if not proc.stdout.strip():
        return {"overall_score": 0, "grade": "F", "axes": [], "error": "no output"}
    try:
        data = json.loads(proc.stdout)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(proc.stdout)
        return data
    except json.JSONDecodeError:
        return {"overall_score": 0, "grade": "F", "axes": [], "error": "json parse failed"}


def run_enterprise_metrics() -> dict[str, Any]:
    cache_path = REPO_ROOT / "docs" / "metrics" / "enterprise_metrics_cache.json"
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    proc = _run_script("enterprise_metrics.py", ["--json"], timeout=120)
    if proc.returncode == -1:
        return {"quality_index": {"total": 0, "max": 1000, "grade": "F"}, "error": proc.stderr}
    if not proc.stdout.strip():
        return {"quality_index": {"total": 0, "max": 1000, "grade": "F"}, "error": "no output"}
    try:
        data = json.loads(proc.stdout)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(proc.stdout)
        return data
    except json.JSONDecodeError:
        return {"quality_index": {"total": 0, "max": 1000, "grade": "F"}, "error": "json parse failed"}


def run_quality_gate() -> dict[str, Any]:
    cache_path = REPO_ROOT / "docs" / "metrics" / "quality_gate_cache.json"
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    proc = _run_script("quality_gate.py", ["--ci"], timeout=120)
    if proc.returncode == -1:
        return {"overall": "FAIL", "checks": [], "error": proc.stderr}
    if not proc.stdout.strip():
        return {"overall": "FAIL", "checks": [], "error": "no output"}
    try:
        data = json.loads(proc.stdout)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(proc.stdout)
        return data
    except json.JSONDecodeError:
        return {"overall": "FAIL", "checks": [], "error": "json parse failed"}


def run_debt_registry() -> dict[str, Any]:
    registry_path = REPO_ROOT / "docs" / "technical-debt" / "registry.json"
    if registry_path.exists():
        try:
            return json.loads(registry_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    proc = _run_script("technical_debt_registry.py", ["--json", "--refresh"], timeout=300)
    if proc.returncode == -1:
        return {"meta": {"total_items": 0, "total_est_hours": 0, "by_priority": {}}, "items": [], "error": proc.stderr}
    if not proc.stdout.strip():
        return {"meta": {"total_items": 0, "total_est_hours": 0, "by_priority": {}}, "items": [], "error": "no output"}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"meta": {"total_items": 0, "total_est_hours": 0, "by_priority": {}}, "items": [], "error": "json parse failed"}


def get_scorecard_axis(data: dict[str, Any], name: str) -> int:
    for ax in data.get("axes", []):
        if ax.get("name") == name:
            return ax.get("score", 0)
    return 0


def compute_certification(result: CertificationResult) -> None:
    p0_ok = result.p0_count == 0
    qi = result.quality_index
    arch = result.arch_compliance_score
    cov = result.test_coverage_pct
    qg_pass = result.quality_gate_status == "PASS"

    if not qg_pass:
        result.reasons.append("Quality Gate is not passing")

    for level_name in ["PLATINUM", "GOLD", "SILVER", "BRONZE", "NOT CERTIFIED"]:
        criteria = CERT_LEVELS[level_name]

        if not p0_ok and level_name != "NOT CERTIFIED":
            continue

        if qi < criteria["min_qi"]:
            continue

        if level_name in ("SILVER", "GOLD", "PLATINUM"):
            if arch < criteria["min_arch"]:
                result.conditions.append(
                    f"Architecture compliance {arch:.0f}/{criteria['min_arch']} needed for {level_name}"
                )
                continue

        if level_name in ("GOLD", "PLATINUM"):
            if cov < criteria["min_coverage"]:
                result.conditions.append(
                    f"Test coverage {cov}%/{criteria['min_coverage']}% needed for {level_name}"
                )
                continue

        if not qg_pass and level_name != "NOT CERTIFIED":
            continue

        result.certification_level = level_name
        result.certification_order = criteria["order"]
        return

    result.certification_level = "NOT CERTIFIED"
    result.certification_order = 1


def format_certification_report(result: CertificationResult) -> str:
    lines: list[str] = []

    lines.append("")
    lines.append(f"  {_c('bold', '╔════════════════════════════════════════════════════════════════╗')}")
    lines.append(f"  {_c('bold', '║        GULA ENTERPRISE READINESS CERTIFICATION CHECK            ║')}")
    lines.append(f"  {_c('bold', '╚════════════════════════════════════════════════════════════════╝')}")
    lines.append("")

    now_str = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append(f"  Timestamp:  {now_str}")
    lines.append(f"  Repository: {REPO_ROOT.name}")
    lines.append("")

    level = result.certification_level
    order = result.certification_order
    if level == "PLATINUM":
        badge = _c("bg_green", f"  {level}  ")
    elif level == "GOLD":
        badge = _c("bg_yellow", f"  {level}  ")
    elif level == "SILVER":
        badge = _c("white", f"  {level}  ")
    elif level == "BRONZE":
        badge = _c("bg_blue", f"  {level}  ")
    else:
        badge = _c("bg_red", f"  {level}  ")

    lines.append(f"  {_c('bold', 'CERTIFICATION:')}  {badge}")
    lines.append("")

    qi = result.quality_index
    qi_max = result.quality_index_max
    qi_grade = result.quality_grade
    qi_color = "green" if qi >= 900 else ("cyan" if qi >= 800 else ("yellow" if qi >= 700 else ("magenta" if qi >= 600 else "red")))
    qibar = "█" * max(0, min(qi // (qi_max // 20), 20)) + "░" * max(0, 20 - max(0, min(qi // (qi_max // 20), 20)))
    lines.append(f"  {_c('bold', 'Core Metrics:')}")
    lines.append(f"    Quality Index:           {_c(qi_color, str(qi))}/{qi_max} ({_c(qi_color, qi_grade)})  {qibar}")
    lines.append(f"    Architecture Compliance: {result.arch_compliance_score:.1f}/100")
    lines.append(f"    Test Coverage:           {result.test_coverage_pct}%")
    lines.append(f"    Scorecard Overall:       {result.scorecard_overall}/100 ({result.scorecard_grade})")
    lines.append(f"    Quality Gate:            {result.quality_gate_status}")
    lines.append("")

    lines.append(f"  {_c('bold', 'Technical Debt:')}")
    p0_col = "red" if result.p0_count > 0 else "green"
    lines.append(f"    Total Items:  {result.total_debt_items}")
    lines.append(f"    Total Hours:  {result.total_debt_hours:.0f}")
    lines.append(f"    P0 Items:     {_c(p0_col, str(result.p0_count))}")
    lines.append(f"    P1 Items:     {result.p1_count}")
    lines.append("")

    lines.append(f"  {_c('bold', 'Component Scores:')}")
    max_name_len = max(len(n) for n in result.component_scores) if result.component_scores else 10
    for name, raw_score in sorted(result.component_scores.items()):
        score = int(raw_score) if isinstance(raw_score, (int, float, str)) and str(raw_score).isdigit() else 0
        c = "green" if score >= 80 else ("yellow" if score >= 50 else "red")
        bar = "█" * max(0, min(score // 5, 20)) + "░" * max(0, 20 - max(0, min(score // 5, 20)))
        lines.append(f"    {name:{max_name_len}}  {bar}  {_c(c, f'{score:>3}')}/100")

    lines.append("")

    if result.reasons:
        lines.append(f"  {_c('bold', 'Reasons for Current Level:')}")
        for r in result.reasons:
            lines.append(f"    {_c('red', '✗')} {r}")
        lines.append("")

    if result.conditions:
        lines.append(f"  {_c('bold', 'Conditions for Upgrade:')}")
        for c in result.conditions:
            lines.append(f"    {_c('yellow', '→')} {c}")
        lines.append("")

    lines.append(f"  {_c('bold', 'Check Results:')}")
    for check_name, check_data in result.check_results.items():
        status = check_data.get("status", "UNKNOWN")
        if status == "PASS":
            badge = _c("green", "  PASS  ")
        elif status == "WARNING":
            badge = _c("yellow", " WARNING ")
        else:
            badge = _c("red", "  FAIL  ")
        detail = check_data.get("detail", "")
        lines.append(f"  {badge}  {check_name}")
        if detail:
            lines.append(f"          {detail}")

    lines.append("")
    lines.append(f"  {_c('bold', '─' * 72)}")
    lines.append(f"  Certification Level: {badge}")
    lines.append("")

    if result.certification_level == "NOT CERTIFIED":
        lines.append(f"  {_c('red', '✖ NOT CERTIFIED')} — The platform does not meet minimum certification criteria.")
        lines.append(f"  {_c('bold', 'Minimum Requirements:')}")
        lines.append("    - Quality Index >= 600")
        lines.append("    - Zero P0 debt items")
        lines.append("    - Quality Gate must pass")
    elif result.certification_level == "BRONZE":
        lines.append(f"  {_c('cyan', '✔ BRONZE')} — Foundation established, governance frameworks operational.")
        lines.append(f"  {_c('bold', 'Path to SILVER:')}")
        if result.p0_count > 0:
            lines.append(f"    - Resolve {result.p0_count} P0 debt items (currently blocking)")
        if result.arch_compliance_score < 50:
            lines.append(f"    - Increase Architecture Compliance to 50+ (currently {result.arch_compliance_score:.0f})")
        lines.append("    - Reach Quality Index of 700+")
    elif result.certification_level == "SILVER":
        lines.append(f"  {_c('white', '✔ SILVER')} — Solid foundation with active quality management.")
        lines.append(f"  {_c('bold', 'Path to GOLD:')}")
        if result.arch_compliance_score < 60:
            lines.append(f"    - Increase Architecture Compliance to 60+ (currently {result.arch_compliance_score:.0f})")
        if result.test_coverage_pct < 60:
            lines.append(f"    - Increase Test Coverage to 60%+ (currently {result.test_coverage_pct}%)")
        lines.append("    - Reach Quality Index of 800+")
    elif result.certification_level == "GOLD":
        lines.append(f"  {_c('yellow', '✔ GOLD')} — Near-enterprise readiness with minor gaps.")
        lines.append(f"  {_c('bold', 'Path to PLATINUM:')}")
        if result.arch_compliance_score < 80:
            lines.append(f"    - Increase Architecture Compliance to 80+ (currently {result.arch_compliance_score:.0f})")
        if result.test_coverage_pct < 80:
            lines.append(f"    - Increase Test Coverage to 80%+ (currently {result.test_coverage_pct}%)")
        lines.append("    - Reach Quality Index of 900+")
    elif result.certification_level == "PLATINUM":
        lines.append(f"  {_c('green', '✔ PLATINUM')} — Enterprise-ready. All thresholds met.")

    lines.append("")
    lines.append(f"  {_c('bold', '═' * 72)}")
    lines.append("")

    return "\n".join(lines)


def format_json_report(result: CertificationResult) -> str:
    return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GULA Enterprise Readiness Certification Check",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--ci", action="store_true", help="CI-friendly mode (JSON + exit code)")
    parser.add_argument(
        "--focus", type=str, default=None,
        choices=["arch", "scorecard", "metrics", "quality", "debt", "all"],
        help="Run specific checks only (default: all)",
    )
    args = parser.parse_args()

    if args.json or args.ci:
        global _USE_COLOR
        _USE_COLOR = False

    result = CertificationResult()

    focus = args.focus or "all"
    run_all = focus == "all"

    # ── 1. Architecture Compliance Engine ──
    if run_all or focus == "arch":
        arch_data = run_compliance_engine()
        result.tool_outputs["architecture_compliance"] = arch_data
        result.arch_compliance_score = arch_data.get("score", 0)
        error = arch_data.get("error")
        if error:
            result.check_results["Architecture Compliance"] = {
                "status": "WARNING", "detail": f"Engine error: {error}",
            }
        else:
            passed = not any(r.get("status") == "FAIL" for r in arch_data.get("results", []))
            has_warnings = any(r.get("status") == "WARNING" for r in arch_data.get("results", []))
            if passed and not has_warnings:
                status = "PASS"
            elif passed:
                status = "WARNING"
            else:
                status = "FAIL"
            result.check_results["Architecture Compliance"] = {
                "status": status,
                "detail": f"Score: {result.arch_compliance_score:.0f}/100",
            }

    # ── 2. Repository Scorecard ──
    if run_all or focus == "scorecard":
        scorecard_data = run_scorecard()
        result.tool_outputs["scorecard"] = scorecard_data
        result.scorecard_overall = scorecard_data.get("overall_score", 0)
        result.scorecard_grade = scorecard_data.get("grade", "F")
        error = scorecard_data.get("error")
        if error:
            result.check_results["Repository Scorecard"] = {
                "status": "WARNING", "detail": f"Scorecard error: {error}",
            }
        else:
            status = "PASS" if result.scorecard_overall >= 70 else ("WARNING" if result.scorecard_overall >= 60 else "FAIL")
            result.check_results["Repository Scorecard"] = {
                "status": status,
                "detail": f"Score: {result.scorecard_overall}/100 ({result.scorecard_grade})",
            }

        # Extract component scores
        for ax in scorecard_data.get("axes", []):
            name = ax.get("name", "")
            score = ax.get("score", 0)
            if name == "Test Coverage":
                result.test_coverage_pct = score
            result.component_scores[name] = score

    # ── 3. Enterprise Metrics ──
    if run_all or focus == "metrics":
        metrics_data = run_enterprise_metrics()
        result.tool_outputs["enterprise_metrics"] = metrics_data
        qi = metrics_data.get("quality_index", {})
        result.quality_index = qi.get("total", 0)
        result.quality_index_max = qi.get("max", 1000)
        result.quality_grade = qi.get("grade", "F")
        error = metrics_data.get("error")
        if error:
            result.check_results["Enterprise Metrics"] = {
                "status": "WARNING", "detail": f"Metrics error: {error}",
            }
        else:
            status = "PASS" if result.quality_index >= 600 else "FAIL"
            result.check_results["Enterprise Metrics"] = {
                "status": status,
                "detail": f"Quality Index: {result.quality_index}/{result.quality_index_max} ({result.quality_grade})",
            }

        components = qi.get("components", {})
        if components:
            for comp_name, comp_val in components.items():
                if isinstance(comp_val, dict):
                    score = comp_val.get("score", 0)
                elif isinstance(comp_val, (list, tuple)) and len(comp_val) == 2:
                    score = comp_val[0]
                else:
                    score = comp_val
                result.component_scores[f"QI: {comp_name}"] = int(score) if score else 0

    # ── 4. Quality Gate ──
    if run_all or focus == "quality":
        qg_data = run_quality_gate()
        result.tool_outputs["quality_gate"] = qg_data
        result.quality_gate_status = qg_data.get("overall", "FAIL")
        error = qg_data.get("error")
        if error:
            result.check_results["Quality Gate"] = {
                "status": "WARNING", "detail": f"Quality gate error: {error}",
            }
        else:
            checks = qg_data.get("checks", [])
            passed_checks = sum(1 for c in checks if c.get("status") == "PASS")
            failed_checks = sum(1 for c in checks if c.get("status") == "FAIL")
            result.check_results["Quality Gate"] = {
                "status": result.quality_gate_status,
                "detail": f"{passed_checks} passed, {failed_checks} failed",
            }

    # ── 5. Technical Debt Registry ──
    if run_all or focus == "debt":
        debt_data = run_debt_registry()
        result.tool_outputs["technical_debt"] = debt_data
        meta = debt_data.get("meta", {})
        result.total_debt_items = meta.get("total_items", 0)
        result.total_debt_hours = meta.get("total_est_hours", 0)
        by_priority = meta.get("by_priority", {})
        result.p0_count = by_priority.get("P0", 0)
        result.p1_count = by_priority.get("P1", 0)
        error = debt_data.get("error")
        if error:
            result.check_results["Technical Debt"] = {
                "status": "WARNING", "detail": f"Debt registry error: {error}",
            }
        else:
            if result.p0_count > 0:
                status = "FAIL"
            elif result.p1_count > 5:
                status = "WARNING"
            else:
                status = "PASS"
            result.check_results["Technical Debt"] = {
                "status": status,
                "detail": f"{result.total_debt_items} items, P0={result.p0_count}, P1={result.p1_count}",
            }

    # ── Compute Certification ──
    compute_certification(result)

    # If we only have component scores from the scorecard, fill in what we know
    if not result.component_scores and result.scorecard_overall:
        pass

    # ── Output ──
    if args.ci:
        output = result.to_dict()
        output["exit_code"] = 0 if result.certification_order >= 2 else 2
        print(json.dumps(output, indent=2))
        return output["exit_code"]

    if args.json:
        print(format_json_report(result))
        return 0

    print(format_certification_report(result))

    exit_codes = {
        "PLATINUM": 0,
        "GOLD": 0,
        "SILVER": 0,
        "BRONZE": 0,
        "NOT CERTIFIED": 2,
    }
    return exit_codes.get(result.certification_level, 2)


if __name__ == "__main__":
    sys.exit(main())
