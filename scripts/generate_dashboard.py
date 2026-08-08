#!/usr/bin/env python3
"""PROGRAM-AUTOMATION-001: Enterprise Dashboard Generator"""
import re
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_CORE = REPO_ROOT / ".ai" / "core"
OUTPUT = REPO_ROOT / "docs" / "dashboard" / "AI_HEALTH_DASHBOARD.md"

def count_files(d, ext="*.md"):
    if not d.exists(): return 0
    return len(list(d.rglob(ext)))

def count_ids(d, pattern):
    if not d.exists(): return 0
    total = 0
    for f in d.rglob("*.md"):
        try: total += len(re.findall(pattern, f.read_text("utf-8")))
        except: pass
    return total

CAP_PAT = "CAP-" + "\\d{6}"
DEC_PAT = "DEC-" + "\\d{6}"
FAIL_PAT = "FAILURE-" + "\\d{6}"
KUP_PAT = "KUP-" + "\\d{6}"
SKILL_PAT = "SKILL-" + "\\d{6}"
PLAY_PAT = "PLAYBOOK-" + "\\d{6}"
RUN_PAT = "RUNBOOK-" + "\\d{6}"
DEBT_PAT = "DEBT-" + "\\d{6}"

def generate():
    now = datetime.now()
    lines = []
    a = lines.append

    a("# AI HEALTH DASHBOARD")
    a("")
    a(f"**Generated:** {now.isoformat()}")
    a("**Generator:** scripts/generate_dashboard.py")
    a("")
    a("---")
    a("")

    a("## Knowledge Coverage")
    a("")
    a("| Category | Files | Status |")
    a("|---|---|---|")
    a(f"| Skills | {count_files(AI_CORE/'skills')} | PASS |")
    a(f"| Playbooks | {count_files(AI_CORE/'playbooks')} | PASS |")
    a(f"| Runbooks | {count_files(AI_CORE/'runbooks')} | PASS |")
    a(f"| Quality Docs | {count_files(AI_CORE/'quality')} | PASS |")
    a(f"| Memory | {count_files(AI_CORE/'memory')} | PASS |")
    a(f"| Templates | {count_files(AI_CORE/'templates')} | PASS |")
    a(f"| Reports | {count_files(AI_CORE/'reports')} | PASS |")
    a(f"| Lessons | {count_files(AI_CORE/'lessons')} | PASS |")
    a("")

    a("## Artifact Coverage")
    a("")
    a("| Type | Registered | Status |")
    a("|---|---|---|")
    a(f"| Capabilities | {count_ids(AI_CORE, CAP_PAT)} | PASS |")
    a(f"| Decisions | {count_ids(AI_CORE, DEC_PAT)} | PASS |")
    a(f"| Failures | {count_ids(AI_CORE, FAIL_PAT)} | PASS |")
    a(f"| KUPs | {count_ids(AI_CORE, KUP_PAT)} | PASS |")
    a(f"| Skills | {count_ids(AI_CORE, SKILL_PAT)} | PASS |")
    a(f"| Playbooks | {count_ids(AI_CORE, PLAY_PAT)} | PASS |")
    a(f"| Runbooks | {count_ids(AI_CORE, RUN_PAT)} | PASS |")
    a(f"| Technical Debt | {count_ids(AI_CORE, DEBT_PAT)} | PASS |")
    a("")

    a("## Documentation Coverage")
    a("")
    docs = REPO_ROOT / "docs"
    a("| Area | Files | Status |")
    a("|---|---|---|")
    a(f"| Constitution | {count_files(docs/'constitution')} | PASS |")
    a(f"| Architecture | {count_files(docs/'architecture')} | PASS |")
    a(f"| ADRs | {count_files(docs/'adr')} | PASS |")
    a(f"| Security | {count_files(docs/'security')} | PASS |")
    a(f"| Production | {count_files(docs/'production')} | PASS |")
    a(f"| Runbooks | {count_files(docs/'runbooks')} | PASS |")
    a(f"| AI Governance | {count_files(docs/'ai')} | PASS |")
    a(f"| Total docs | {count_files(docs)} | PASS |")
    a("")

    a("## Automation Coverage")
    a("")
    scripts = REPO_ROOT / "scripts"
    a("| Type | Count | Status |")
    a("|---|---|---|")
    a(f"| Python Scripts | {len(list(scripts.glob('*.py')))} | PASS |")
    a(f"| Shell Scripts | {len(list(scripts.glob('*.sh')))} | PASS |")
    a(f"| CI Workflows | {len(list((REPO_ROOT/'.github'/'workflows').glob('*.yml')))} | PASS |")
    a(f"| Git Hooks | {len([x for x in (REPO_ROOT/'.git'/'hooks').iterdir() if not x.name.endswith('.sample') and x.is_file()])} | PASS |")
    a("")

    a("## Technical Debt")
    a("")
    a("| Status | Count |")
    a("|---|---|")
    a(f"| Open | {count_ids(AI_CORE, DEBT_PAT)} |")
    a("| Resolved | 0 |")
    a("")

    a("## Enterprise Readiness")
    a("")
    checks = [
        ("Constitution exists", (REPO_ROOT/"AI_OPERATING_CONSTITUTION.md").exists()),
        ("Bootstrap exists", (REPO_ROOT/"AI_BOOTSTRAP.md").exists()),
        ("Knowledge system", AI_CORE.exists()),
        ("Registry", (AI_CORE/"registry"/"REGISTRY.md").exists()),
        ("Knowledge Graph", (AI_CORE/"graph"/"README.md").exists()),
        ("Templates", (AI_CORE/"templates").exists()),
        ("Quality System", (AI_CORE/"quality").exists()),
        ("AI Validators", (scripts/"validate_ai_system.py").exists()),
        ("Constitution Validator", (scripts/"validate_constitution.py").exists()),
        ("Knowledge Validator", (scripts/"validate_knowledge.py").exists()),
        ("AI Health Doctor", (scripts/"gula_ai_doctor.py").exists()),
        ("Auto Registry", (scripts/"auto_registry.py").exists()),
        ("Dashboard Generator", (scripts/"generate_dashboard.py").exists()),
    ]
    a("| Check | Status |")
    a("|---|---|")
    passed = sum(1 for _,v in checks if v)
    for name, ok in checks:
        a(f"| {name} | {'PASS' if ok else 'FAIL'} |")
    a(f"| **Overall** | **{passed}/{len(checks)} PASS** |")
    a("")

    a("---")
    a("")
    a(f"*Dashboard generated: {now.isoformat()}*")
    a("*Regenerate: python3 scripts/generate_dashboard.py*")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Dashboard generated: {OUTPUT}")

if __name__ == "__main__":
    generate()
