"""Phase 4 — Mission Scheduler.

Priority queue, mission queue, dependency graph, execution graph, critical
path, parallel execution, task ordering, preemption, and fair scheduling.
Deterministic ordering guarantees reproducible mission execution.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field

from .core import Task, utcnow


@dataclass(order=True)
class _PriorityEntry:
    priority: int
    seq: int
    task: Task = field(compare=False)


class PriorityQueue:
    """A max-priority queue (higher priority number dequeues first)."""

    def __init__(self) -> None:
        self._heap: list[_PriorityEntry] = []
        self._seq = 0

    def push(self, task: Task) -> None:
        self._seq += 1
        heapq.heappush(self._heap, _PriorityEntry(-task.priority, self._seq, task))

    def pop(self) -> Task | None:
        if not self._heap:
            return None
        return heapq.heappop(self._heap).task

    def peek(self) -> Task | None:
        return self._heap[0].task if self._heap else None

    def __len__(self) -> int:
        return len(self._heap)

    def drain(self) -> list[Task]:
        order: list[Task] = []
        while (task := self.pop()) is not None:
            order.append(task)
        return order


def _build_graph(tasks: list[Task]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Build (dependencies, dependents) adjacency maps."""
    deps: dict[str, set[str]] = {t.task_id: set(t.dependencies) for t in tasks}
    dependents: dict[str, set[str]] = {t.task_id: set() for t in tasks}
    for task in tasks:
        for dep in task.dependencies:
            dependents.setdefault(dep, set()).add(task.task_id)
    return deps, dependents


def find_cycle(tasks: list[Task]) -> list[str]:
    """Return the first dependency cycle found, or an empty list."""
    deps, _ = _build_graph(tasks)
    visited: dict[str, int] = {}  # 0 = visiting, 1 = done
    stack: list[str] = []
    cycle: list[str] = []

    def visit(node: str) -> bool:
        visited[node] = 0
        stack.append(node)
        for neighbor in deps.get(node, ()):
            if neighbor not in deps:
                continue
            if visited.get(neighbor) == 0:
                cycle.extend([*stack[stack.index(neighbor):], neighbor])
                return True
            if visited.get(neighbor) == 1:
                continue
            if visit(neighbor):
                return True
        stack.pop()
        visited[node] = 1
        return False

    for task in tasks:
        if task.task_id not in visited and visit(task.task_id):
            return cycle
    return []


def execution_layers(tasks: list[Task]) -> list[list[str]]:
    """Topological layers: tasks in the same layer can run in parallel.

    Raises ValueError on a dependency cycle.
    """
    cycle = find_cycle(tasks)
    if cycle:
        raise ValueError(f"Dependency cycle detected: {' -> '.join(cycle)}")
    deps, dependents = _build_graph(tasks)
    ready = {t for t in deps if not deps[t]}
    layers: list[list[str]] = []
    while ready:
        layer = sorted(ready)
        layers.append(layer)
        next_ready: set[str] = set()
        for task_id in layer:
            for dependent in dependents.get(task_id, ()):
                deps[dependent].discard(task_id)
                if not deps[dependent]:
                    next_ready.add(dependent)
        ready = next_ready
    if sum(len(layer) for layer in layers) != len(tasks):
        raise ValueError("Not all tasks schedulable; cycle present")
    return layers


def critical_path(tasks: list[Task]) -> list[str]:
    """Return the critical path (longest duration chain) of the mission.

    Uses the longest-path algorithm on the task DAG where edge weights are
    the duration of the *predecessor* task. Deterministic tie-breaking by
    task id.
    """
    layers = execution_layers(tasks)
    duration = {t.task_id: t.estimated_minutes for t in tasks}
    _deps, dependents = _build_graph(tasks)
    longest: dict[str, float] = {t.task_id: duration[t.task_id] for t in tasks}
    prev: dict[str, str] = {}
    for layer in layers:
        for task_id in layer:
            for dependent in sorted(dependents.get(task_id, ())):
                candidate = longest[task_id] + duration[dependent]
                if candidate > longest[dependent]:
                    longest[dependent] = candidate
                    prev[dependent] = task_id

    end = max(tasks, key=lambda t: longest[t.task_id])
    path: list[str] = []
    current = end.task_id
    while current:
        path.append(current)
        current = prev.get(current, "")
    return list(reversed(path))


def order_tasks(tasks: list[Task]) -> list[Task]:
    """Deterministic execution order: critical path first, then topo layers.

    Returns tasks ordered by (layer index, -priority, task_id).
    """
    layers = execution_layers(tasks)
    layer_index = {task_id: i for i, layer in enumerate(layers) for task_id in layer}
    priority = {t.task_id: t.priority for t in tasks}
    return sorted(tasks, key=lambda t: (layer_index[t.task_id], -priority[t.task_id], t.task_id))


def fair_schedule(tasks: list[Task]) -> list[Task]:
    """Round-robin scheduling across engines to guarantee fairness.

    Tasks are grouped by engine, ordered by (-priority, task_id) within each
    group, then interleaved engine by engine. This prevents one engine from
    starving the mission queue.
    """
    groups: dict[str, list[Task]] = {}
    for task in sorted(tasks, key=lambda t: (-t.priority, t.task_id)):
        groups.setdefault(task.engine, []).append(task)
    schedule: list[Task] = []
    while groups:
        for engine in sorted(groups):
            tasks_for_engine = groups[engine]
            if not tasks_for_engine:
                continue
            schedule.append(tasks_for_engine.pop(0))
            if not tasks_for_engine:
                groups.pop(engine)
    return schedule


def mission_schedule(mission_id: str, tasks: list[Task]) -> dict[str, object]:
    """Build the complete mission schedule (Phase 4 deliverables)."""
    return {
        "mission_id": mission_id,
        "generated_at": utcnow(),
        "mission_queue": [t.task_id for t in sorted(tasks, key=lambda t: -t.priority)],
        "dependency_graph": {t.task_id: list(t.dependencies) for t in tasks},
        "execution_graph": execution_layers(tasks),
        "critical_path": critical_path(tasks),
        "task_ordering": [t.task_id for t in order_tasks(tasks)],
        "fair_schedule": [t.task_id for t in fair_schedule(tasks)],
        "preemptible": [t.task_id for t in tasks if t.priority <= 1],
        "task_count": len(tasks),
        "status": "ready" if not find_cycle(tasks) else "cycle-detected",
    }
