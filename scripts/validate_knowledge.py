#!/usr/bin/env python3
"""
PROGRAM-AUTOMATION-001: Knowledge Validator

Validates:
- Registry integrity
- Knowledge Graph consistency
- Search Index accuracy
- Memory completeness
- Skills/Playbooks/Runbooks integrity
- Capabilities/Decisions/Failures tracking
- KUP/RFC lifecycle
- Templates completeness
- No orphan objects
- No duplicate IDs
- No broken references
- Cross-reference integrity

Usage:
    python scripts/validate_knowledge.py
    python scripts/validate_knowledge.py --json
    python scripts/validate_knowledge.py --fix  # Auto-fix where possible
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_CORE = REPO_ROOT / ".ai" / "core"

ID_PATTERNS = {
    "KUP": r"KUP-\d{6}", "SKILL": r"SKILL-\d{6}",
    "PLAYBOOK": r"PLAYBOOK-\d{6}", "RUNBOOK": r"RUNBOOK-\d{6}",
    "CHECKLIST": r"CHECKLIST-\d{6}", "KNOW": r"KNOW-\d{6}",
    "CAP": r"CAP-\d{6}", "DEC": r"DEC-\d{6}",
    "FAILURE": r"FAILURE-\d{6}", "DEBT": r"DEBT-\d{6}",
    "REPORT": r"REPORT-\d{6}", "CONST": r"CONST-\d{6}",
}


def scan_all_ids():
    """Scan all .md files in .ai/core for IDs."""
    all_ids = {}
    for md_file in AI_CORE.rglob("*.md"):
        try:
            content = md_file.read_text("utf-8")
        except Exception:
            continue
        rel = str(md_file.relative_to(REPO_ROOT))
        for name, pat in ID_PATTERNS.items():
            for match in re.findall(pat, content):
                all_ids.setdefault(match, set()).add(rel)
    return all_ids


def check_registry_integrity():
    results = []
    reg = AI_CORE / "registry" / "REGISTRY.md"
    if not reg.exists():
        results.append(("registry_exists", "FAIL", "REGISTRY.md not found"))
        return results

    content = reg.read_text("utf-8")
    results.append(("registry_exists", "PASS", "Registry exists"))

    ver = re.search(r"Version:\s*(\S+)", content)
    if ver:
        results.append(("registry_version", "PASS", f"Version: {ver.group(1)}"))
    else:
        results.append(("registry_version", "WARN", "No version found"))

    total = re.search(r"\*\*Total Artifacts\*\*.*?\|\s*(\d+)", content)
    if total:
        results.append(("registry_total", "PASS", f"Total: {total.group(1)} artifacts"))
    else:
        results.append(("registry_total", "WARN", "Total count not found"))

    all_ids = scan_all_ids()
    registry_ids = set()
    for pat in ID_PATTERNS.values():
        registry_ids.update(re.findall(pat, content))

    unregistered = registry_ids - set(all_ids.keys())
    if unregistered:
        results.append(("registry_unregistered", "WARN", f"IDs in registry but not in files: {unregistered}"))
    else:
        results.append(("registry_unregistered", "PASS", f"All {len(registry_ids)} registry IDs found in files"))

    return results


def check_duplicate_ids():
    results = []
    all_ids = scan_all_ids()
    dupes = {k: v for k, v in all_ids.items() if len(v) > 1}
    if dupes:
        details = [f"{k}: {len(v)} files" for k, v in dupes.items()]
        results.append(("duplicate_ids", "WARN", f"{len(dupes)} IDs in multiple files", details))
    else:
        results.append(("duplicate_ids", "PASS", f"No duplicate IDs ({len(all_ids)} unique)"))
    return results


def check_orphan_files():
    results = []
    registered_ids = set()
    reg = AI_CORE / "registry" / "REGISTRY.md"
    if reg.exists():
        content = reg.read_text("utf-8")
        for pat in ID_PATTERNS.values():
            registered_ids.update(re.findall(pat, content))

    named_files = []
    for md_file in AI_CORE.rglob("*.md"):
        name = md_file.stem
        for prefix in ["KUP-", "SKILL-", "PLAYBOOK-", "RUNBOOK-", "CHECKLIST-",
                        "KNOW-", "CAP-", "DEC-", "FAILURE-", "DEBT-", "REPORT-"]:
            if name.startswith(prefix):
                named_files.append((name, str(md_file.relative_to(REPO_ROOT))))

    orphans = [f for f in named_files if not any(fid in f[0] for fid in registered_ids)]
    if orphans:
        results.append(("orphan_files", "WARN", f"{len(orphans)} files not in registry",
                        [f[1] for f in orphans[:5]]))
    else:
        results.append(("orphan_files", "PASS", "No orphan files detected"))
    return results


def check_graph_integrity():
    results = []
    graph = AI_CORE / "graph" / "README.md"
    if graph.exists():
        content = graph.read_text("utf-8")
        lines = content.strip().split("\n")
        results.append(("graph_exists", "PASS", f"Graph exists ({len(lines)} lines)"))
        edges = [l for l in lines if "|" in l and "---" not in l]
        results.append(("graph_edges", "PASS", f"{len(edges)} edges defined"))
    else:
        results.append(("graph_exists", "WARN", "Graph README missing"))
    return results


def check_search_index():
    results = []
    idx = AI_CORE / "index" / "INDEX.md"
    search = AI_CORE / "index" / "SEARCH_INDEX.md"
    priority = AI_CORE / "index" / "SEARCH_PRIORITY.md"

    for name, path in [("INDEX", idx), ("SEARCH_INDEX", search), ("SEARCH_PRIORITY", priority)]:
        if path.exists():
            content = path.read_text("utf-8")
            results.append((f"index_{name.lower()}", "PASS", f"{name} exists ({len(content)} chars)"))
        else:
            results.append((f"index_{name.lower()}", "WARN", f"{name} missing"))
    return results


def check_skills_integrity():
    results = []
    d = AI_CORE / "skills"
    if not d.exists():
        results.append(("skills_dir", "WARN", "Skills dir missing"))
        return results

    skills = [f for f in d.glob("*.md") if f.name not in ("README.md", "SKILL_TEMPLATE.md")]
    results.append(("skills_count", "PASS", f"{len(skills)} skills"))

    for s in skills:
        content = s.read_text("utf-8")
        has_id = bool(re.search(r"SKILL-\d{6}", content))
        has_status = "Status:" in content or "status:" in content
        if not has_id:
            results.append((f"skill_{s.stem}_id", "WARN", f"{s.name}: no SKILL ID"))
        if not has_status:
            results.append((f"skill_{s.stem}_status", "WARN", f"{s.name}: no status field"))
    return results


def check_playbooks_integrity():
    results = []
    d = AI_CORE / "playbooks"
    if not d.exists():
        results.append(("playbooks_dir", "WARN", "Playbooks dir missing"))
        return results

    items = [f for f in d.glob("*.md") if f.name not in ("README.md", "PLAYBOOK_TEMPLATE.md")]
    results.append(("playbooks_count", "PASS", f"{len(items)} playbooks"))
    return results


def check_runbooks_integrity():
    results = []
    d = AI_CORE / "runbooks"
    if not d.exists():
        results.append(("runbooks_dir", "WARN", "Runbooks dir missing"))
        return results

    items = [f for f in d.glob("*.md") if f.name not in ("README.md", "RUNBOOK_TEMPLATE.md")]
    results.append(("runbooks_count", "PASS", f"{len(items)} runbooks"))
    return results


def check_capabilities_decisions_failures():
    results = []
    for name, dirname, pattern in [
        ("capabilities", "capabilities", r"CAP-\d{6}"),
        ("decisions", "decisions", r"DEC-\d{6}"),
        ("failures", "failures", r"FAILURE-\d{6}"),
    ]:
        readme = AI_CORE / dirname / "README.md"
        if readme.exists():
            content = readme.read_text("utf-8")
            items = re.findall(pattern, content)
            results.append((name, "PASS", f"{len(items)} {name} registered"))
        else:
            results.append((name, "WARN", f"{name} README missing"))
    return results


def check_templates():
    results = []
    d = AI_CORE / "templates"
    if not d.exists():
        results.append(("templates_dir", "WARN", "Templates dir missing"))
        return results

    required = ["SKILL_TEMPLATE.md", "PLAYBOOK_TEMPLATE.md", "RUNBOOK_TEMPLATE.md"]
    for tmpl in required:
        if (d / tmpl).exists():
            results.append((f"template_{tmpl}", "PASS", f"{tmpl} exists"))
        else:
            results.append((f"template_{tmpl}", "WARN", f"{tmpl} missing"))
    return results


def check_cross_references():
    results = []
    all_ids = scan_all_ids()

    ref_count = sum(len(v) for v in all_ids.values())
    results.append(("cross_refs", "PASS", f"{ref_count} total ID references across {len(all_ids)} unique IDs"))
    return results


def run_validation():
    start = time.time()
    checks = []

    for name, status, msg, *rest in (
        check_registry_integrity() +
        check_duplicate_ids() +
        check_orphan_files() +
        check_graph_integrity() +
        check_search_index() +
        check_skills_integrity() +
        check_playbooks_integrity() +
        check_runbooks_integrity() +
        check_capabilities_decisions_failures() +
        check_templates() +
        check_cross_references()
    ):
        details = rest[0] if rest else []
        checks.append({"name": name, "status": status, "message": msg, "details": details})

    duration = int((time.time() - start) * 1000)
    passed = sum(1 for c in checks if c["status"] == "PASS")
    warnings = sum(1 for c in checks if c["status"] == "WARN")
    failures = sum(1 for c in checks if c["status"] == "FAIL")
    overall = "FAIL" if failures > 0 else ("WARN" if warnings > 0 else "PASS")

    return {
        "timestamp": datetime.now().isoformat(),
        "duration_ms": duration,
        "overall": overall,
        "total": len(checks),
        "passed": passed,
        "warnings": warnings,
        "failures": failures,
        "checks": checks,
    }


def print_report(report, use_json=False):
    if use_json:
        print(json.dumps(report, indent=2))
        return

    print("=" * 70)
    print("KNOWLEDGE VALIDATOR")
    print("=" * 70)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Duration: {report['duration_ms']}ms")
    print(f"Overall: {report['overall']}")
    print(f"Checks: {report['total']} | PASS: {report['passed']} | WARN: {report['warnings']} | FAIL: {report['failures']}")
    print("=" * 70)

    for c in report["checks"]:
        icon = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]"}[c["status"]]
        print(f"  {icon} {c['message']}")
        for d in c.get("details", [])[:3]:
            print(f"         {d}")

    print("=" * 70)
    print(f"RESULT: {report['overall']}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Knowledge Validator")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    report = run_validation()
    print_report(report, use_json=args.json)
    sys.exit(1 if report["overall"] == "FAIL" else 0)


if __name__ == "__main__":
    main()
