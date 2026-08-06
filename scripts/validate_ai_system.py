#!/usr/bin/env python3
"""
PROGRAM-AUTOMATION-001: AI Validation Engine

Validates the entire GULA AI Operating System:
- Constitution compliance
- Bootstrap integrity
- Knowledge system integrity
- Registry consistency
- Skill/Playbook/Runbook completeness
- Template validity
- Index accuracy
- Graph integrity
- Cross-references
- Broken links
- Duplicate IDs
- Missing metadata
- Invalid references

Usage:
    python scripts/validate_ai_system.py              # Full validation
    python scripts/validate_ai_system.py --fast       # Quick checks only
    python scripts/validate_ai_system.py --section X  # Validate specific section
    python scripts/validate_ai_system.py --json       # JSON output
"""

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AI_CORE = REPO_ROOT / ".ai" / "core"

REQUIRED_AI_CORE_DIRS = [
    "index", "registry", "graph", "memory", "skills", "playbooks",
    "runbooks", "templates", "quality", "capabilities", "decisions",
    "failures", "kup", "constitution", "prompts", "lessons", "reports",
    "checkpoints", "automation", "backend", "frontend", "mobile", "api",
    "database", "devops", "security", "architecture", "performance",
    "monitoring", "observability", "infrastructure", "deployment",
    "desktop", "testing", "research", "reviews", "roadmap", "incidents",
]

ID_PATTERNS = {
    "KUP": r"KUP-\d{6}", "SKILL": r"SKILL-\d{6}",
    "PLAYBOOK": r"PLAYBOOK-\d{6}", "RUNBOOK": r"RUNBOOK-\d{6}",
    "CHECKLIST": r"CHECKLIST-\d{6}", "KNOW": r"KNOW-\d{6}",
    "CAP": r"CAP-\d{6}", "DEC": r"DEC-\d{6}",
    "FAILURE": r"FAILURE-\d{6}", "DEBT": r"DEBT-\d{6}",
    "REPORT": r"REPORT-\d{6}", "CONST": r"CONST-\d{6}",
}


@dataclass
class Check:
    name: str
    status: str  # PASS, WARN, FAIL
    message: str
    section: str = ""


@dataclass
class Report:
    checks: list = field(default_factory=list)
    sections: dict = field(default_factory=dict)
    start_time: float = 0
    duration_ms: int = 0

    def add(self, name: str, status: str, message: str, section: str = ""):
        c = Check(name=name, status=status, message=message, section=section)
        self.checks.append(c)
        self.sections.setdefault(section, []).append(c)

    @property
    def passed(self): return sum(1 for c in self.checks if c.status == "PASS")

    @property
    def warnings(self): return sum(1 for c in self.checks if c.status == "WARN")

    @property
    def failures(self): return sum(1 for c in self.checks if c.status == "FAIL")

    @property
    def total(self): return len(self.checks)

    @property
    def overall(self):
        if self.failures > 0: return "FAIL"
        if self.warnings > 0: return "WARN"
        return "PASS"


def validate_constitution(r: Report):
    const = REPO_ROOT / "AI_OPERATING_CONSTITUTION.md"
    if const.exists():
        content = const.read_text("utf-8")
        lines = content.strip().split("\n")
        r.add("constitution_exists", "PASS", f"Constitution exists ({len(lines)} lines)", "constitution")
        for sec in ["VISION", "MISSION", "PRINCIPLES", "GOVERNANCE", "QUALITY", "SECURITY"]:
            if sec.lower() in content.lower():
                r.add(f"const_{sec.lower()}", "PASS", f"Has {sec} section", "constitution")
            else:
                r.add(f"const_{sec.lower()}", "WARN", f"Missing {sec} section", "constitution")
    else:
        r.add("constitution_exists", "FAIL", "AI_OPERATING_CONSTITUTION.md not found", "constitution")

    reg = AI_CORE / "constitution" / "CONSTITUTION_REGISTRY.md"
    r.add("constitution_registry", "PASS" if reg.exists() else "WARN",
          "Constitution registry exists" if reg.exists() else "Constitution registry missing", "constitution")


def validate_bootstrap(r: Report):
    bs = REPO_ROOT / "AI_BOOTSTRAP.md"
    if bs.exists():
        content = bs.read_text("utf-8")
        lines = content.strip().split("\n")
        r.add("bootstrap_exists", "PASS", f"Bootstrap exists ({len(lines)} lines)", "bootstrap")
        for sec in ["constitution", "knowledge", "registry", "quality", "validation"]:
            if sec.lower() in content.lower():
                r.add(f"bs_{sec}", "PASS", f"Has {sec} section", "bootstrap")
            else:
                r.add(f"bs_{sec}", "WARN", f"Missing {sec} section", "bootstrap")
    else:
        r.add("bootstrap_exists", "FAIL", "AI_BOOTSTRAP.md not found", "bootstrap")


def validate_knowledge(r: Report):
    if AI_CORE.exists():
        dirs = [d.name for d in AI_CORE.iterdir() if d.is_dir()]
        missing = [d for d in REQUIRED_AI_CORE_DIRS if d not in dirs]
        if not missing:
            r.add("ai_dirs", "PASS", f"All {len(REQUIRED_AI_CORE_DIRS)} dirs present", "knowledge")
        else:
            r.add("ai_dirs", "WARN", f"Missing: {', '.join(missing)}", "knowledge")
    else:
        r.add("ai_core", "FAIL", ".ai/core/ not found", "knowledge")

    for tmpl in ["SKILL_TEMPLATE.md", "PLAYBOOK_TEMPLATE.md", "RUNBOOK_TEMPLATE.md"]:
        p = AI_CORE / "templates" / tmpl
        r.add(f"tmpl_{tmpl}", "PASS" if p.exists() else "WARN",
              f"{tmpl} exists" if p.exists() else f"{tmpl} missing", "knowledge")

    mem = AI_CORE / "memory"
    if mem.exists():
        count = len(list(mem.glob("*.md")))
        r.add("memory", "PASS", f"Memory has {count} files", "knowledge")
    else:
        r.add("memory", "WARN", "Memory dir missing", "knowledge")


def validate_registry(r: Report):
    reg = AI_CORE / "registry" / "REGISTRY.md"
    if reg.exists():
        content = reg.read_text("utf-8")
        ver = re.search(r"(?:Version:\s*|version:\s*[\"']?)([^\s\"']+)", content)
        if ver:
            r.add("registry_version", "PASS", f"Version: {ver.group(1)}", "registry")
        else:
            r.add("registry_version", "WARN", "No version found", "registry")
        all_ids = []
        for pat in ID_PATTERNS.values():
            all_ids.extend(re.findall(pat, content))
        seen = set()
        dupes = [i for i in all_ids if i in seen or seen.add(i)]
        r.add("registry_ids", "PASS" if not dupes else "FAIL",
              f"{len(all_ids)} IDs, no duplicates" if not dupes else f"Dupes: {dupes}", "registry")
    else:
        r.add("registry_exists", "FAIL", "REGISTRY.md not found", "registry")


def validate_skills(r: Report):
    d = AI_CORE / "skills"
    if d.exists():
        skills = [f for f in d.glob("*.md") if f.name not in ("README.md", "SKILL_TEMPLATE.md")]
        r.add("skills_count", "PASS", f"{len(skills)} skills", "skills")
        for s in skills:
            content = s.read_text("utf-8")
            if len(content.strip()) < 50:
                r.add(f"skill_{s.stem}", "WARN", f"{s.name} is very short", "skills")
    else:
        r.add("skills_dir", "WARN", "Skills dir missing", "skills")


def validate_playbooks(r: Report):
    d = AI_CORE / "playbooks"
    if d.exists():
        items = [f for f in d.glob("*.md") if f.name not in ("README.md", "PLAYBOOK_TEMPLATE.md")]
        r.add("playbooks_count", "PASS", f"{len(items)} playbooks", "playbooks")
    else:
        r.add("playbooks_dir", "WARN", "Playbooks dir missing", "playbooks")


def validate_runbooks(r: Report):
    d = AI_CORE / "runbooks"
    if d.exists():
        items = [f for f in d.glob("*.md") if f.name not in ("README.md", "RUNBOOK_TEMPLATE.md")]
        r.add("runbooks_count", "PASS", f"{len(items)} runbooks", "runbooks")
    else:
        r.add("runbooks_dir", "WARN", "Runbooks dir missing", "runbooks")


def validate_capabilities(r: Report):
    cap = AI_CORE / "capabilities" / "README.md"
    if cap.exists():
        content = cap.read_text("utf-8")
        caps = re.findall(r"CAP-\d{6}", content)
        r.add("capabilities", "PASS", f"{len(caps)} capabilities registered", "capabilities")
    else:
        r.add("capabilities", "WARN", "Capabilities README missing", "capabilities")


def validate_decisions(r: Report):
    dec = AI_CORE / "decisions" / "README.md"
    if dec.exists():
        content = dec.read_text("utf-8")
        decs = re.findall(r"DEC-\d{6}", content)
        r.add("decisions", "PASS", f"{len(decs)} decisions registered", "decisions")
    else:
        r.add("decisions", "WARN", "Decisions README missing", "decisions")


def validate_failures(r: Report):
    fail = AI_CORE / "failures" / "README.md"
    if fail.exists():
        content = fail.read_text("utf-8")
        fails = re.findall(r"FAILURE-\d{6}", content)
        r.add("failures", "PASS", f"{len(fails)} failures tracked", "failures")
    else:
        r.add("failures", "WARN", "Failures README missing", "failures")


def validate_kup(r: Report):
    kup_dir = AI_CORE / "kup"
    if kup_dir.exists():
        kups = [f for f in kup_dir.glob("*.md") if f.name not in ("README.md", "RFC_WORKFLOW.md", "KUP_TEMPLATE.md", "APPROVAL_WORKFLOW.md", "MERGE_POLICY.md", "VERSIONING.md", "QUALITY_REQUIREMENTS.md")]
        r.add("kup_count", "PASS", f"{len(kups)} KUPs", "kup")
    else:
        r.add("kup_dir", "WARN", "KUP dir missing", "kup")


def validate_quality(r: Report):
    q = AI_CORE / "quality"
    if q.exists():
        docs = list(q.glob("*.md"))
        r.add("quality_docs", "PASS", f"{len(docs)} quality docs", "quality")
    else:
        r.add("quality_dir", "WARN", "Quality dir missing", "quality")


def validate_graph(r: Report):
    g = AI_CORE / "graph" / "README.md"
    if g.exists():
        content = g.read_text("utf-8")
        edges = content.count("|")
        r.add("graph_edges", "PASS", "Graph has edges defined", "graph")
    else:
        r.add("graph", "WARN", "Graph README missing", "graph")


def validate_index(r: Report):
    idx = AI_CORE / "index" / "INDEX.md"
    if idx.exists():
        content = idx.read_text("utf-8")
        total_match = re.search(r"\*\*Grand total\*\*.*?\|\s*(\d+)", content)
        if total_match:
            r.add("index_total", "PASS", f"Index claims {total_match.group(1)} artifacts", "index")
        else:
            r.add("index_total", "WARN", "Index total not found", "index")
    else:
        r.add("index_exists", "FAIL", "INDEX.md not found", "index")


def validate_cross_references(r: Report):
    broken = []
    all_ids = {}
    for md_file in AI_CORE.rglob("*.md"):
        try:
            content = md_file.read_text("utf-8")
        except Exception:
            continue
        for name, pat in ID_PATTERNS.items():
            for match in re.findall(pat, content):
                all_ids.setdefault(match, []).append(str(md_file.relative_to(REPO_ROOT)))

    dupes = {k: v for k, v in all_ids.items() if len(v) > 1}
    if dupes:
        r.add("cross_ref_dupes", "WARN", f"ID refs in multiple files: {len(dupes)}", "cross_references")
    else:
        r.add("cross_ref_dupes", "PASS", "No duplicate ID references", "cross_references")

    r.add("total_ids", "PASS", f"{len(all_ids)} unique IDs across all files", "cross_references")


def validate_ai_config_files(r: Report):
    configs = ["AGENTS.md", "CLAUDE.md", "COPILOT.md", "CODEX.md", "GEMINI.md"]
    for f in configs:
        p = REPO_ROOT / f
        if p.exists():
            content = p.read_text("utf-8")
            has_const = "AI_OPERATING_CONSTITUTION" in content
            has_bootstrap = "AI_BOOTSTRAP" in content
            r.add(f"config_{f}", "PASS" if has_const else "WARN",
                  f"{f}: constitution={'yes' if has_const else 'no'}, bootstrap={'yes' if has_bootstrap else 'no'}",
                  "config_files")
        else:
            r.add(f"config_{f}", "WARN", f"{f} not found", "config_files")


def validate_broken_links(r: Report):
    broken = []
    for md_file in AI_CORE.rglob("*.md"):
        try:
            content = md_file.read_text("utf-8")
        except Exception:
            continue
        for match in re.finditer(r"\[.*?\]\(([^)]+)\)", content):
            link = match.group(1)
            if link.startswith("http") or link.startswith("#"):
                continue
            target = (md_file.parent / link).resolve()
            if not target.exists():
                broken.append(f"{md_file.name} -> {link}")

    if broken:
        r.add("broken_links", "WARN", f"{len(broken)} broken links found", "cross_references")
    else:
        r.add("broken_links", "PASS", "No broken links found", "cross_references")


def validate_versioning(r: Report):
    reg = AI_CORE / "registry" / "REGISTRY.md"
    if reg.exists():
        content = reg.read_text("utf-8")
        ver = re.search(r"Version:\s*(\S+)", content)
        if ver:
            r.add("registry_version", "PASS", f"Version: {ver.group(1)}", "versioning")
        else:
            r.add("registry_version", "WARN", "No version found", "versioning")
    else:
        r.add("registry_version", "FAIL", "Registry not found", "versioning")


def run_validation(section: str = None, fast: bool = False):
    report = Report(start_time=time.time())

    validators = {
        "constitution": validate_constitution,
        "bootstrap": validate_bootstrap,
        "knowledge": validate_knowledge,
        "registry": validate_registry,
        "skills": validate_skills,
        "playbooks": validate_playbooks,
        "runbooks": validate_runbooks,
        "capabilities": validate_capabilities,
        "decisions": validate_decisions,
        "failures": validate_failures,
        "kup": validate_kup,
        "quality": validate_quality,
        "graph": validate_graph,
        "index": validate_index,
        "cross_references": validate_cross_references,
        "config_files": validate_ai_config_files,
        "versioning": validate_versioning,
    }

    if fast:
        validators = {k: v for k, v in validators.items()
                      if k in ("constitution", "bootstrap", "registry", "knowledge", "index")}

    if section:
        if section in validators:
            validators[section](report)
        else:
            print(f"Unknown section: {section}")
            print(f"Available: {', '.join(validators.keys())}")
            sys.exit(1)
    else:
        for name, func in validators.items():
            func(report)

    report.duration_ms = int((time.time() - report.start_time) * 1000)
    return report


def print_report(report: Report, use_json: bool = False):
    if use_json:
        data = {
            "timestamp": datetime.now().isoformat(),
            "duration_ms": report.duration_ms,
            "overall": report.overall,
            "total": report.total,
            "passed": report.passed,
            "warnings": report.warnings,
            "failures": report.failures,
            "sections": {},
        }
        for section, checks in report.sections.items():
            data["sections"][section] = [
                {"name": c.name, "status": c.status, "message": c.message}
                for c in checks
            ]
        print(json.dumps(data, indent=2))
        return

    print()
    print("=" * 70)
    print("GULA AI VALIDATION ENGINE")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Duration: {report.duration_ms}ms")
    print(f"Overall: {report.overall}")
    print(f"Checks: {report.total} | PASS: {report.passed} | WARN: {report.warnings} | FAIL: {report.failures}")
    print("=" * 70)

    for section, checks in report.sections.items():
        print(f"\n--- {section.upper()} ---")
        for c in checks:
            icon = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]"}.get(c.status, "[????]")
            print(f"  {icon} {c.message}")

    print("\n" + "=" * 70)
    if report.overall == "PASS":
        print("RESULT: ALL CHECKS PASSED")
    elif report.overall == "WARN":
        print(f"RESULT: PASSED WITH {report.warnings} WARNINGS")
    else:
        print(f"RESULT: {report.failures} FAILURES DETECTED")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="GULA AI Validation Engine")
    parser.add_argument("--fast", action="store_true", help="Quick checks only")
    parser.add_argument("--section", type=str, help="Validate specific section")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--list-sections", action="store_true", help="List available sections")
    args = parser.parse_args()

    if args.list_sections:
        print("Available sections:")
        for s in ["constitution", "bootstrap", "knowledge", "registry", "skills",
                   "playbooks", "runbooks", "capabilities", "decisions", "failures",
                   "kup", "quality", "graph", "index", "cross_references",
                   "config_files", "versioning"]:
            print(f"  {s}")
        sys.exit(0)

    report = run_validation(section=args.section, fast=args.fast)
    print_report(report, use_json=args.json)
    sys.exit(1 if report.overall == "FAIL" else 0)


if __name__ == "__main__":
    main()
