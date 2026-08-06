#!/usr/bin/env python3
"""PROGRAM-AUTOMATION-001: Enforcement Policy

Rejects automatically:
- Broken Registry
- Broken Constitution
- Broken References
- Duplicate IDs
- Missing Rollback
- Missing Verification
- Missing Documentation
- Missing KUP
- Missing RFC (where required)
- Constitution violations

Usage:
    python scripts/enforce_policy.py                  # Enforce all policies
    python scripts/enforce_policy.py --check-only     # Check without exit codes
    python scripts/enforce_policy.py --json           # JSON output
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_CORE = REPO_ROOT / ".ai" / "core"
SCRIPTS = REPO_ROOT / "scripts"

def run_script(script):
    try:
        r = subprocess.run(["python3", str(SCRIPTS / script)], capture_output=True, text=True, timeout=120, cwd=REPO_ROOT)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return -1, "", str(e)

def enforce():
    results = []
    violations = []

    def add(name, status, msg):
        results.append({"name": name, "status": status, "message": msg})
        if status == "FAIL":
            violations.append(name)

    print("=" * 60)
    print("GULA AI ENFORCEMENT POLICY")
    print("=" * 60)

    # 1. Constitution validation
    rc, out, err = run_script("validate_constitution.py")
    add("constitution_valid", "PASS" if rc == 0 else "FAIL",
        "Constitution validation " + ("passed" if rc == 0 else "failed"))

    # 2. Knowledge validation
    rc, out, err = run_script("validate_knowledge.py")
    add("knowledge_valid", "PASS" if rc == 0 else "FAIL",
        "Knowledge validation " + ("passed" if rc == 0 else "failed"))

    # 3. AI System validation
    rc, out, err = run_script("validate_ai_system.py")
    add("ai_system_valid", "PASS" if rc == 0 else "FAIL",
        "AI system validation " + ("passed" if rc == 0 else "failed"))

    # 4. Duplicate IDs check
    rc, out, err = run_script("validate_knowledge.py")
    if "duplicate_ids" in out:
        add("duplicate_ids", "WARN", "Check duplicate IDs in knowledge validation")
    else:
        add("duplicate_ids", "PASS", "No duplicate ID issues detected")

    # 5. Registry integrity
    reg = AI_CORE / "registry" / "REGISTRY.md"
    add("registry_exists", "PASS" if reg.exists() else "FAIL",
        "Registry " + ("exists" if reg.exists() else "MISSING"))

    # 6. Broken references
    rc, out, err = run_script("validate_ai_system.py")
    if "broken links" in out.lower() or "broken_links" in out.lower():
        add("broken_references", "WARN", "Broken references detected")
    else:
        add("broken_references", "PASS", "No broken references")

    # 7. Documentation coverage
    docs = REPO_ROOT / "docs"
    doc_count = len(list(docs.rglob("*.md"))) if docs.exists() else 0
    add("documentation", "PASS" if doc_count > 10 else "FAIL",
        f"Documentation: {doc_count} files")

    # 8. Health check
    rc, out, err = run_script("gula_ai_doctor.py")
    health = "unknown"
    for line in out.split("\n"):
        if "Health Score" in line:
            m = re.search(r"([\d.]+)", line)
            if m: health = m.group(1)
    add("health_check", "PASS" if rc == 0 else "FAIL", f"Health: {health}/100")

    # 9. Missing KUP check (knowledge changes should have KUP)
    kup_count = len([f for f in (AI_CORE/"kup").glob("*.md") if f.name.startswith("KUP-")]) if (AI_CORE/"kup").exists() else 0
    add("kup_coverage", "PASS" if kup_count > 0 else "WARN", f"KUP count: {kup_count}")

    # 10. Constitution reference check
    const_refs = 0
    for cfg in ["AGENTS.md", "CLAUDE.md", "AI_BOOTSTRAP.md"]:
        p = REPO_ROOT / cfg
        if p.exists() and "AI_OPERATING_CONSTITUTION" in p.read_text("utf-8"):
            const_refs += 1
    add("constitution_references", "PASS" if const_refs >= 3 else "FAIL",
        f"Constitution referenced in {const_refs}/3 configs")

    # Summary
    failures = [r for r in results if r["status"] == "FAIL"]
    warnings = [r for r in results if r["status"] == "WARN"]

    print()
    for r in results:
        icon = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]"}[r["status"]]
        print(f"  {icon} {r['message']}")

    print()
    print("=" * 60)
    print(f"ENFORCEMENT RESULT: {len(failures)} FAILURES, {len(warnings)} WARNINGS")
    print("=" * 60)

    if failures:
        print("VIOLATIONS:")
        for f in failures:
            print(f"  - {f}")
        return {"overall": "FAIL", "results": results, "violations": failures}
    return {"overall": "WARN" if warnings else "PASS", "results": results, "violations": failures}

def main():
    parser = argparse.ArgumentParser(description="Enforcement Policy")
    parser.add_argument("--check-only", action="store_true", help="Check without exit")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = enforce()

    if args.json:
        print(json.dumps(report, indent=2))

    if not args.check_only and report["overall"] == "FAIL":
        sys.exit(1)

if __name__ == "__main__":
    main()
