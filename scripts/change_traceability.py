#!/usr/bin/env python3
"""PROGRAM-AUTOMATION-001: Change Traceability System

Every modification must generate a trace record with:
- Reason, Evidence, Affected Files, Affected Knowledge
- Affected Registry, Affected Graph, Rollback, Verification
- Related RFC, KUP, ADR, Decision, Timestamp, Author

Nothing may change silently.

Usage:
    python scripts/change_traceability.py                          # Review last commit
    python scripts/change_traceability.py --git-diff               # Review uncommitted changes
    python scripts/change_traceability.py --show 1234567           # Show trace for commit
"""
import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRACE_LOG = REPO_ROOT / ".ai" / "core" / "traceability" / "CHANGE_LOG.md"

def run_git(args):
    try:
        r = subprocess.run(["git"] + args, capture_output=True, text=True, cwd=REPO_ROOT, timeout=10)
        return r.stdout.strip()
    except Exception:
        return ""

def get_author():
    return run_git(["config", "user.name"]) or "unknown"

def get_last_commit():
    return run_git(["log", "-1", "--format=%H %an %ai %s"])

def get_commit_files(commit_hash="HEAD~1..HEAD"):
    out = run_git(["diff", "--name-only", *commit_hash.split()])
    return out.split("\n") if out else []

def classify_file(path):
    if path.startswith("backend/"): return "backend"
    if path.startswith("frontend"): return "frontend"
    if path.startswith("docs/"): return "docs"
    if path.startswith("scripts/"): return "scripts"
    if path.startswith(".ai/"): return "knowledge"
    if path.startswith(".github/"): return "ci"
    return "other"

def check_knowledge_impact(files):
    impact = []
    for f in files:
        cat = classify_file(f)
        if cat == "backend": impact.append(f"Backend change: {f} - may need API docs update")
        elif cat == "frontend": impact.append(f"Frontend change: {f} - may need UI docs update")
        elif cat == "scripts": impact.append(f"Script change: {f} - may need runbook update")
        elif cat == "knowledge": impact.append(f"Knowledge change: {f} - registry may need update")
    return impact

def check_required_traceability(files):
    """Check if change has complete traceability."""
    results = []
    has_rollback = any("rollback" in f.lower() or "revert" in f.lower() for f in files)
    results.append(("rollback_plan", has_rollback, "Rollback/rollback plan in change" if has_rollback else "No rollback plan found - manual review needed"))
    return results

def generate_trace(files, author, commit_info=""):
    trace = {
        "timestamp": datetime.now().isoformat(),
        "author": author,
        "commit": commit_info,
        "files": files,
        "file_count": len(files),
        "affected_areas": {},
        "knowledge_impact": check_knowledge_impact(files),
        "related_kup": None,
        "related_rfc": None,
        "related_adr": None,
        "rollback": "git revert <commit> or git checkout <path>",
        "verification": "Run: python3 scripts/gula_ai_doctor.py",
    }
    for f in files:
        cat = classify_file(f)
        trace["affected_areas"].setdefault(cat, []).append(f)
    return trace

def append_log(trace):
    if not TRACE_LOG.parent.exists():
        TRACE_LOG.parent.mkdir(parents=True, exist_ok=True)

    header = "# GULA Change Traceability Log\n\n"
    if not TRACE_LOG.exists():
        TRACE_LOG.write_text(header, encoding="utf-8")

    content = TRACE_LOG.read_text("utf-8")
    entry = (
        f"## Trace {trace['timestamp']}\n"
        f"- Author: {trace['author']}\n"
        f"- Commit: {trace['commit']}\n"
        f"- Files: {trace['file_count']}\n"
        f"- Areas: {', '.join(f'{k}:{len(v)}' for k, v in trace['affected_areas'].items())}\n"
        f"- Rollback: {trace['rollback']}\n"
        f"- Verification: {trace['verification']}\n\n"
    )
    TRACE_LOG.write_text(header + entry + content, encoding="utf-8")
    return TRACE_LOG

def main():
    parser = argparse.ArgumentParser(description="Change Traceability")
    parser.add_argument("--git-diff", action="store_true", help="Review uncommitted changes")
    parser.add_argument("--show", type=str, help="Show trace for commit range (default HEAD~1..HEAD)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    author = get_author()

    if args.git_diff:
        files = run_git(["diff", "--name-only"]).split("\n")
        files = [f for f in files if f]
        commit_info = "UNCOMMITTED CHANGES"
    elif args.show:
        files = get_commit_files(args.show)
        commit_info = run_git(["log", "-1", "--format=%H %an %ai %s"]) if args.show == "HEAD" else args.show
    else:
        files = get_commit_files()
        commit_info = get_last_commit()

    files = [f for f in files if f]
    trace = generate_trace(files, author, commit_info)

    if args.json:
        print(json.dumps(trace, indent=2))
    else:
        print("=" * 60)
        print("CHANGE TRACEABILITY")
        print("=" * 60)
        print(f"Timestamp: {trace['timestamp']}")
        print(f"Author: {trace['author']}")
        print(f"Commit: {trace['commit']}")
        print(f"Files: {trace['file_count']}")
        print("\nAffected Areas:")
        for area, fs in trace["affected_areas"].items():
            print(f"  {area}: {len(fs)} files")
        print("\nKnowledge Impact:")
        for impact in trace["knowledge_impact"]:
            print(f"  - {impact}")
        print(f"\nRollback: {trace['rollback']}")
        print(f"Verification: {trace['verification']}")
        print("\n" + "=" * 60)
        print("Nothing may change silently. Log this trace.")
        print("=" * 60)

    log = append_log(trace)
    print(f"\n[OK] Trace appended to {log}")

if __name__ == "__main__":
    main()
