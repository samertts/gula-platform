"""Phase 4 — Dependency Engine.

Determine execution order, blocking tasks, parallel tasks, critical path, and
the task graph. Tasks in the same phase on different surfaces are independent
and can run in parallel; each phase blocks the next. The engine never assumes
a phase boundary ordering — it computes it from the tasks.
"""

from __future__ import annotations

import re
from collections import defaultdict

from scripts.orchestrator.core import OrchestratedPlan, TaskStatus


def _phase_of(task_name: str) -> str:
    match = re.match(r"\[([^\]]+)\]", task_name)
    return match.group(1) if match else "General"


def build_dependencies(plan: OrchestratedPlan) -> OrchestratedPlan:
    """Populate depends_on, execution_order, parallel_groups, critical_path."""
    phased: dict[str, list] = defaultdict(list)
    order_seen: list[str] = []
    for task in plan.tasks:
        phase = _phase_of(task.name)
        phased[phase].append(task)
        if phase not in order_seen:
            order_seen.append(phase)

    # Within a phase, same-surface tasks are chained; different surfaces are
    # independent (parallel). Every task in a phase depends on the last task
    # of the previous phase, so phases execute in order but intra-phase tasks
    # remain parallel.
    phase_last: dict[str, str | None] = {}
    for phase in order_seen:
        tasks = phased.get(phase, [])
        prev_last = _previous_phase_last(order_seen, phase, phase_last)
        for i, task in enumerate(tasks):
            deps: list[str] = []
            if i > 0 and tasks[i - 1].surface == task.surface:
                deps.append(tasks[i - 1].task_id)
            if prev_last:
                deps.append(prev_last)
            task.depends_on = list(dict.fromkeys(d for d in deps if d != task.task_id))
        phase_last[phase] = tasks[-1].task_id

    plan.execution_order = [t.task_id for t in plan.tasks]

    # Parallel groups: independent tasks within each phase.
    groups: list[list[str]] = []
    for tasks in phased.values():
        group = [t.task_id for t in tasks]
        if len(group) > 1:
            groups.append(group)
    plan.parallel_groups = groups

    plan.critical_path = _critical_path(plan, order_seen)
    return plan


def _previous_phase_last(order_seen: list[str], phase: str, phase_last: dict[str, str | None]) -> str | None:
    if phase not in order_seen:
        return None
    idx = order_seen.index(phase)
    if idx == 0:
        return None
    for prev in reversed(order_seen[:idx]):
        if phase_last.get(prev):
            return phase_last[prev]
    return None


def _critical_path(plan: OrchestratedPlan, phases: list[str]) -> list[str]:
    """Longest estimated chain of tasks across the phase sequence."""
    if not plan.tasks:
        return []
    by_phase: dict[str, list] = defaultdict(list)
    for task in plan.tasks:
        by_phase[_phase_of(task.name)].append(task)

    path: list[str] = []
    for phase in phases:
        tasks = by_phase.get(phase, [])
        if not tasks:
            continue
        longest = max(tasks, key=lambda t: t.estimated_minutes)
        path.append(longest.task_id)
    return path


def blocking_tasks(plan: OrchestratedPlan) -> list[str]:
    """Tasks that other tasks depend on (in-degree > 0 targets)."""
    blocked: set[str] = set()
    for task in plan.tasks:
        for dep in task.depends_on:
            blocked.add(dep)
    return sorted(blocked)


def next_runnable(plan: OrchestratedPlan) -> list[str]:
    """Tasks whose dependencies are all completed (topologically ready)."""
    completed = {t.task_id for t in plan.tasks if t.status == TaskStatus.COMPLETED.value}
    ready: list[str] = []
    for task in plan.tasks:
        if task.status != TaskStatus.PENDING.value:
            continue
        if all(dep in completed for dep in task.depends_on):
            ready.append(task.task_id)
    return ready


def longest_path_minutes(plan: OrchestratedPlan) -> int:
    """Critical-path duration in minutes."""
    total = 0
    for task_id in plan.critical_path:
        for task in plan.tasks:
            if task.task_id == task_id:
                total += task.estimated_minutes
    return total


def build_graph(plan: OrchestratedPlan) -> dict[str, list[str]]:
    """Adjacency list: task_id -> list of task_ids it blocks."""
    graph: dict[str, list[str]] = {t.task_id: [] for t in plan.tasks}
    for task in plan.tasks:
        for dep in task.depends_on:
            if dep in graph:
                graph[dep].append(task.task_id)
    return graph


def describe(plan: OrchestratedPlan) -> str:
    """Human-readable schedule summary with parallel groups and critical path."""
    lines = [f"Schedule: {len(plan.tasks)} tasks, "
             f"{len(plan.parallel_groups)} parallel groups, "
             f"critical path {longest_path_minutes(plan)} minutes"]
    for group in plan.parallel_groups:
        names = []
        for task in plan.tasks:
            if task.task_id in group:
                names.append(f"{task.name} [{task.surface}]")
        lines.append(f"  parallel: {', '.join(names)}")
    if plan.critical_path:
        names = []
        for task_id in plan.critical_path:
            for task in plan.tasks:
                if task.task_id == task_id:
                    names.append(task.name)
        lines.append(f"  critical path: {' -> '.join(names)}")
    return "\n".join(lines)
