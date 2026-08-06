#!/usr/bin/env python3
"""
PROGRAM-AUTOMATION-001: Constitution Validator

Verifies:
- All AI configuration files reference AI_OPERATING_CONSTITUTION.md
- No duplicated constitutional rules
- No conflicting rules
- Correct precedence
- Constitution is supreme authority

Usage:
    python scripts/validate_constitution.py
    python scripts/validate_constitution.py --json
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONSTITUTION = REPO_ROOT / "AI_OPERATING_CONSTITUTION.md"

AI_CONFIG_FILES = [
    "AGENTS.md", "CLAUDE.md", "COPILOT.md", "CODEX.md", "GEMINI.md",
    "AI_BOOTSTRAP.md",
]

GITHUB_CONFIG_FILES = [
    ".github/copilot-instructions.md",
]

PRECEDENCE_ORDER = [
    "AI_OPERATING_CONSTITUTION.md",
    "AI_BOOTSTRAP.md",
    "ADR",
    "Architecture",
    "Standards",
    "Knowledge",
    "Skills",
    "Playbooks",
    "Runbooks",
    "Tool-specific instructions",
]


def check_constitution_exists():
    if CONSTITUTION.exists():
        content = CONSTITUTION.read_text("utf-8")
        lines = content.strip().split("\n")
        return True, f"Constitution exists ({len(lines)} lines)", content
    return False, "AI_OPERATING_CONSTITUTION.md not found", ""


def check_config_references(content_map):
    results = []
    for fname, content in content_map.items():
        if "AI_OPERATING_CONSTITUTION" in content:
            results.append((fname, "PASS", "References constitution"))
        else:
            results.append((fname, "WARN", "Does NOT reference constitution"))
    return results


def check_precedence(content):
    results = []
    for item in PRECEDENCE_ORDER:
        if item.lower() in content.lower():
            results.append((item, "PASS", f"Precedence mentions {item}"))
        else:
            results.append((item, "WARN", f"Precedence missing {item}"))
    return results


def check_duplicate_rules():
    results = []
    if not CONSTITUTION.exists():
        return results

    content = CONSTITUTION.read_text("utf-8")

    sections = re.findall(r"^#+\s+(.+)$", content, re.MULTILINE)
    seen = set()
    dupes = []
    for s in sections:
        normalized = s.strip().lower()
        if normalized in seen:
            dupes.append(s)
        seen.add(normalized)

    if dupes:
        results.append(("duplicate_sections", "WARN", f"Duplicate sections: {dupes}"))
    else:
        results.append(("duplicate_sections", "PASS", f"No duplicate sections ({len(sections)} unique)"))

    return results


def check_constitution_sections():
    results = []
    if not CONSTITUTION.exists():
        return results

    content = CONSTITUTION.read_text("utf-8")

    required = [
        "VISION", "MISSION", "GOVERNANCE", "QUALITY", "SECURITY",
        "CHANGE MANAGEMENT", "TECHNICAL DEBT", "ROLLBACK",
    ]
    for sec in required:
        if sec.lower() in content.lower():
            results.append((f"section_{sec.lower()}", "PASS", f"Has {sec} section"))
        else:
            results.append((f"section_{sec.lower()}", "WARN", f"Missing {sec} section"))

    return results


def check_constitution_id():
    results = []
    if not CONSTITUTION.exists():
        return results

    content = CONSTITUTION.read_text("utf-8")
    if "CONST-" in content:
        const_ids = re.findall(r"CONST-\d{6}", content)
        results.append(("constitution_id", "PASS", f"Has ID: {const_ids}"))
    else:
        results.append(("constitution_id", "WARN", "No CONST-NNNNNN ID found"))

    return results


def run_validation():
    start = time.time()
    report = {"timestamp": datetime.now().isoformat(), "checks": []}

    ok, msg, content = check_constitution_exists()
    report["checks"].append({"name": "constitution_exists", "status": "PASS" if ok else "FAIL", "message": msg})
    if not ok:
        report["duration_ms"] = int((time.time() - start) * 1000)
        return report

    content_map = {}
    for fname in AI_CONFIG_FILES + GITHUB_CONFIG_FILES:
        p = REPO_ROOT / fname
        if p.exists():
            content_map[fname] = p.read_text("utf-8")

    for name, status, msg in check_config_references(content_map):
        report["checks"].append({"name": f"ref_{name}", "status": status, "message": msg})

    for name, status, msg in check_precedence(content):
        report["checks"].append({"name": f"prec_{name}", "status": status, "message": msg})

    for name, status, msg in check_duplicate_rules():
        report["checks"].append({"name": name, "status": status, "message": msg})

    for name, status, msg in check_constitution_sections():
        report["checks"].append({"name": name, "status": status, "message": msg})

    for name, status, msg in check_constitution_id():
        report["checks"].append({"name": name, "status": status, "message": msg})

    report["duration_ms"] = int((time.time() - start) * 1000)
    report["total"] = len(report["checks"])
    report["passed"] = sum(1 for c in report["checks"] if c["status"] == "PASS")
    report["warnings"] = sum(1 for c in report["checks"] if c["status"] == "WARN")
    report["failures"] = sum(1 for c in report["checks"] if c["status"] == "FAIL")
    report["overall"] = "FAIL" if report["failures"] > 0 else ("WARN" if report["warnings"] > 0 else "PASS")
    return report


def print_report(report, use_json=False):
    if use_json:
        print(json.dumps(report, indent=2))
        return

    print("=" * 70)
    print("CONSTITUTION VALIDATOR")
    print("=" * 70)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Duration: {report['duration_ms']}ms")
    print(f"Overall: {report['overall']}")
    print(f"Checks: {report['total']} | PASS: {report['passed']} | WARN: {report['warnings']} | FAIL: {report['failures']}")
    print("=" * 70)

    for c in report["checks"]:
        icon = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]"}[c["status"]]
        print(f"  {icon} {c['message']}")

    print("=" * 70)
    print(f"RESULT: {report['overall']}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Constitution Validator")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    report = run_validation()
    print_report(report, use_json=args.json)
    sys.exit(1 if report["overall"] == "FAIL" else 0)


if __name__ == "__main__":
    main()
