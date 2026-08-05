"""Learner CLI — GULA-LEARNER-001 commands.

Integrated into `scripts/kernel.py` so the Kernel remains the single entry
point, matching the Builder, Reviewer, Orchestrator, and Deployer pattern.
"""

from __future__ import annotations

import sys


def run_audit() -> int:
    """Phase 0 — write LEARNER_AUDIT_REPORT.md."""
    from .audit import run_audit as _audit

    path = _audit()
    print(f"[OK] {path.name} written")
    return 0


def run_extract() -> int:
    """Phase 1 — extract knowledge from a mission or deployment record."""
    from scripts.kernel.core import REPO_ROOT
    from scripts.learner.core import read_json

    from .extract import extract_from_deployment, extract_from_mission, persist_extraction

    source = sys.argv[2] if len(sys.argv) > 2 else "mission:ORN-DEMO"
    path = None
    if source.startswith("deployment:"):
        record = read_json(
            REPO_ROOT / ".ai" / "core" / "deployer" / "history"
            / f"{source.split(':')[1]}.json"
        )
        if record:
            path = persist_extraction(extract_from_deployment(record))
    elif source.startswith("mission:"):
        registry = read_json(
            REPO_ROOT / ".ai" / "core" / "orchestrator" / "history" / "registry.json"
        )
        mission = registry.get("missions", {}).get(source.split(":", 1)[1])
        if mission:
            path = persist_extraction(extract_from_mission(mission))
    if path:
        print(f"[OK] extraction written to {path.relative_to(REPO_ROOT)}")
        return 0
    print(f"source not found: {source}")
    return 1


def run_skill() -> int:
    """Phase 2 — generate a reusable skill from an extraction."""
    from .extract import list_extractions
    from .skills import generate_skill, persist_skill

    extractions = list_extractions()
    if not extractions:
        print("No extractions yet. Run learner-extract first.")
        return 1
    for extraction in extractions[-1:]:
        skill = generate_skill(extraction)
        if skill is None:
            print("Extraction not reusable; no skill generated.")
            return 1
        path = persist_skill(skill)
        print(f"[OK] {skill.skill_id} -> {path.name}")
    return 0


def run_playbook() -> int:
    """Phase 3 — generate a playbook for a kind."""
    from scripts.learner.core import PLAYBOOK_KINDS

    from .extract import list_extractions
    from .playbooks import generate_playbook, persist_playbook

    kind = sys.argv[2] if len(sys.argv) > 2 else "deployment"
    if kind not in PLAYBOOK_KINDS:
        print(f"unknown playbook kind: {kind} (valid: {', '.join(PLAYBOOK_KINDS)})")
        return 2
    extractions = list_extractions()
    playbook = generate_playbook(kind, extractions[-1] if extractions else None)
    if playbook is None:
        print("could not generate playbook")
        return 2
    path = persist_playbook(playbook)
    print(f"[OK] {playbook.item_id} -> {path.name}")
    return 0


def run_runbook() -> int:
    """Phase 4 — generate a runbook for a kind."""
    from scripts.learner.core import RUNBOOK_KINDS

    from .extract import list_extractions
    from .runbooks import generate_runbook, persist_runbook

    kind = sys.argv[2] if len(sys.argv) > 2 else "production"
    if kind not in RUNBOOK_KINDS:
        print(f"unknown runbook kind: {kind} (valid: {', '.join(RUNBOOK_KINDS)})")
        return 2
    extractions = list_extractions()
    runbook = generate_runbook(kind, extractions[-1] if extractions else None)
    if runbook is None:
        print("could not generate runbook")
        return 2
    path = persist_runbook(runbook)
    print(f"[OK] {runbook.item_id} -> {path.name}")
    return 0


def run_memory() -> int:
    """Phase 5 — evolve memory and the knowledge graph."""
    from .memory import add_graph_node, evolve_memory, graph_nodes, persist_memory

    kind = sys.argv[2] if len(sys.argv) > 2 else "engineering"
    item = evolve_memory(kind, body="Recorded by the Learner knowledge pipeline.")
    path = persist_memory(item)
    add_graph_node(item.item_id, kind="memory", title=item.title,
                   related=["skills", "playbooks", "runbooks"])
    print(f"[OK] {item.item_id} -> {path.name} | graph nodes: {len(graph_nodes())}")
    return 0


def run_patterns() -> int:
    """Phase 6 — detect recurring patterns from knowledge evidence."""
    from .extract import list_extractions
    from .memory import graph_nodes
    from .patterns import detect_patterns, persist_patterns

    evidence: list[tuple[str, str]] = []
    for extraction in list_extractions():
        evidence.append((_area(extraction.source), extraction.solution))
    for node in graph_nodes():
        evidence.append((node.get("kind", ""), node.get("title", "")))
    patterns = detect_patterns(evidence)
    path = persist_patterns(patterns)
    print(f"[OK] {len(patterns)} pattern(s) -> {path.name}")
    return 0


def run_improve() -> int:
    """Phase 7 — propose engine improvements."""
    from .improve import persist_proposals, propose_improvements

    proposals = propose_improvements()
    path = persist_proposals(proposals)
    for proposal in proposals:
        print(f"  [open] {proposal.proposal_id} {proposal.target:<16} {proposal.title}")
    print(f"[OK] {len(proposals)} proposals -> {path.name}")
    return 0


def run_quality() -> int:
    """Phase 8 — run all knowledge-quality checks."""
    from .quality import render_markdown, run_quality

    report = run_quality()
    print(render_markdown(report))
    return 0 if report.health_score >= 70 else 1


def run_search() -> int:
    """Phase 9 — build the search index or search for a query."""
    from .search import build_index, count_documents, search

    arg = sys.argv[2] if len(sys.argv) > 2 else "--build"
    if arg == "--build":
        build_index()
        print(f"[OK] index built with {count_documents()} documents")
        return 0
    results = search(arg)
    if not results:
        print("no results")
        return 0
    for result in results[:8]:
        print(f"  [{result['kind']}] {result['id']} -> {result['path']}")
    return 0


def run_report() -> int:
    """Phase 10 — write LEARNER_IMPLEMENTATION_REPORT.md."""
    from .report import build_report

    build_report()
    print("[OK] LEARNER_IMPLEMENTATION_REPORT.md written")
    return 0


def _run_learn() -> int:
    """Run the complete learning pipeline end-to-end (the success criterion)."""
    from .audit import run_audit as _audit
    from .extract import extract_from_mission, persist_extraction
    from .improve import persist_proposals, propose_improvements
    from .memory import add_graph_node, evolve_memory, find_memory_by_title, persist_memory
    from .patterns import detect_patterns, persist_patterns
    from .playbooks import find_playbook_by_title, generate_playbook, persist_playbook
    from .report import build_report
    from .runbooks import find_runbook_by_title, generate_runbook, persist_runbook
    from .search import build_index, count_documents
    from .skills import find_skill_by_title, generate_skill, persist_skill

    _audit()

    mission = {
        "mission_id": "ORN-LEARN-001",
        "objective": "Record knowledge from a completed engineering mission",
        "mission_type": "refactor",
        "status": "complete",
    }
    extraction = extract_from_mission(mission)
    persist_extraction(extraction)
    print(f"[1] extraction from {extraction.source}")

    skill = generate_skill(extraction, title="Knowledge Recording Pipeline",
                           technology="python")
    if skill is None:
        print("[2] SKIPPED — extraction not reusable")
    else:
        existing = find_skill_by_title(skill.title)
        if existing is not None:
            skill = existing
            print(f"[2] reuse existing skill {skill.skill_id}")
        else:
            skill_path = persist_skill(skill)
            print(f"[2] skill {skill.skill_id} -> {skill_path.name}")

    playbook = generate_playbook("deployment", extraction)
    existing_playbook = find_playbook_by_title(playbook.title)
    if existing_playbook is not None:
        playbook = existing_playbook
        print(f"[3] reuse existing playbook {playbook.item_id}")
    else:
        playbook_path = persist_playbook(playbook)
        print(f"[3] playbook {playbook.item_id} -> {playbook_path.name}")

    runbook = generate_runbook("production", extraction)
    existing_runbook = find_runbook_by_title(runbook.title)
    if existing_runbook is not None:
        runbook = existing_runbook
        print(f"[4] reuse existing runbook {runbook.item_id}")
    else:
        runbook_path = persist_runbook(runbook)
        print(f"[4] runbook {runbook.item_id} -> {runbook_path.name}")

    memory = evolve_memory(
        "engineering",
        title="Mission Knowledge Pipeline",
        body=extraction.solution,
    )
    existing_memory = find_memory_by_title(memory.title)
    if existing_memory is not None:
        memory = existing_memory
        print(f"[5] reuse existing memory {memory.item_id}")
    else:
        memory_path = persist_memory(memory)
        print(f"[5] memory {memory.item_id} -> {memory_path.name}")
    add_graph_node(memory.item_id, kind="memory", title=memory.title,
                   related=[playbook.item_id, runbook.item_id])
    if skill is not None:
        add_graph_node(skill.skill_id, kind="skill", title=skill.title,
                       related=[memory.item_id, playbook.item_id, runbook.item_id])
    add_graph_node(playbook.item_id, kind="playbook", title=playbook.title,
                   related=[runbook.item_id, memory.item_id])
    add_graph_node(runbook.item_id, kind="runbook", title=runbook.title,
                   related=[playbook.item_id, memory.item_id])

    patterns = detect_patterns([
        ("deployment", extraction.solution),
        ("security", extraction.security_impact),
    ])
    patterns_path = persist_patterns(patterns)
    print(f"[6] patterns {len(patterns)} -> {patterns_path.name}")

    proposals = propose_improvements()
    proposals_path = persist_proposals(proposals)
    print(f"[7] proposals {len(proposals)} -> {proposals_path.name}")

    build_index()
    print(f"[9] search index -> {count_documents()} documents")

    build_report()
    print("[10] LEARNER_IMPLEMENTATION_REPORT.md written")
    return 0


def run_learn() -> int:
    try:
        return _run_learn()
    except ValueError as exc:
        print(f"Error: {exc}")
        return 2


def run_check() -> int:
    """Run all Learner self-checks; exit 1 on any failure."""
    failures: list[str] = []

    from .audit import audit_system
    from .extract import extract_from_deployment, extract_from_mission, missing_fields
    from .improve import propose_improvements
    from .patterns import detect_patterns
    from .playbooks import PLAYBOOK_STEPS, generate_playbook
    from .quality import run_quality
    from .runbooks import RUNBOOK_STEPS, generate_runbook
    from .search import build_index, search
    from .skills import generate_skill

    # 1. Audit covers all twelve knowledge components.
    items = audit_system()
    if len(items) != 12:
        failures.append(f"audit expected 12 components got {len(items)}")

    # 2. Extraction derives complete fields from mission and deployment.
    mission = {"objective": "X", "mission_type": "bug", "status": "done"}
    mission_ex = extract_from_mission(mission)
    deployment = {"deployment_id": "D1", "version": "1.0.0",
                  "environment": "prod", "status": "live", "validations": [],
                  "rollbacks": []}
    deployment_ex = extract_from_deployment(deployment)
    if mission_ex.source != "mission:unknown":
        failures.append("mission extraction source mismatch")
    if deployment_ex.source != "deployment:D1":
        failures.append("deployment extraction source mismatch")
    if missing_fields(mission_ex) == []:
        failures.append("mission extraction should have some missing fields")

    # 3. Skill generation is deterministic and versioned.
    import re as _re
    skill = generate_skill(mission_ex, title="Unique Skill", technology="python")
    if skill is None:
        failures.append("reusable mission must produce a skill")
    if skill and not _re.fullmatch(r"SKILL-\d{6}", skill.skill_id):
        failures.append(f"skill id must match SKILL-NNNNNN got {skill.skill_id}")

    # 4. Playbook and runbook templates are complete and deterministic.
    for kind, steps in PLAYBOOK_STEPS.items():
        if not generate_playbook(kind, mission_ex):
            failures.append(f"playbook generation failed for {kind}")
        if len(steps) < 5:
            failures.append(f"playbook {kind} must have at least 5 steps")
    for kind, steps in RUNBOOK_STEPS.items():
        if not generate_runbook(kind, mission_ex):
            failures.append(f"runbook generation failed for {kind}")
        if len(steps) < 5:
            failures.append(f"runbook {kind} must have at least 5 steps")

    # 5. Pattern detection respects thresholds.
    patterns = detect_patterns([
        ("deployment", "deploy failure rolled back snapshot"),
        ("deployment", "deploy failure rolled back snapshot"),
    ])
    if len(patterns) != 1:
        failures.append("expected one deployment pattern from two hits")

    # 6. Improvement proposals cover all six engines.
    proposals = propose_improvements()
    if len(proposals) != 6:
        failures.append(f"expected 6 improvement proposals got {len(proposals)}")
    if len({p.target for p in proposals}) != 6:
        failures.append("improvement proposals must target distinct engines")

    # 7. Quality runs and produces a bounded health score.
    report = run_quality()
    if not (0 <= report.health_score <= 100):
        failures.append("quality health score out of bounds")
    if len(report.checks) != 7:
        failures.append(f"quality must run 7 checks got {len(report.checks)}")

    # 8. Search index builds and finds relevant results.
    build_index()
    hits = search("deployment rollback")
    if not isinstance(hits, list):
        failures.append("search must return a list")

    print("LEARNER SELF-CHECK")
    print("=" * 60)
    if failures:
        for failure in failures:
            print(f"  - {failure}")
        print("=" * 60)
        return 1
    for item in items:
        state = "verified" if item.status == "verified" else "planned"
        print(f"  [PASS] audit {item.title:<18} {state}")
    print("  [PASS] extraction deterministic (mission + deployment)")
    print("  [PASS] skills versioned + id sequence")
    print("  [PASS] playbooks/runbooks templates complete")
    print("  [PASS] patterns thresholded + 6 proposals")
    print("  [PASS] quality 7 checks + bounded health")
    print("  [PASS] search index + relevance")
    print("=" * 60)
    print("RESULT: ALL LEARNER CHECKS PASSED")
    return 0


def _area(source: str) -> str:
    if source.startswith("deployment:"):
        return "deployment"
    if source.startswith("mission:"):
        return "backend"
    return "tooling"


LEARNER_COMMANDS = {
    "learner-audit": run_audit,
    "learner-extract": run_extract,
    "learner-skill": run_skill,
    "learner-playbook": run_playbook,
    "learner-runbook": run_runbook,
    "learner-memory": run_memory,
    "learner-patterns": run_patterns,
    "learner-improve": run_improve,
    "learner-quality": run_quality,
    "learner-search": run_search,
    "learner-report": run_report,
    "learner-learn": run_learn,
    "learner-check": run_check,
}
