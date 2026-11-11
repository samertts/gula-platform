#!/usr/bin/env python3
"""
GULA Platform — Self-Audit & Self-Improvement Agent
=====================================================
Uses Claude AI to continuously audit the codebase, detect issues,
generate fixes, run tests, and commit improvements autonomously.

This script implements the "self-building / self-improving" loop:
  1. Collect context: git diff, test results, pyflakes output, metrics
  2. Ask Claude to audit and suggest fixes
  3. Apply safe auto-fixes, bounded by a path allow-list and a per-run
     change budget (see PROTECTED_PATH_PREFIXES / MAX_FILES_PER_RUN below)
  4. Run impact-aware tests for the changed files (falling back to the
     full suite when no targeted test can be identified — unknown impact
     always broadens verification, it never skips it); if all pass,
     commit only the exact files this run touched; if not, restore the
     exact pre-fix content of exactly those files (never `git checkout --
     .`, which would also discard any unrelated uncommitted work sitting
     in the tree)
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
import re
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

# ─── Autonomous-mutation safety policy ────────────────────────────────────────
# A path is REJECTED if it starts with any of these (relative to REPO_ROOT),
# or contains any of the substrings below, regardless of case. Deterministic,
# no LLM/network involved -- this check runs before a single byte is written.
# Mirrors the "Requires human approval" / "Never autonomously" boundaries this
# repo's own CLAUDE.md already states for schema, auth, and CI changes.
PROTECTED_PATH_PREFIXES: tuple[str, ...] = (
    "backend/migrations/",
    "backend/app/security/",
    "backend/app/config.py",
    "backend/app/models/audit_log.py",
    "backend/app/services/audit_service.py",
    ".github/workflows/",
    "cloudflare/",
    "terraform/",
    "k8s/",
    "digitalocean/",
)
PROTECTED_PATH_SUBSTRINGS: tuple[str, ...] = (
    "secret", "credential", "password", ".env", "private_key", "id_rsa",
)

# Per-run bounds. Deliberately small and conservative: this agent is meant
# to apply narrow, mechanical corrections (a lint fix, a one-line contract
# repair), never a multi-file change -- if a genuine fix needs more than
# this, it needs a human, not a wider budget.
MAX_FILES_PER_RUN = 5
MAX_CHARS_CHANGED_PER_FILE = 400


def _is_protected_path(repo_relative_path: str) -> bool:
    """`repo_relative_path` must already be relative to REPO_ROOT (not
    BACKEND_DIR) -- fixes are declared relative to BACKEND_DIR, so
    callers should check this against the RESOLVED path (see
    `_resolve_target_path`), never the raw fix['file'] string, which may
    be missing the leading 'backend/' the prefixes below assume."""
    normalized = repo_relative_path.replace("\\", "/").lstrip("/")
    if normalized.startswith(PROTECTED_PATH_PREFIXES):
        return True
    lowered = normalized.lower()
    return any(s in lowered for s in PROTECTED_PATH_SUBSTRINGS)


def _resolve_target_path(rel_path: str) -> Path | None:
    """Resolves a fix's declared path (relative to BACKEND_DIR, per this
    file's existing convention) to an absolute Path strictly inside
    REPO_ROOT, or None if it's protected, escapes the repo (path
    traversal), or doesn't exist. Every autonomous write goes through
    this single choke point, and the protected-path check runs against
    the RESOLVED path relative to REPO_ROOT -- never the raw input
    string -- so it applies correctly regardless of which base
    (BACKEND_DIR or REPO_ROOT) the fix actually resolves against."""
    if not rel_path or rel_path.startswith("/"):
        return None
    repo_root = REPO_ROOT.resolve()
    for base in (BACKEND_DIR, REPO_ROOT):
        candidate = (base / rel_path).resolve()
        try:
            candidate_rel = candidate.relative_to(repo_root)
        except ValueError:
            continue  # escapes the repo -- never follow it
        if _is_protected_path(str(candidate_rel)):
            return None
        if candidate.exists():
            return candidate
    return None


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


@dataclass
class ApplyResult:
    applied:   list[str] = field(default_factory=list)
    rejected:  list[str] = field(default_factory=list)   # human-readable reasons
    snapshots: dict[Path, str] = field(default_factory=dict)  # for exact rollback


def _apply_auto_fixes(fixes: list[dict]) -> ApplyResult:
    """Applies auto-fixable patches, bounded by the path allow-list and the
    per-run change budget. Every accepted fix's pre-change content is
    captured in `snapshots` before it is written, so a verification
    failure can restore exactly those files (see `_rollback_exact`) --
    nothing else in the working tree is ever touched by that rollback."""
    result = ApplyResult()
    for fix in fixes:
        rel_path = fix.get("file", "")
        search   = fix.get("search", "")
        replace  = fix.get("replace", "")
        reason   = fix.get("reason", "")

        if len(result.applied) >= MAX_FILES_PER_RUN:
            result.rejected.append(f"{rel_path}: budget exceeded (MAX_FILES_PER_RUN={MAX_FILES_PER_RUN})")
            continue

        if not all([rel_path, search, replace]):
            result.rejected.append(f"{rel_path}: missing file/search/replace")
            continue

        if abs(len(replace) - len(search)) > MAX_CHARS_CHANGED_PER_FILE:
            result.rejected.append(f"{rel_path}: change exceeds MAX_CHARS_CHANGED_PER_FILE={MAX_CHARS_CHANGED_PER_FILE}")
            continue

        target = _resolve_target_path(rel_path)
        if target is None:
            # _resolve_target_path folds "protected", "path traversal", and
            # "doesn't exist" into one None -- re-derive which one for a
            # readable reason without duplicating its resolution logic.
            probe = (BACKEND_DIR / rel_path).resolve()
            try:
                probe_rel = str(probe.relative_to(REPO_ROOT.resolve()))
            except ValueError:
                probe_rel = rel_path
            if _is_protected_path(probe_rel):
                result.rejected.append(f"{rel_path}: protected path, autonomous mutation forbidden")
            else:
                result.rejected.append(f"{rel_path}: does not resolve to an existing in-repo file")
            continue

        content = target.read_text()
        if search not in content:
            result.rejected.append(f"{rel_path}: search text not found (stale fix)")
            continue

        result.snapshots[target] = content  # snapshot BEFORE mutating
        new_content = content.replace(search, replace, 1)
        target.write_text(new_content)
        result.applied.append(f"{rel_path}: {reason}")

    return result


def _rollback_exact(snapshots: dict[Path, str]) -> None:
    """Restores exactly the files this run snapshotted, to exactly their
    pre-fix content. No git command is used and no other path is ever
    touched -- unrelated uncommitted work elsewhere in the tree, or
    another agent's concurrent changes, survive untouched."""
    for path, original_content in snapshots.items():
        path.write_text(original_content)


def _module_dotted_path(path: Path) -> str | None:
    """Converts an absolute backend/app/... path to its dotted import form
    (e.g. backend/app/core/hybrid_router.py -> app.core.hybrid_router), or
    None if it isn't under backend/app at all."""
    try:
        rel = path.relative_to(BACKEND_DIR / "app")
    except ValueError:
        return None
    parts = ("app", *rel.with_suffix("").parts)
    return ".".join(parts)


def _tests_importing(dotted: str) -> list[str]:
    """Reverse-dependency search: every backend/tests/**/*.py file that
    actually imports the given dotted module path (exact module, or a
    package it lives in via `from app.core import hybrid_router` /
    `import app.core.hybrid_router`). Deterministic (plain text search,
    no execution) -- used as a second, narrower tier between an exact
    test_<stem>.py match and the full-suite fallback."""
    escaped = re.escape(dotted)
    _, out = _run(
        ["grep", "-rlE", rf"(from {escaped}(\.| )|from {escaped} import|import {escaped}\b)",
         "--include=*.py", "tests"],
        cwd=BACKEND_DIR,
    )
    if not out:
        return []
    return sorted(p for p in out.splitlines() if p)


def _select_impact_aware_tests(applied_paths: list[Path]) -> tuple[list[str], str]:
    """Maps changed backend/app files to the narrowest test set the
    evidence supports. Returns (test_args, confidence):

    - "TARGETED"      -- every changed path has an exact test_<stem>.py.
    - "IMPORT_MATCHED" -- no exact-name match for at least one path, but
      every changed path is imported by at least one identifiable test
      file (reverse-dependency search) -- still a deterministic, narrower
      set than the full suite, just not the naming-convention shortcut.
    - "UNKNOWN"       -- at least one changed path has no identifiable
      test by either method -- caller must broaden verification, never
      skip it.
    """
    targeted: list[str] = []
    import_matched: set[str] = set()
    for path in applied_paths:
        try:
            rel = path.relative_to(BACKEND_DIR / "app")
        except ValueError:
            return [], "UNKNOWN"  # changed a file outside backend/app -- can't map it
        candidate = BACKEND_DIR / "tests" / f"test_{rel.stem}.py"
        if candidate.exists():
            targeted.append(str(candidate.relative_to(BACKEND_DIR)))
            continue
        dotted = _module_dotted_path(path)
        matches = _tests_importing(dotted) if dotted else []
        if not matches:
            return [], "UNKNOWN"
        import_matched.update(matches)

    if import_matched:
        # Mixed exact-match + import-match paths both resolved to *some*
        # concrete test set -- run the union, but report the weaker tier
        # honestly rather than claiming TARGETED for the whole batch.
        return sorted(set(targeted) | import_matched), "IMPORT_MATCHED"
    return sorted(set(targeted)), "TARGETED"


def _verify_after_fix(applied_paths: list[Path]) -> tuple[bool, str]:
    """Syntax-checks every actually-changed file (never a fixed stand-in
    like app/main.py -- a changed file that nothing imports would
    otherwise never have its own syntax checked at all), then runs the
    narrowest test set the evidence supports. TARGETED/IMPORT_MATCHED run
    only the tests mapped to the changed files; UNKNOWN (no mapping found
    for at least one changed file, by either method) broadens to the full
    suite rather than guessing -- unknown impact is never treated as "safe
    to skip", and the full-suite fallback itself is never removed."""
    for path in applied_paths:
        rc, _out = _run(["python", "-m", "py_compile", str(path)], cwd=BACKEND_DIR)
        if rc != 0:
            return False, "syntax_check_failed"

    test_args, confidence = _select_impact_aware_tests(applied_paths)
    if confidence in ("TARGETED", "IMPORT_MATCHED"):
        rc, _out = _run(["python", "-m", "pytest", *test_args, "-q", "--tb=short"], cwd=BACKEND_DIR, timeout=120)
        return rc == 0, confidence

    rc, _out = _run(["python", "-m", "pytest", "tests/", "-q", "--tb=short"], cwd=BACKEND_DIR, timeout=300)
    return rc == 0, "UNKNOWN_broadened_to_full_suite"


def _commit_fixes(applied: list[str], applied_paths: list[Path]) -> bool:
    """Stage and commit ONLY the files this run touched -- never `git add
    -A`, which would also stage any unrelated uncommitted work sitting in
    the tree at the time this runs."""
    if not applied or not applied_paths:
        return False
    _run(["git", "add", "--", *[str(p) for p in applied_paths]])
    msg = "fix: self-audit agent auto-fixes\n\n" + "\n".join(f"- {a}" for a in applied)
    msg += "\n\nhttps://claude.ai/code/session_019jkuFtbcJ1mDeZqhAUT69x"
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
        """Prints the audit result to stdout. Was previously dead code --
        computed a color per grade and discarded it, then iterated every
        issue/fix list with a bare `pass`, so a real, API-billed audit run
        produced zero console output (the JSON report file in logs/ was
        the only surviving evidence). Restored to actually print, using
        the exact color mapping the method already (uselessly) computed.
        """
        reset = "\033[0m"
        color = {"GREEN": "\033[32m", "YELLOW": "\033[33m", "RED": "\033[31m"}.get(self.grade, "")
        print(f"\n{color}[{self.grade}]{reset} {self.timestamp} — production_ready={self.production_ready}")
        if self.summary:
            print(f"  {self.summary}")

        for severity, issues in [
            ("CRITICAL", self.critical_issues),
            ("HIGH", self.high_issues),
            ("MEDIUM", self.medium_issues),
        ]:
            if issues:
                print(f"\n{severity} ({len(issues)}):")
                for i in issues:
                    loc = f"{i.get('file', '?')}:{i.get('line', '?')}"
                    print(f"  - {loc}: {i.get('issue', '')}")
                    if i.get("fix"):
                        print(f"    fix: {i['fix']}")

        if self.applied_fixes:
            print(f"\nAuto-applied fixes ({len(self.applied_fixes)}):")
            for f in self.applied_fixes:
                print(f"  - {f}")



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
        apply_result = _apply_auto_fixes(result.auto_fixable)
        if apply_result.rejected:
            result.summary += "\n\nRejected by mutation policy:\n" + "\n".join(f"- {r}" for r in apply_result.rejected)
        if apply_result.applied:
            applied_paths = list(apply_result.snapshots.keys())
            verified, confidence = _verify_after_fix(applied_paths)
            if verified:
                _commit_fixes(apply_result.applied, applied_paths)
                result.applied_fixes = [f"{a} [{confidence}]" for a in apply_result.applied]
            else:
                _rollback_exact(apply_result.snapshots)
                result.summary += f"\n\nVerification failed ({confidence}) — exact rollback applied to {len(apply_result.snapshots)} file(s)."

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
