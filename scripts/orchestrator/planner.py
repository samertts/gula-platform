"""Phase 2 — Mission Planner.

Convert every mission into Mission > Program > Phase > Micro Phase > Task >
Verification > Checkpoint > Completion. Every task respects the 5 minute /
50 file budget. Each task carries a surface so Phase 3 can route it to the
correct engine.
"""

from __future__ import annotations

from scripts.orchestrator.core import (
    MAX_TASK_FILES,
    MAX_TASK_MINUTES,
    AssignedTask,
    MissionClassification,
    OrchestratedPlan,
    make_id,
)

# Program templates per mission type: (phase, micro, task, surface, minutes, files).
# Surfaces map to engines in the Router (Phase 3).
PROGRAM_TEMPLATES: dict[str, tuple[tuple[str, str, str, str, int, int], ...]] = {
    "feature": (
        ("Foundation", "Contracts", "Review existing contracts for the capability", "architecture", 3, 5),
        ("Foundation", "Data Model", "Define or extend the data model", "database", 4, 8),
        ("Core", "Backend API", "Implement the backend API surface", "backend", 5, 25),
        ("Core", "Frontend UI", "Implement the frontend surface", "frontend", 5, 30),
        ("Integration", "End-to-end wiring", "Wire frontend to backend end-to-end", "backend", 4, 15),
        ("Verification", "Unit Tests", "Add unit tests for the new capability", "testing", 4, 10),
        ("Verification", "Review", "Review the change set before acceptance", "verification", 3, 3),
        ("Documentation", "Docs", "Document the feature for users and agents", "documentation", 3, 5),
        ("Knowledge", "Registry", "Register the capability in the knowledge system", "knowledge", 3, 2),
    ),
    "bug": (
        ("Diagnosis", "Reproduce", "Reproduce the defect with a failing test", "testing", 4, 5),
        ("Diagnosis", "Root Cause", "Isolate the root cause", "backend", 4, 10),
        ("Fix", "Patch", "Apply the minimal corrective patch", "backend", 4, 15),
        ("Verification", "Regression Test", "Add a regression test for the defect", "testing", 3, 5),
        ("Verification", "Review", "Review the fix for side effects", "verification", 3, 3),
        ("Documentation", "Knowledge", "Record the failure lesson", "knowledge", 2, 2),
    ),
    "refactor": (
        ("Analysis", "Inventory", "Map the code being refactored", "architecture", 4, 10),
        ("Extraction", "Extract Module", "Extract the module with no behavior change", "backend", 5, 30),
        ("Cleanup", "Remove Dead Code", "Remove dead code and obsolete references", "backend", 4, 25),
        ("Verification", "Suite", "Confirm the full suite passes", "testing", 4, 5),
        ("Verification", "Review", "Review the refactor", "verification", 3, 3),
    ),
    "deployment": (
        ("Preparation", "Environment", "Prepare the target environment", "deployment", 5, 10),
        ("Build", "Artifact", "Build and verify the artifact", "deployment", 5, 15),
        ("Rollout", "Release", "Roll out to the target environment", "deployment", 5, 15),
        ("Verification", "Health Check", "Verify health checks and rollback path", "verification", 3, 5),
        ("Documentation", "Runbook", "Record the deployment in the runbook", "knowledge", 2, 2),
    ),
    "security": (
        ("Assessment", "Threat Model", "Scope the security posture", "security", 4, 10),
        ("Hardening", "Remediation", "Apply the security fix", "security", 5, 25),
        ("Hardening", "Test", "Prove the fix blocks the attack", "testing", 4, 10),
        ("Verification", "Review", "Security review of the change", "verification", 4, 3),
        ("Documentation", "Advisory", "Record the advisory", "knowledge", 2, 2),
    ),
    "performance": (
        ("Baseline", "Benchmark", "Benchmark the current behavior", "optimization", 5, 10),
        ("Optimization", "Optimize", "Apply the optimization", "optimization", 5, 25),
        ("Verification", "Compare", "Compare against baseline", "optimization", 4, 5),
        ("Verification", "Review", "Review the optimization", "verification", 3, 3),
    ),
    "architecture": (
        ("Design", "ADR", "Write the architecture decision record", "architecture", 4, 2),
        ("Design", "Contract", "Define the contracts and boundaries", "architecture", 5, 15),
        ("Implementation", "Apply", "Apply the architectural change", "backend", 5, 30),
        ("Verification", "Review", "Review against the ADR", "verification", 4, 3),
    ),
    "documentation": (
        ("Capture", "Author", "Author the documentation", "documentation", 5, 20),
        ("Integrate", "Link", "Link the documentation into the knowledge system", "knowledge", 3, 5),
        ("Verification", "Review", "Review for accuracy", "verification", 2, 2),
    ),
    "knowledge": (
        ("Extract", "Learn", "Extract the lesson or skill", "knowledge", 4, 10),
        ("Persist", "Index", "Persist and index the knowledge", "knowledge", 4, 8),
        ("Verification", "Check", "Verify the knowledge is discoverable", "verification", 2, 2),
    ),
    "infrastructure": (
        ("Provision", "Infra Change", "Apply the infrastructure change", "infrastructure", 5, 20),
        ("Integration", "Wire", "Wire services to the change", "deployment", 5, 20),
        ("Verification", "Verify", "Verify the infrastructure", "verification", 3, 5),
    ),
    "testing": (
        ("Plan", "Coverage Map", "Map the untested surface", "testing", 3, 10),
        ("Author", "Write Tests", "Author the test suite", "testing", 5, 40),
        ("Verify", "Run", "Run and fix the suite", "testing", 4, 10),
        ("Review", "Review", "Review test quality", "verification", 2, 3),
    ),
    "research": (
        ("Investigate", "Survey", "Survey the research question", "research", 5, 20),
        ("Analyze", "Analyze", "Analyze findings and alternatives", "research", 5, 15),
        ("Report", "Write Up", "Write up the findings", "documentation", 4, 10),
    ),
}


def plan_mission(
    classification: MissionClassification,
    *,
    mission_id: str | None = None,
    plan_id: str | None = None,
    program: str = "GULA Engineering Program",
) -> OrchestratedPlan:
    """Decompose a classification into a budgeted, surfaced plan."""
    tasks: list[AssignedTask] = []
    for phase_name, _micro_name, task_name, surface, minutes, files in PROGRAM_TEMPLATES.get(
        classification.mission_type, PROGRAM_TEMPLATES["research"]
    ):
        tasks.append(AssignedTask(
            task_id=make_id("OTASK"),
            name=f"[{phase_name}] {task_name}",
            engine="",  # assigned by the Router (Phase 3)
            surface=surface,
            estimated_minutes=minutes,
            estimated_files=files,
        ))
    return OrchestratedPlan(
        plan_id=plan_id or make_id("OPL"),
        mission_id=mission_id or make_id("ORN"),
        objective=classification.objective,
        program=program,
        tasks=tasks,
    )


def budget_violations(plan: OrchestratedPlan) -> list[str]:
    """Return budget violations (max 5 min / 50 files per task)."""
    violations: list[str] = []
    for task in plan.tasks:
        if task.estimated_minutes > MAX_TASK_MINUTES:
            violations.append(
                f"{task.task_id}: {task.estimated_minutes} min > {MAX_TASK_MINUTES}"
            )
        if task.estimated_files > MAX_TASK_FILES:
            violations.append(
                f"{task.task_id}: {task.estimated_files} files > {MAX_TASK_FILES}"
            )
    return violations


def describe_plan(plan: OrchestratedPlan) -> str:
    lines = [
        f"plan {plan.plan_id} | mission {plan.mission_id} | {plan.objective}",
        f"program: {plan.program}",
    ]
    for task in plan.tasks:
        lines.append(
            f"  {task.task_id} {task.surface:<14} {task.estimated_minutes:>2}min "
            f"{task.estimated_files:>2}files  {task.name}"
        )
    return "\n".join(lines)
