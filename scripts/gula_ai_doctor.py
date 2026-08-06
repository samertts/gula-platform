#!/usr/bin/env python3
"""PROGRAM-AUTOMATION-001: AI Health Doctor"""
import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_CORE = REPO_ROOT / ".ai" / "core"
SCRIPTS = REPO_ROOT / "scripts"

class HC:
    def __init__(s, name, cat):
        s.name, s.category, s.status, s.message, s.score = name, cat, "PASS", "", 100
    def warn(s, m): s.status, s.message, s.score = "WARN", m, 70
    def fail(s, m): s.status, s.message, s.score = "FAIL", m, 0
    def ok(s, m): s.status, s.message = "PASS", m

def chk_constitution():
    h = HC("constitution", "Constitution")
    p = REPO_ROOT / "AI_OPERATING_CONSTITUTION.md"
    if p.exists():
        h.ok(f"Constitution exists ({len(p.read_text('utf-8').strip().splitlines())} lines)")
    else:
        h.fail("Not found")
    return h

def chk_bootstrap():
    h = HC("bootstrap", "Bootstrap")
    p = REPO_ROOT / "AI_BOOTSTRAP.md"
    if p.exists():
        c = p.read_text("utf-8")
        h.ok(f"Bootstrap exists ({len(c)} chars)" + (", refs constitution" if "AI_OPERATING_CONSTITUTION" in c else ""))
    else:
        h.fail("Not found")
    return h

def chk_knowledge():
    h = HC("knowledge", "Knowledge System")
    if AI_CORE.exists():
        d = [x.name for x in AI_CORE.iterdir() if x.is_dir()]
        f = list(AI_CORE.rglob("*.md"))
        h.ok(f"{len(d)} dirs, {len(f)} files")
    else:
        h.fail(".ai/core/ not found")
    return h

def chk_registry():
    h = HC("registry", "Registry")
    p = AI_CORE / "registry" / "REGISTRY.md"
    if p.exists():
        c = p.read_text("utf-8")
        t = re.search(r"\*\*Total Artifacts\*\*.*?\|\s*(\d+)", c)
        h.ok(f"Registry: {t.group(1)} artifacts" if t else "Registry exists")
    else:
        h.fail("REGISTRY.md not found")
    return h

def chk_graph():
    h = HC("graph", "Knowledge Graph")
    p = AI_CORE / "graph" / "README.md"
    if p.exists():
        e = len([l for l in p.read_text("utf-8").splitlines() if "|" in l and "---" not in l])
        h.ok(f"{e} edges")
    else:
        h.warn("Graph not found")
    return h

def chk_templates():
    h = HC("templates", "Templates")
    d = AI_CORE / "templates"
    if d.exists():
        r = ["SKILL_TEMPLATE.md", "PLAYBOOK_TEMPLATE.md", "RUNBOOK_TEMPLATE.md"]
        m = [t for t in r if not (d/t).exists()]
        h.ok(f"All {len(r)} present") if not m else h.warn(f"Missing: {m}")
    else:
        h.fail("Templates dir not found")
    return h

def chk_skills():
    h = HC("skills", "Skills")
    d = AI_CORE / "skills"
    if d.exists():
        s = [f for f in d.glob("*.md") if f.name not in ("README.md","SKILL_TEMPLATE.md")]
        h.ok(f"{len(s)} skills")
    else:
        h.warn("Skills dir not found")
    return h

def chk_playbooks():
    h = HC("playbooks", "Playbooks")
    d = AI_CORE / "playbooks"
    if d.exists():
        i = [f for f in d.glob("*.md") if f.name not in ("README.md","PLAYBOOK_TEMPLATE.md")]
        h.ok(f"{len(i)} playbooks")
    else:
        h.warn("Playbooks dir not found")
    return h

def chk_runbooks():
    h = HC("runbooks", "Runbooks")
    d = AI_CORE / "runbooks"
    if d.exists():
        i = [f for f in d.glob("*.md") if f.name not in ("README.md","RUNBOOK_TEMPLATE.md")]
        h.ok(f"{len(i)} runbooks")
    else:
        h.warn("Runbooks dir not found")
    return h

def chk_capabilities():
    h = HC("capabilities", "Capabilities")
    p = AI_CORE / "capabilities" / "README.md"
    if p.exists():
        c = re.findall(r"CAP-\d{6}", p.read_text("utf-8"))
        h.ok(f"{len(c)} capabilities")
    else:
        h.warn("Not found")
    return h

def chk_decisions():
    h = HC("decisions", "Decisions")
    p = AI_CORE / "decisions" / "README.md"
    if p.exists():
        d = re.findall(r"DEC-\d{6}", p.read_text("utf-8"))
        h.ok(f"{len(d)} decisions")
    else:
        h.warn("Not found")
    return h

def chk_failures():
    h = HC("failures", "Failures")
    p = AI_CORE / "failures" / "README.md"
    if p.exists():
        f = re.findall(r"FAILURE-\d{6}", p.read_text("utf-8"))
        h.ok(f"{len(f)} failures tracked")
    else:
        h.warn("Not found")
    return h

def chk_kup():
    h = HC("kup", "KUP System")
    d = AI_CORE / "kup"
    if d.exists():
        k = [f for f in d.glob("*.md") if f.name not in ("README.md","RFC_WORKFLOW.md","KUP_TEMPLATE.md","APPROVAL_WORKFLOW.md","MERGE_POLICY.md","VERSIONING.md","QUALITY_REQUIREMENTS.md")]
        h.ok(f"{len(k)} KUPs")
    else:
        h.warn("KUP dir not found")
    return h

def chk_rfc():
    h = HC("rfc", "RFC Workflow")
    p = AI_CORE / "kup" / "RFC_WORKFLOW.md"
    h.ok("RFC workflow documented") if p.exists() else h.warn("Not found")
    return h

def chk_adr():
    h = HC("adr", "ADR System")
    d = REPO_ROOT / "docs" / "adr"
    if d.exists():
        h.ok(f"{len(list(d.glob('*.md')))} ADRs")
    else:
        h.warn("docs/adr/ not found")
    return h

def chk_documentation():
    h = HC("documentation", "Documentation")
    d = REPO_ROOT / "docs"
    if d.exists():
        h.ok(f"{len(list(d.rglob('*.md')))} doc files")
    else:
        h.warn("docs/ not found")
    return h

def chk_automation():
    h = HC("automation", "Automation")
    s = list(SCRIPTS.glob("*.py")) + list(SCRIPTS.glob("*.sh"))
    h.ok(f"{len(s)} scripts")
    return h

def chk_quality():
    h = HC("quality", "Quality System")
    d = AI_CORE / "quality"
    if d.exists():
        h.ok(f"{len(list(d.glob('*.md')))} quality docs")
    else:
        h.warn("Quality dir not found")
    return h

def chk_memory():
    h = HC("memory", "Memory")
    d = AI_CORE / "memory"
    if d.exists():
        h.ok(f"{len(list(d.glob('*.md')))} memory files")
    else:
        h.warn("Memory dir not found")
    return h

def chk_config_files():
    h = HC("config_files", "AI Config Files")
    c = ["AGENTS.md","CLAUDE.md","COPILOT.md","CODEX.md","GEMINI.md"]
    f = [x for x in c if (REPO_ROOT/x).exists()]
    h.ok(f"All {len(c)} present") if len(f)==len(c) else h.warn(f"Missing: {[x for x in c if x not in f]}")
    return h

ALL_CHECKS = [chk_constitution, chk_bootstrap, chk_knowledge, chk_registry, chk_graph, chk_templates, chk_skills, chk_playbooks, chk_runbooks, chk_capabilities, chk_decisions, chk_failures, chk_kup, chk_rfc, chk_adr, chk_documentation, chk_automation, chk_quality, chk_memory, chk_config_files]

def run_doctor(section=None):
    start = time.time()
    checks = []
    for func in ALL_CHECKS:
        c = func()
        if not section or c.category.lower()==section.lower() or c.name==section:
            checks.append(c)
    dur = int((time.time()-start)*1000)
    p = sum(1 for c in checks if c.status=="PASS")
    w = sum(1 for c in checks if c.status=="WARN")
    f = sum(1 for c in checks if c.status=="FAIL")
    avg = sum(c.score for c in checks)/len(checks) if checks else 0
    overall = "FAIL" if f>0 else ("WARN" if w>0 else "PASS")
    return {"timestamp":datetime.now().isoformat(),"duration_ms":dur,"overall":overall,"health_score":round(avg,1),"total":len(checks),"passed":p,"warnings":w,"failures":f,"checks":[{"name":c.name,"category":c.category,"status":c.status,"message":c.message,"score":c.score} for c in checks]}

def print_report(r, use_json=False):
    if use_json: print(json.dumps(r,indent=2)); return
    print("="*70)
    print("GULA AI DOCTOR")
    print("="*70)
    print(f"Timestamp: {r['timestamp']}")
    print(f"Duration: {r['duration_ms']}ms")
    print(f"Overall: {r['overall']}")
    print(f"Health Score: {r['health_score']}/100")
    print(f"Checks: {r['total']} | PASS: {r['passed']} | WARN: {r['warnings']} | FAIL: {r['failures']}")
    print("="*70)
    for c in r["checks"]:
        ic = {"PASS":"[PASS]","WARN":"[WARN]","FAIL":"[FAIL]"}[c["status"]]
        sc = f"({c['score']})" if c["score"]<100 else ""
        print(f"  {ic} {sc:5s} {c['category']:20s} {c['message']}")
    print("="*70)
    print(f"RESULT: {r['overall']} | Health: {r['health_score']}/100")
    print("="*70)

def main():
    p = argparse.ArgumentParser(description="AI Health Doctor")
    p.add_argument("--json", action="store_true")
    p.add_argument("--section", type=str)
    args = p.parse_args()
    r = run_doctor(section=args.section)
    print_report(r, use_json=args.json)
    sys.exit(1 if r["overall"]=="FAIL" else 0)

if __name__ == "__main__":
    main()
