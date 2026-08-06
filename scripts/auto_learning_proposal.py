#!/usr/bin/env python3
"""PROGRAM-AUTOMATION-001: Auto Learning Proposal Generator

After every completed task, automatically prepare:
- Knowledge Update Proposal
- Suggested Skills, Playbooks, Runbooks
- Suggested Documentation
- Suggested ADR
- Suggested Memory Update

Never merges automatically. Always waits for approval.
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_CORE = REPO_ROOT / ".ai" / "core"

def scan_recent_changes():
    """Scan git for recently changed files."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=10
        )
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except Exception:
        return []

def classify_changes(files):
    """Classify changes by type."""
    result = {"backend": [], "frontend": [], "docs": [], "scripts": [], "ai": [], "config": [], "other": []}
    for f in files:
        if f.startswith("backend/"): result["backend"].append(f)
        elif f.startswith("frontend"): result["frontend"].append(f)
        elif f.startswith("docs/"): result["docs"].append(f)
        elif f.startswith("scripts/"): result["scripts"].append(f)
        elif f.startswith(".ai/"): result["ai"].append(f)
        else: result["other"].append(f)
    return result

def generate_proposals(changes):
    """Generate learning proposals based on changes."""
    proposals = []
    if changes["backend"]:
        proposals.append({
            "type": "skill", "priority": "MEDIUM",
            "title": "Backend change detected",
            "description": f"Backend files changed: {', '.join(changes['backend'][:3])}",
            "action": "Consider adding a skill if this is a reusable pattern"
        })
    if changes["frontend"]:
        proposals.append({
            "type": "playbook", "priority": "MEDIUM",
            "title": "Frontend change detected",
            "description": f"Frontend files changed: {', '.join(changes['frontend'][:3])}",
            "action": "Consider adding a playbook for frontend patterns"
        })
    if changes["docs"]:
        proposals.append({
            "type": "documentation", "priority": "LOW",
            "title": "Documentation updated",
            "description": f"Doc files changed: {', '.join(changes['docs'][:3])}",
            "action": "Verify documentation is current"
        })
    if changes["scripts"]:
        proposals.append({
            "type": "runbook", "priority": "MEDIUM",
            "title": "Script change detected",
            "description": f"Script files changed: {', '.join(changes['scripts'][:3])}",
            "action": "Consider updating runbooks if behavior changed"
        })
    return proposals

def main():
    parser = argparse.ArgumentParser(description="Auto Learning Proposal")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    files = scan_recent_changes()
    changes = classify_changes(files)
    proposals = generate_proposals(changes)

    report = {
        "timestamp": datetime.now().isoformat(),
        "files_changed": len(files),
        "changes": {k: v for k, v in changes.items() if v},
        "proposals": proposals,
        "action": "Review proposals. Never merge automatically. Always wait for approval."
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("=" * 60)
        print("AUTO LEARNING PROPOSAL")
        print("=" * 60)
        print(f"Files changed: {len(files)}")
        for cat, fs in changes.items():
            if fs: print(f"  {cat}: {len(fs)} files")
        print(f"\nProposals: {len(proposals)}")
        for p in proposals:
            print(f"\n  [{p['priority']}] {p['type'].upper()}: {p['title']}")
            print(f"  {p['description']}")
            print(f"  Action: {p['action']}")
        print("\n" + "=" * 60)
        print("REVIEW REQUIRED - Never merge automatically")
        print("=" * 60)

if __name__ == "__main__":
    main()
