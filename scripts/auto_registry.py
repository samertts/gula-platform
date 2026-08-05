#!/usr/bin/env python3
"""
PROGRAM-AUTOMATION-001: Auto Registry Updater

Automatically updates:
- Registry (REGISTRY.md)
- Search Index (SEARCH_INDEX.md)
- Knowledge Graph (graph/README.md)
- Artifact Counters

Triggered when:
- Skill, Playbook, Runbook, Capability, Decision, Failure, KUP, RFC is added
- Any artifact with a valid ID is detected

Usage:
    python scripts/auto_registry.py                    # Scan and update all
    python scripts/auto_registry.py --dry-run          # Preview without changes
    python scripts/auto_registry.py --type skill       # Update specific type
    python scripts/auto_registry.py --status           # Show registry status
"""

import argparse
import re
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_CORE = REPO_ROOT / ".ai" / "core"
REGISTRY = AI_CORE / "registry" / "REGISTRY.md"
GRAPH = AI_CORE / "graph" / "README.md"
SEARCH_INDEX = AI_CORE / "index" / "SEARCH_INDEX.md"
INDEX = AI_CORE / "index" / "INDEX.md"

ID_PATTERNS = {
    "skill": (r"SKILL-\d{6}", "skills"),
    "playbook": (r"PLAYBOOK-\d{6}", "playbooks"),
    "runbook": (r"RUNBOOK-\d{6}", "runbooks"),
    "kup": (r"KUP-\d{6}", "kup"),
    "cap": (r"CAP-\d{6}", "capabilities"),
    "dec": (r"DEC-\d{6}", "decisions"),
    "failure": (r"FAILURE-\d{6}", "failures"),
    "debt": (r"DEBT-\d{6}", "quality"),
    "checklist": (r"CHECKLIST-\d{6}", "checklists"),
    "know": (r"KNOW-\d{6}", "memory"),
    "report": (r"REPORT-\d{6}", "reports"),
    "const": (r"CONST-\d{6}", "constitution"),
    "policy": (r"POLICY-\d{6}", "policies"),
    "plugin": (r"PLUGIN-\d{6}", "sdk"),
    "cat": (r"CAT-\d{6}", "marketplace"),
    "mem": (r"MEM-\d{6}", "memory"),
    "evt": (r"EVT-\d{6}", "events"),
    "wf": (r"WF-\d{6}", "workflows"),
}


def scan_artifacts():
    """Scan all .md files for registered artifacts."""
    artifacts = {}
    for md_file in AI_CORE.rglob("*.md"):
        try:
            content = md_file.read_text("utf-8")
        except Exception:
            continue
        rel = str(md_file.relative_to(REPO_ROOT))
        for name, (pat, cat) in ID_PATTERNS.items():
            for match in re.findall(pat, content):
                if match not in artifacts:
                    artifacts[match] = {
                        "id": match,
                        "type": name,
                        "category": cat,
                        "files": [],
                        "first_seen": datetime.now().isoformat(),
                    }
                artifacts[match]["files"].append(rel)
    return artifacts


def get_artifact_counts():
    """Count artifacts by type."""
    artifacts = scan_artifacts()
    counts = {}
    for art in artifacts.values():
        t = art["type"]
        counts[t] = counts.get(t, 0) + 1
    return counts


def update_registry_status():
    """Show current registry status."""
    counts = get_artifact_counts()
    total = sum(counts.values())

    print("Registry Status")
    print("=" * 40)
    for art_type, count in sorted(counts.items()):
        print(f"  {art_type:12s}: {count}")
    print(f"  {'TOTAL':12s}: {total}")
    print("=" * 40)

    if REGISTRY.exists():
        content = REGISTRY.read_text("utf-8")
        ver = re.search(r"Version:\s*(\S+)", content)
        if ver:
            print(f"  Version: {ver.group(1)}")
        updated = re.search(r"Last Verified:\s*(.+)", content)
        if updated:
            print(f"  Last Verified: {updated.group(1).strip()}")


def generate_registry_update(artifacts, dry_run=False):
    """Generate updated registry content."""
    if not REGISTRY.exists():
        print("[WARN] REGISTRY.md not found, skipping update")
        return

    content = REGISTRY.read_text("utf-8")
    counts = {}
    for art in artifacts.values():
        t = art["type"]
        counts[t] = counts.get(t, 0) + 1

    total = sum(counts.values())

    # Update the total count line
    new_content = re.sub(
        r"\|\s*\*\*Total Artifacts\*\*\s*\|\s*\d+\s*\|",
        f"| **Total Artifacts** | {total} |",
        content,
    )

    # Add Technical Debt section if missing
    if "Technical Debt" not in new_content and counts.get("debt", 0) > 0:
        new_content = new_content.rstrip() + "\n\n## Technical Debt\n\n| ID | Description | Status |\n|---|---|---|\n"
        for art_id, art in artifacts.items():
            if art["type"] == "debt":
                new_content += f"| {art_id} | Auto-tracked | Open |\n"

    if dry_run:
        print("[DRY RUN] Would update REGISTRY.md")
        print(f"  New total: {total} artifacts")
        for t, c in sorted(counts.items()):
            print(f"  {t}: {c}")
    else:
        REGISTRY.write_text(new_content, encoding="utf-8")
        print(f"[OK] Registry updated: {total} artifacts")


def generate_graph_update(dry_run=False):
    """Update graph with current artifact relationships."""
    if not GRAPH.exists():
        print("[WARN] Graph README not found, skipping")
        return

    content = GRAPH.read_text("utf-8")

    # Add auto-registry relationship if missing
    if "auto_registry" not in content:
        new_edge = "| .ai/core/registry/ | .ai/core/skills/ | Auto-updates |\n"
        new_edge += "| .ai/core/registry/ | .ai/core/playbooks/ | Auto-updates |\n"
        new_edge += "| .ai/core/registry/ | .ai/core/runbooks/ | Auto-updates |\n"

        # Insert before the status line
        content = content.replace(
            "---\n\n**Status:",
            new_edge + "\n---\n\n**Status:",
        )

        if dry_run:
            print("[DRY RUN] Would add auto-registry edges to graph")
        else:
            GRAPH.write_text(content, encoding="utf-8")
            print("[OK] Graph updated with auto-registry edges")


def main():
    parser = argparse.ArgumentParser(description="Auto Registry Updater")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changes")
    parser.add_argument("--status", action="store_true", help="Show registry status")
    parser.add_argument("--type", type=str, help="Update specific type only")
    args = parser.parse_args()

    if args.status:
        update_registry_status()
        return

    print("Scanning artifacts...")
    artifacts = scan_artifacts()
    print(f"Found {len(artifacts)} artifacts")

    update_registry_status()
    generate_registry_update(artifacts, dry_run=args.dry_run)
    generate_graph_update(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
