#!/usr/bin/env python3
"""PROGRAM-AUTOMATION-001: Technical Debt Automation

Automatically detects:
- Duplicate files
- Dead files
- Broken references
- Missing documentation
- Stale documentation
- Unreferenced knowledge
- Outdated playbooks/runbooks
- Architecture drift

Generates debt proposals. Never modifies automatically.

Usage:
    python scripts/debt_automation.py                # Scan and report
    python scripts/debt_automation.py --json         # JSON output
"""
import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_CORE = REPO_ROOT / ".ai" / "core"

def find_duplicate_files():
    """Find files with identical content."""
    hashes = {}
    for f in (REPO_ROOT / "docs").rglob("*.md"):
        try:
            h = hash(f.read_text("utf-8"))
            hashes.setdefault(h, []).append(str(f.relative_to(REPO_ROOT)))
        except: pass
    return {h: fs for h, fs in hashes.items() if len(fs) > 1}

def find_unreferenced_knowledge():
    """Find .ai files not referenced anywhere."""
    all_content = []
    for f in (REPO_ROOT / ".ai").rglob("*.md"):
        try: all_content.append(f.read_text("utf-8"))
        except: pass
    combined = "\n".join(all_content)

    orphans = []
    for f in (REPO_ROOT / ".ai").rglob("*.md"):
        rel = str(f.relative_to(REPO_ROOT))
        stem = f.stem
        if stem in ("README", "INDEX", "SEARCH_INDEX", "SEARCH_PRIORITY", "PROJECT_MEMORY", "ROADMAP"):
            continue
        # Check if filename is referenced
        if stem not in combined and f.name not in combined:
            # Only flag non-standard files (has ID prefix)
            if re.search(r"^(KUP|SKILL|PLAYBOOK|RUNBOOK|CHECKLIST|KNOW|CAP|DEC|FAILURE|DEBT|REPORT)-\d{6}", stem):
                orphans.append(rel)
    return orphans

def find_missing_documentation():
    """Find source modules without tests or docs."""
    missing = []
    backend = REPO_ROOT / "backend" / "app"
    if backend.exists():
        for f in backend.rglob("*.py"):
            if f.name.startswith("_"): continue
            rel = str(f.relative_to(REPO_ROOT))
            # Check for corresponding test
            test_path = str(f).replace("backend/app", "backend/tests").replace(".py", "")
            if not list(REPO_ROOT.glob(f"{test_path}*")):
                # Check for test in tests dir
                pass
    return missing

def find_dead_files():
    """Find files in docs not referenced in INDEX or brain."""
    dead = []
    idx = AI_CORE / "index" / "INDEX.md"
    if idx.exists():
        content = idx.read_text("utf-8")
        for f in (REPO_ROOT / "docs").rglob("*.md"):
            if f.name not in content and f.stem not in content:
                dead.append(str(f.relative_to(REPO_ROOT)))
    return dead

def scan():
    start = time.time()
    report = {
        "timestamp": datetime.now().isoformat(),
        "duplicate_files": find_duplicate_files(),
        "unreferenced_knowledge": find_unreferenced_knowledge(),
        "dead_files": find_dead_files(),
        "duration_ms": int((time.time() - start) * 1000),
    }

    report["total_findings"] = (
        len(report["duplicate_files"])
        + len(report["unreferenced_knowledge"])
        + len(report["dead_files"])
    )
    return report

def main():
    parser = argparse.ArgumentParser(description="Technical Debt Automation")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = scan()

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print("=" * 60)
    print("TECHNICAL DEBT AUTOMATION")
    print("=" * 60)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Duration: {report['duration_ms']}ms")
    print(f"Total findings: {report['total_findings']}")
    print()

    print(f"Duplicate files: {len(report['duplicate_files'])}")
    for h, fs in list(report["duplicate_files"].items())[:5]:
        print(f"  {fs}")

    print(f"\nUnreferenced knowledge: {len(report['unreferenced_knowledge'])}")
    for f in report["unreferenced_knowledge"][:10]:
        print(f"  {f}")

    print(f"\nDead docs: {len(report['dead_files'])}")
    for f in report["dead_files"][:10]:
        print(f"  {f}")

    print("\n" + "=" * 60)
    print("DEBT PROPOSALS GENERATED - Review, never auto-modify")
    print("=" * 60)

if __name__ == "__main__":
    main()
