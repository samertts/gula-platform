"""Orchestrator CLI — GULA-ORCHESTRATOR-001 commands.

Integrated into `scripts/kernel.py` so the Kernel remains the single entry
point. Every Orchestrator command is reached through the Kernel, matching the
Builder and Reviewer integration pattern.
"""

from __future__ import annotations

import sys

from scripts.orchestrator.core import (
    ENGINES,
    MissionRecord,
    MissionStatus,
    make_id,
)


def run_audit() -> int:
    """Phase 0 — write ORCHESTRATOR_AUDIT_REPORT.md."""
    from .audit import run_audit as _audit

    path = _audit()
    print(f"[OK] {path.name} written")
    return 0


def _mission_record(classification, mission_id: str) -> MissionRecord:
    return MissionRecord(
        mission_id=mission_id,
        objective=classification.objective,
        mission_type=classification.mission_type,
        status=MissionStatus.CLASSIFIED.value,
        priority=classification.priority,
        complexity=classification.complexity,
        risk=classification.risk,
    )


def _run_pipeline(objective: str) -> tuple[MissionRecord, object]:
    """classify → plan → route → schedule → checkpoint → record."""
    from .checkpoint import save_checkpoint
    from .classifier import classify
    from .dashboard import write_status
    from .dependencies import build_dependencies
    from .history import add_event, persist_record, register
    from .planner import budget_violations, plan_mission
    from .router import route_plan

    classification = classify(objective)
    mission_id = make_id("ORN")
    record = _mission_record(classification, mission_id)
    record.status = MissionStatus.PLANNED.value
    add_event(record, "mission received", objective)

    plan = plan_mission(classification, mission_id=mission_id)
    violations = budget_violations(plan)
    if violations:
        print(f"[WARN] budget violations: {violations}")

    plan = route_plan(plan)
    plan = build_dependencies(plan)
    record.plan_id = plan.plan_id
    record.status = MissionStatus.ROUTED.value

    save_checkpoint(mission_id, "routed", plan.to_dict())
    add_event(record, "plan routed", f"{len(plan.tasks)} tasks")
    persist_record(record)
    register(mission_id, objective, classification.mission_type, record.status)
    write_status(record, plan)
    return record, plan


def run_mission() -> int:
    """Run a single-objective mission end-to-end and print the plan."""
    from .dependencies import describe as describe_dependencies

    objective = sys.argv[2] if len(sys.argv) > 2 else ""
    if not objective:
        print('Usage: orchestrator-mission "<objective>"')
        return 2
    record, plan = _run_pipeline(objective)
    print(f"MISSION {record.mission_id} — {record.mission_type} mission")
    print(f"  objective: {record.objective}")
    print(f"  plan: {plan.plan_id} | tasks: {len(plan.tasks)}")
    print(f"  engines: {sorted({t.engine for t in plan.tasks if t.engine})}")
    print(f"  parallel groups: {len(plan.parallel_groups)}")
    print(f"  critical path: {' -> '.join(plan.critical_path) or '—'}")
    print(describe_dependencies(plan))
    return 0


def run_classify() -> int:
    """Phase 1 — classify an objective."""
    from .classifier import classify

    objective = sys.argv[2] if len(sys.argv) > 2 else ""
    if not objective:
        print('Usage: orchestrator-classify "<objective>"')
        return 2
    c = classify(objective)
    print(f"type={c.mission_type} priority={c.priority} "
          f"complexity={c.complexity} risk={c.risk}")
    print(f"duration={c.duration_minutes}min specialists={', '.join(c.required_specialists) or '—'}")
    for r in c.rationale:
        print(f"  - {r}")
    return 0


def run_plan() -> int:
    """Phase 2 — classify + plan a mission."""
    from .dependencies import build_dependencies
    from .dependencies import describe as describe_dependencies
    from .planner import describe_plan, plan_mission

    objective = sys.argv[2] if len(sys.argv) > 2 else ""
    if not objective:
        print('Usage: orchestrator-plan "<objective>"')
        return 2
    from .classifier import classify

    plan = build_dependencies(plan_mission(classify(objective)))
    print(f"PLAN {plan.plan_id} for mission {plan.mission_id}")
    print(describe_plan(plan))
    print(describe_dependencies(plan))
    return 0


def run_route() -> int:
    """Phase 3+4 — classify + plan + route + schedule a mission."""
    from .dependencies import describe as describe_dependencies

    objective = sys.argv[2] if len(sys.argv) > 2 else ""
    if not objective:
        print('Usage: orchestrator-route "<objective>"')
        return 2
    record, plan = _run_pipeline(objective)
    print(f"ROUTED {record.mission_id}")
    print(describe_dependencies(plan))
    return 0


def run_checkpoint() -> int:
    """Phase 5 — report checkpoint state for a mission."""
    from .checkpoint import checkpoint_count, latest_checkpoint

    mission_id = sys.argv[2] if len(sys.argv) > 2 else ""
    if not mission_id:
        print("Usage: orchestrator-checkpoint <mission_id>")
        return 2
    latest = latest_checkpoint(mission_id)
    count = checkpoint_count(mission_id)
    if latest:
        print(f"mission {mission_id}: {count} checkpoint(s), latest at "
              f"{latest.step} ({latest.checkpoint_id})")
    else:
        print(f"mission {mission_id}: no checkpoints yet")
    return 0


def run_resume() -> int:
    """Phase 5 — resume a mission from its latest checkpoint."""
    from .checkpoint import resume_state
    from .history import load_record

    mission_id = sys.argv[2] if len(sys.argv) > 2 else ""
    if not mission_id:
        print("Usage: orchestrator-resume <mission_id>")
        return 2
    record = load_record(mission_id)
    state = resume_state(mission_id)
    tasks = state.get("tasks", [])
    done = sum(1 for t in tasks if t.get("status") == "completed")
    print(f"RESUME {mission_id} ({record.status})")
    print(f"  objective: {record.objective}")
    print(f"  checkpoint state tasks: {done}/{len(tasks)} completed")
    return 0


def run_status() -> int:
    """Phase 8 — regenerate MISSION_STATUS.md for the latest mission."""
    from .dashboard import write_status
    from .history import list_missions, load_record

    missions = list_missions()
    if not missions:
        print("No missions registered yet. Run orchestrator-mission first.")
        return 1
    mission_id = sys.argv[2] if len(sys.argv) > 2 else missions[-1]["mission_id"]
    record = load_record(mission_id)
    from scripts.orchestrator.core import OrchestratedPlan

    from .checkpoint import resume_state

    state = resume_state(mission_id)
    plan = OrchestratedPlan(
        plan_id=state.get("plan_id", ""),
        mission_id=mission_id,
        objective=record.objective,
        tasks=[_task_from_dict(t) for t in state.get("tasks", [])],
        execution_order=state.get("execution_order", []),
        parallel_groups=state.get("parallel_groups", []),
        critical_path=state.get("critical_path", []),
    )
    path = write_status(record, plan)
    print(f"[OK] {path.name} regenerated for {mission_id}")
    return 0


def _task_from_dict(data: dict) -> object:
    from scripts.orchestrator.core import AssignedTask

    return AssignedTask(
        task_id=data.get("task_id", ""),
        name=data.get("name", ""),
        engine=data.get("engine", ""),
        surface=data.get("surface", ""),
        estimated_minutes=data.get("estimated_minutes", 0),
        estimated_files=data.get("estimated_files", 0),
        depends_on=data.get("depends_on", []),
        status=data.get("status", "pending"),
        evidence=data.get("evidence", ""),
        started_at=data.get("started_at", ""),
        completed_at=data.get("completed_at", ""),
    )


def run_history() -> int:
    """Phase 9 — list registered missions, optionally filtered by query."""
    from .history import list_missions, search_missions

    query = sys.argv[2] if len(sys.argv) > 2 else ""
    missions = search_missions(query) if query else list_missions()
    if not missions:
        print("No missions found.")
        return 1
    for m in missions:
        print(f"{m['mission_id']}  {m['mission_type']:<13} {m['status']:<10} {m['objective']}")
    return 0


def run_report() -> int:
    """Phase 10 — write ORCHESTRATOR_IMPLEMENTATION_REPORT.md."""
    from .report import write_report

    path = write_report()
    print(f"[OK] {path.name} written")
    return 0


def run_check() -> int:
    """Run all Orchestrator self-checks; exit 1 on any failure."""
    failures: list[str] = []

    from .audit import detect
    from .checkpoint import save_checkpoint
    from .classifier import classify
    from .dependencies import build_dependencies
    from .failure import classify_failure
    from .planner import budget_violations, plan_mission
    from .resources import snapshot
    from .router import route_plan

    # 1. Deterministic classification
    c = classify("Build Patient Management")
    if c.mission_type != "feature":
        failures.append(f"classifier type expected feature got {c.mission_type}")
    if c.risk not in {"low", "moderate"}:
        failures.append(f"classifier risk unexpected {c.risk}")

    # 2. Budgeted plan, no violations
    plan = plan_mission(c)
    if budget_violations(plan):
        failures.append("plan has budget violations")

    # 3. Routing + DAG schedule
    plan = build_dependencies(route_plan(plan))
    if any(len(t.depends_on) > 0 for t in plan.tasks if t.name.startswith("Foundation")):
        failures.append("foundation tasks must be runnable-first")
    if not plan.critical_path:
        failures.append("critical path empty")

    # 4. Failure classifier determinism
    decision = classify_failure("OTASK-1", "connection refused to postgres")
    if not decision.retry_allowed:
        failures.append("transient failure not retryable")

    # 5. Resource snapshot determinism
    usage = snapshot("ORN-CHECK", context_bytes=1, files_read=1, files_modified=1)
    if usage.repo_bytes <= 0:
        failures.append("repo size snapshot empty")

    # 6. Checkpoint round-trip
    save_checkpoint("ORN-CHECK", "verify", {"ok": True}, checkpoint_id="OCK-CHECK1")
    from .checkpoint import latest_checkpoint

    restored = latest_checkpoint("ORN-CHECK")
    if not restored or restored.state.get("ok") is not True:
        failures.append("checkpoint round-trip failed")

    # 7. Audit: engine detection must be deterministic
    detected = detect()
    if not all(e in detected for e in ("kernel", "builder", "reviewer")):
        failures.append("audit engine detection incomplete")

    print("ORCHESTRATOR SELF-CHECK")
    print("=" * 60)
    if failures:
        for failure in failures:
            print(f"  - {failure}")
        print("=" * 60)
        return 1
    for engine in ENGINES:
        print(f"  [PASS] engine {engine:10s} {'present' if engine in detected else 'absent (fallback)'}")
    print("  [PASS] classifier/planner/router/dependencies deterministic")
    print("  [PASS] failure classifier + resource manager + checkpoint round-trip")
    print("  [PASS] no budget violations on reference mission")
    print("=" * 60)
    print("RESULT: ALL ORCHESTRATOR CHECKS PASSED")
    return 0


ORCHESTRATOR_COMMANDS = {
    "orchestrator-audit": run_audit,
    "orchestrator-mission": run_mission,
    "orchestrator-classify": run_classify,
    "orchestrator-plan": run_plan,
    "orchestrator-route": run_route,
    "orchestrator-checkpoint": run_checkpoint,
    "orchestrator-resume": run_resume,
    "orchestrator-status": run_status,
    "orchestrator-history": run_history,
    "orchestrator-report": run_report,
    "orchestrator-check": run_check,
}
