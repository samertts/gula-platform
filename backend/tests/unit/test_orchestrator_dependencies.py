"""Unit tests for GULA-ORCHESTRATOR-001 — Phase 4 Dependency Engine."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.orchestrator.classifier import classify
from scripts.orchestrator.dependencies import (
    blocking_tasks,
    build_dependencies,
    build_graph,
    describe,
    longest_path_minutes,
    next_runnable,
)
from scripts.orchestrator.planner import plan_mission
from scripts.orchestrator.router import route_plan


def _scheduled(objective: str):
    plan = plan_mission(classify(objective))
    return build_dependencies(route_plan(plan))


class TestScheduling:
    def test_execution_order_matches_task_count(self):
        plan = _scheduled("Build Patient Management")
        assert len(plan.execution_order) == len(plan.tasks)

    def test_foundation_tasks_runnable_first(self):
        plan = _scheduled("Build Patient Management")
        for task in plan.tasks:
            if task.name.startswith("[Foundation]"):
                assert task.depends_on == []

    def test_core_backend_depends_on_foundation(self):
        plan = _scheduled("Build Patient Management")
        backend = next(t for t in plan.tasks if "[Core]" in t.name and t.surface == "backend")
        assert backend.depends_on

    def test_critical_path_nonempty(self):
        plan = _scheduled("Build Patient Management")
        assert plan.critical_path

    def test_critical_path_matches_expected_phases(self):
        plan = _scheduled("Build Patient Management")
        phases = [next(t.name for t in plan.tasks if t.task_id == tid).split("]")[0][1:]
                  for tid in plan.critical_path]
        assert phases == ["Foundation", "Core", "Integration", "Verification", "Documentation", "Knowledge"]

    def test_parallel_groups_nonempty(self):
        plan = _scheduled("Build Patient Management")
        assert plan.parallel_groups

    def test_longest_path_minutes_positive(self):
        plan = _scheduled("Build Patient Management")
        assert longest_path_minutes(plan) > 0


class TestGraph:
    def test_build_graph_returns_adjacency(self):
        plan = _scheduled("Build Patient Management")
        graph = build_graph(plan)
        assert set(graph) == {t.task_id for t in plan.tasks}
        for task in plan.tasks:
            for dep in task.depends_on:
                assert task.task_id in graph[dep]

    def test_blocking_tasks_subsets_all(self):
        plan = _scheduled("Build Patient Management")
        blockers = blocking_tasks(plan)
        assert all(b in {t.task_id for t in plan.tasks} for b in blockers)

    def test_next_runnable_starts_foundation(self):
        plan = _scheduled("Build Patient Management")
        ready = next_runnable(plan)
        assert ready
        for task in plan.tasks:
            if task.task_id in ready:
                assert all(
                    next(t for t in plan.tasks if t.task_id == dep).status == "completed"
                    for dep in task.depends_on
                )


class TestDescribe:
    def test_describe_lists_schedule(self):
        plan = _scheduled("Build Patient Management")
        text = describe(plan)
        assert "parallel" in text.lower()
        assert "critical path" in text.lower()

    def test_describe_mentions_parallel_surfaces(self):
        plan = _scheduled("Build Patient Management")
        text = describe(plan)
        assert "backend" in text
        assert "frontend" in text


class TestAllTemplates:
    def test_every_mission_type_schedules(self):
        for objective in [
            "Build X", "Fix the crash", "Refactor the module", "Deploy to staging",
            "Harden auth", "Improve latency", "Write an ADR for the module boundary",
            "Document the API", "Learn the lesson and index it", "Apply the docker change",
            "Add coverage for the service", "Investigate the options",
        ]:
            plan = _scheduled(objective)
            assert plan.execution_order, objective
            assert plan.critical_path, objective
