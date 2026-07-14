#!/usr/bin/env python3
"""
GULA Platform — Self-Audit & Self-Improvement Agent
=====================================================
Uses Claude AI to continuously audit the codebase, detect issues,
generate fixes, run tests, and commit improvements autonomously.

This script implements the "self-building / self-improving" loop:
  1. Collect context: git diff, test results, pyflakes output, metrics
  2. Ask Claude to audit and suggest fixes
  3. Apply safe auto-fixes
  4. Run tests — if pass, commit; if fail, revert and log
  5. Schedule the next cycle

Usage:
  python3 scripts/self_audit_agent.py                   # single audit run
  python3 scripts/self_audit_agent.py --watch 3600      # repeat every hour
  python3 scripts/self_audit_agent.py --fix              # auto-apply safe fixes
  python3 scripts/self_audit_agent.py --report-only     # report only, no fixes

Requirements:
  pip install anthropic
  export ANTHROPIC_API_KEY=your_key

Environment:
  ANTHROPIC_API_KEY   — Claude API key (required)
  GULA_AUDIT_MODEL    — Claude model (default: claude-sonnet-4-6)
  GULA_AUTO_FIX       — "true" to apply auto-fixes (default: false)
  GULA_AUDIT_INTERVAL — seconds between cycles in --watch mode (default: 3600)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from backend.app._compat import UTC

# ─── Config ───────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).parent.parent.resolve()
BACKEND_DIR = REPO_ROOT / "backend"
MODEL       = os.getenv("GULA_AUDIT_MODEL", "claude-sonnet-4-6")
AUTO_FIX    = os.getenv("GULA_AUTO_FIX", "false").lower() == "true"
INTERVAL    = int(os.getenv("GULA_AUDIT_INTERVAL", "3600"))
_ENV        = os.getenv("ENV", "production")

# Production safety: auto-fix is NEVER allowed in production.
# Operators must set ENV=development and GULA_AUTO_FIX=true explicitly.
if _ENV == "production" and AUTO_FIX:
    AUTO_FIX = False

# Max chars of context to send to Claude (to stay within token limits)
_MAX_DIFF_CHARS   = 8_000
_MAX_LINT_CHARS   = 3_000
_MAX_TEST_CHARS   = 4_000


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _run(cmd: list[str], cwd: Path = REPO_ROOT, timeout: int = 120) -> tuple[int, str]:
    """Run a subprocess and return (returncode, combined_stdout_stderr)."""
    try:
        result = subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, text=True,
            timeout=timeout, env={**os.environ, "PYTHONPATH": str(BACKEND_DIR)},
        )
        return result.returncode, (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        return -1, f"TIMEOUT after {timeout}s"
    except Exception as e:
        return -1, str(e)


def _collect_context() -> dict:
    """Gather everything Claude needs to audit the platform."""
    ctx: dict = {}

    # Recent git changes
    _, diff = _run(["git", "diff", "HEAD~3", "HEAD", "--stat"])
    _, diff_code = _run(["git", "diff", "HEAD~3", "HEAD", "--", "backend/app/", "*.py"])
    ctx["git_diff_stat"]   = diff[:_MAX_DIFF_CHARS]
    ctx["git_diff_code"]   = diff_code[:_MAX_DIFF_CHARS]

    # Lint results
    _, lint = _run(["python", "-m", "pyflakes", "app"], cwd=BACKEND_DIR)
    _, flake = _run(["python", "-m", "flake8", "app", "--select=E9,F821,F811,W605"], cwd=BACKEND_DIR)
    ctx["pyflakes"] = lint[:_MAX_LINT_CHARS]
    ctx["flake8"]   = flake[:_MAX_LINT_CHARS]

    # Test results
    _, tests = _run(["python", "-m", "pytest", "tests/", "-v", "--tb=short", "-q"], cwd=BACKEND_DIR, timeout=180)
    ctx["test_results"] = tests[:_MAX_TEST_CHARS]

    # Syntax check
    _, syntax = _run(["python", "-m", "py_compile", "app/main.py"], cwd=BACKEND_DIR)
    ctx["syntax_ok"] = "OK" if not syntax else syntax[:500]

    # Health metrics (if backend is running)
    _, health = _run(["python3", "-c", """
import urllib.request, json
try:
    r = urllib.request.urlopen('http://localhost:8000/health/deep', timeout=3)
    print(json.dumps(json.loads(r.read()), indent=2))
except Exception as e:
    print(f'Backend not reachable: {e}')
"""])
    ctx["health"] = health[:2_000]

    # File structure summary
    _, structure = _run(["find", "backend/app", "-name", "*.py", "-type", "f"])
    ctx["file_count"] = len(structure.split("\n")) if structure else 0

    return ctx


def _build_audit_prompt(ctx: dict) -> str:
    return f"""You are auditing the GULA Platform — a production-grade medical lab management SaaS built with FastAPI, PostgreSQL, Redis.

Your role: Production Security & Quality Auditor

## Context

### Recent Git Changes (stat)
```
{ctx.get('git_diff_stat', 'N/A')}
```

### Code Changes (diff)
```python
{ctx.get('git_diff_code', 'N/A')[:4000]}
```

### Lint Results (pyflakes)
```
{ctx.get('pyflakes', 'clean') or 'clean'}
```

### flake8 (E9/F821)
```
{ctx.get('flake8', 'clean') or 'clean'}
```

### Test Results
```
{ctx.get('test_results', 'N/A')}
```

### Syntax Check: {ctx.get('syntax_ok', 'unknown')}

### Health Metrics
```json
{ctx.get('health', 'N/A')}
```

### Total Python files: {ctx.get('file_count', 0)}

## Your Task

Analyze everything above and return a JSON response ONLY with this exact structure:

{{
  "grade": "GREEN" | "YELLOW" | "RED",
  "critical_issues": [
    {{"file": "path/to/file.py", "line": 42, "issue": "description", "fix": "exact fix"}}
  ],
  "high_issues": [...same format...],
  "medium_issues": [...same format...],
  "auto_fixable": [
    {{"file": "relative/path.py", "search": "exact text to find", "replace": "exact replacement text", "reason": "why"}}
  ],
  "summary": "one-paragraph assessment",
  "production_ready": true | false
}}

Rules:
- Only report CONFIRMED issues with specific file:line references
- auto_fixable items must be SAFE and have EXACT search/replace strings (no placeholders)
- Prefer finding 0 issues over reporting false positives
- Focus on: security, data integrity, correctness, performance
"""


def _apply_auto_fixes(fixes: list[dict]) -> list[str]:
    """Apply auto-fixable patches. Returns list of applied fix descriptions."""
    applied = []
    for fix in fixes:
        rel_path = fix.get("file", "")
        search   = fix.get("search", "")
        replace  = fix.get("replace", "")
        reason   = fix.get("reason", "")

        if not all([rel_path, search, replace]):
            continue

        target = BACKEND_DIR / rel_path if not rel_path.startswith("/") else Path(rel_path)
        if not target.exists():
            target = REPO_ROOT / rel_path
        if not target.exists():
            continue

        content = target.read_text()
        if search not in content:
            continue

        new_content = content.replace(search, replace, 1)
        target.write_text(new_content)
        applied.append(f"{rel_path}: {reason}")

    return applied


def _verify_after_fix() -> bool:
    """Run syntax check and tests after applying fixes. Return True if all pass."""
    rc, out = _run(["python", "-m", "py_compile", "app/main.py"], cwd=BACKEND_DIR)
    if rc != 0:
        return False
    rc, _out = _run(["python", "-m", "pytest", "tests/test_domain.py", "-q", "--tb=short"], cwd=BACKEND_DIR, timeout=60)
    return rc == 0


def _commit_fixes(applied: list[str]) -> bool:
    """Stage and commit auto-applied fixes."""
    if not applied:
        return False
    _run(["git", "add", "-A"])
    msg = "fix: self-audit agent auto-fixes\n\n" + "\n".join(f"- {a}" for a in applied)
    msg += "\n\nhttps://claude.ai/code/session_017XFDSYkLAT5uno4BMDf285"
    rc, _out = _run(["git", "commit", "-m", msg])
    return rc == 0


@dataclass
class AuditResult:
    grade:            str = "UNKNOWN"
    critical_issues:  list = field(default_factory=list)
    high_issues:      list = field(default_factory=list)
    medium_issues:    list = field(default_factory=list)
    auto_fixable:     list = field(default_factory=list)
    summary:          str = ""
    production_ready: bool = False
    raw_response:     str = ""
    applied_fixes:    list = field(default_factory=list)
    timestamp:        str = ""

    def print_report(self):
        {"GREEN": "\033[32m", "YELLOW": "\033[33m", "RED": "\033[31m"}.get(self.grade, "")

        for _severity, issues in [
            ("CRITICAL", self.critical_issues),
            ("HIGH", self.high_issues),
            ("MEDIUM", self.medium_issues),
        ]:
            if issues:
                for i in issues:
                    if i.get("fix"):
                        pass

        if self.applied_fixes:
            for _f in self.applied_fixes:
                pass



def run_audit(auto_fix: bool = False) -> AuditResult:
    """Run one full audit cycle."""
    result = AuditResult(timestamp=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"))

    try:
        import anthropic
    except ImportError:
        sys.exit(1)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit(1)

    ctx = _collect_context()

    client   = anthropic.Anthropic(api_key=api_key)
    prompt   = _build_audit_prompt(ctx)

    message = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text if message.content else "{}"
    result.raw_response = raw

    # Parse JSON response (Claude may wrap it in ```json ... ```)
    try:
        json_str = raw
        if "```json" in raw:
            json_str = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            json_str = raw.split("```")[1].split("```")[0].strip()
        data = json.loads(json_str)
    except Exception:
        result.summary = raw[:500]
        return result

    result.grade            = data.get("grade", "UNKNOWN")
    result.critical_issues  = data.get("critical_issues", [])
    result.high_issues      = data.get("high_issues", [])
    result.medium_issues    = data.get("medium_issues", [])
    result.auto_fixable     = data.get("auto_fixable", [])
    result.summary          = data.get("summary", "")
    result.production_ready = data.get("production_ready", False)

    # Auto-fix if enabled and there are safe fixes — gate on kill switch + policy
    if auto_fix and _ENV == "production":
        auto_fix = False

    if auto_fix and result.auto_fixable:
        applied = _apply_auto_fixes(result.auto_fixable)
        if applied:
            if _verify_after_fix():
                committed = _commit_fixes(applied)
                result.applied_fixes = applied
                if committed:
                    pass
            else:
                _run(["git", "checkout", "--", "."])

    # Save report
    report_path = REPO_ROOT / "logs" / f"audit_{result.timestamp.replace(' ', '_').replace(':', '').replace('-', '')}.json"
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps({
        "timestamp":        result.timestamp,
        "grade":            result.grade,
        "production_ready": result.production_ready,
        "critical_issues":  result.critical_issues,
        "high_issues":      result.high_issues,
        "medium_issues":    result.medium_issues,
        "applied_fixes":    result.applied_fixes,
        "summary":          result.summary,
    }, indent=2, ensure_ascii=False))

    return result


def main():
    parser = argparse.ArgumentParser(description="GULA Platform self-audit agent")
    parser.add_argument("--fix",         action="store_true", help="Auto-apply safe fixes")
    parser.add_argument("--report-only", action="store_true", help="Report only, no fixes")
    parser.add_argument("--watch",       type=int, metavar="SECONDS",
                        help="Repeat audit every N seconds (daemon mode)")
    args = parser.parse_args()

    auto_fix = (args.fix or AUTO_FIX) and not args.report_only

    if args.watch:
        pass

    cycle = 0
    while True:
        cycle += 1
        if args.watch:
            pass

        result = run_audit(auto_fix=auto_fix)
        result.print_report()

        if not args.watch:
            sys.exit(0 if result.production_ready else 1)

        time.sleep(args.watch)


if __name__ == "__main__":
    main()
