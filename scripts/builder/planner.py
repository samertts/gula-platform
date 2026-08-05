"""Phase 2 — Mission Planner.

Decompose a mission into a deterministic hierarchy:

    Program
      Phase
        Micro Phase
          Task (max 5 min / 50 files)
            Verification
            Checkpoint
              Completion

No task may exceed the Kernel phase budget (5 minutes / 50 files). The
planner always produces a plan whose tasks respect those limits.
"""

from __future__ import annotations

import uuid

from scripts.builder.analyzer import analyze
from scripts.builder.core import (
    MAX_TASK_FILES,
    MAX_TASK_MINUTES,
    MicroPhase,
    MissionAnalysis,
    MissionPlan,
    PlanPhase,
    PlanTask,
)

# Execution order shared by the Execution Engine (Phase 4).
EXECUTION_ORDER: tuple[str, ...] = (
    "analyze",
    "plan",
    "validate",
    "execute",
    "test",
    "verify",
    "document",
    "knowledge",
    "checkpoint",
    "continue",
)

PHASE_NAMES: dict[str, str] = {
    "analyze": "Analyze",
    "plan": "Plan",
    "validate": "Validate",
    "execute": "Implement",
    "test": "Test",
    "verify": "Verify",
    "document": "Document",
    "knowledge": "Update Knowledge",
    "checkpoint": "Checkpoint",
    "continue": "Continue",
}

# Baseline task minutes per execution step (sum <= typical budget).
PHASE_MINUTES: dict[str, int] = {
    "analyze": 2,
    "plan": 2,
    "validate": 1,
    "execute": 3,
    "test": 2,
    "verify": 1,
    "document": 2,
    "knowledge": 2,
    "checkpoint": 1,
    "continue": 1,
}

# Verification per execution step.
PHASE_VERIFICATION: dict[str, str] = {
    "analyze": "analysis produced with non-empty type/risk/complexity",
    "plan": "plan passes budget validation (<=5 min and <=50 files per task)",
    "validate": "plan meets constraints; dependencies resolved",
    "execute": "changed files present; no broken imports",
    "test": "tests run and pass",
    "verify": "verification strategy from analysis satisfied",
    "document": "documentation updated for the change",
    "knowledge": "knowledge system updated (registry/index)",
    "checkpoint": "checkpoint written to disk",
    "continue": "next step scheduled or mission marked complete",
}

# Expected file count per execution step.
PHASE_FILES: dict[str, int] = {
    "analyze": 1,
    "plan": 1,
    "validate": 1,
    "execute": 8,
    "test": 3,
    "verify": 1,
    "document": 2,
    "knowledge": 2,
    "checkpoint": 1,
    "continue": 1,
}

# Remaining steps after the current phase (used for cycle detection).
STEP_ORDER: dict[str, int] = {step: idx for idx, step in enumerate(EXECUTION_ORDER)}


def decompose(analysis: MissionAnalysis, plan_id: str | None = None) -> MissionPlan:
    """Split a mission into Program -> Phase -> Micro Phase -> Task."""
    mission_id = analysis.mission_id
    phases: list[PlanPhase] = []
    for step in EXECUTION_ORDER:
        micro_id = f"MICRO-{plan_id or mission_id}-{STEP_ORDER[step]}".upper()
        task = PlanTask(
            task_id=f"TASK-{uuid.uuid4().hex[:8].upper()}",
            name=PHASE_NAMES[step],
            estimated_minutes=PHASE_MINUTES[step],
            estimated_files=PHASE_FILES[step],
            verification=PHASE_VERIFICATION[step],
            checkpoint=f"step:{step}",
            status="pending",
        )
        microphase = MicroPhase(micro_id=micro_id, name=PHASE_NAMES[step], tasks=[task])
        phases.append(
            PlanPhase(phase_id=f"PHASE-{STEP_ORDER[step] + 1}", name=PHASE_NAMES[step], microphases=[microphase])
        )
    return MissionPlan(
        plan_id=plan_id or f"PLN-{uuid.uuid4().hex[:8].upper()}",
        mission_id=mission_id,
        program=f"{analysis.mission_type}-program",
        phases=phases,
    )


def budget_violations(plan: MissionPlan) -> list[str]:
    """Return every task that exceeds the 5-minute / 50-file budget."""
    violations: list[str] = []
    for task in plan.all_tasks():
        if task.estimated_minutes > MAX_TASK_MINUTES:
            violations.append(f"{task.task_id}: {task.estimated_minutes} min > {MAX_TASK_MINUTES}")
        if task.estimated_files > MAX_TASK_FILES:
            violations.append(f"{task.task_id}: {task.estimated_files} files > {MAX_TASK_FILES}")
    return violations


def is_within_budget(plan: MissionPlan) -> bool:
    """True when every task respects the phase budget."""
    return not budget_violations(plan)


def total_minutes(plan: MissionPlan) -> int:
    return sum(t.estimated_minutes for t in plan.all_tasks())


def total_files(plan: MissionPlan) -> int:
    return sum(t.estimated_files for t in plan.all_tasks())


def plan_mission(objective: str, plan_id: str | None = None) -> tuple[MissionAnalysis, MissionPlan]:
    """Analyze then plan a free-form objective."""
    analysis = analyze(objective)
    plan = decompose(analysis, plan_id)
    return analysis, plan


def describe_plan(plan: MissionPlan) -> str:
    """Render a compact human summary of the plan."""
    lines = [f"{plan.plan_id} ({plan.program}): {len(plan.phases)} phases"]
    for phase in plan.phases:
        for micro in phase.microphases:
            for task in micro.tasks:
                lines.append(
                    f"  {phase.phase_id} > {micro.micro_id} > {task.task_id} "
                    f"{task.name} ({task.estimated_minutes}min/{task.estimated_files}files)"
                )
    lines.append(
        f"budget: {total_minutes(plan)}min / {total_files(plan)}files "
        f"[{'PASS' if is_within_budget(plan) else 'FAIL'}]"
    )
    return "\n".join(lines)
