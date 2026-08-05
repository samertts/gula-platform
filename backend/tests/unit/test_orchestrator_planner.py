"""Unit tests for GULA-ORCHESTRATOR-001 — Phase 2 Planner."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.orchestrator.classifier import classify
from scripts.orchestrator.core import MAX_TASK_FILES, MAX_TASK_MINUTES
from scripts.orchestrator.planner import (
    budget_violations,
    describe_plan,
    plan_mission,
)


def _plan_for(objective: str):
    return plan_mission(classify(objective))


class TestPlanStructure:
    def test_plan_ids_assigned(self):
        plan = _plan_for("Build Patient Management")
        assert plan.plan_id.startswith("OPL-")
        assert plan.mission_id.startswith("ORN-")

    def test_objective_carried_through(self):
        plan = _plan_for("Build Patient Management")
        assert plan.objective == "Build Patient Management"

    def test_tasks_have_ids(self):
        plan = _plan_for("Build Patient Management")
        assert len(plan.tasks) > 0
        for task in plan.tasks:
            assert task.task_id.startswith("OTASK-")

    def test_tasks_have_surface(self):
        plan = _plan_for("Build Patient Management")
        assert all(task.surface for task in plan.tasks)

    def test_tasks_have_estimates(self):
        plan = _plan_for("Build Patient Management")
        for task in plan.tasks:
            assert task.estimated_minutes > 0
            assert task.estimated_files > 0

    def test_feature_plan_has_nine_tasks(self):
        assert len(_plan_for("Build Patient Management").tasks) == 9


class TestBudget:
    def test_no_violations_on_reference_mission(self):
        plan = _plan_for("Build Patient Management")
        assert budget_violations(plan) == []

    def test_no_violations_on_security_mission(self):
        plan = _plan_for("Harden the authentication system")
        assert budget_violations(plan) == []

    def test_no_violations_on_research(self):
        plan = _plan_for("Investigate queue options")
        assert budget_violations(plan) == []

    def test_every_task_within_minute_budget(self):
        plan = _plan_for("Build Patient Management")
        for task in plan.tasks:
            assert task.estimated_minutes <= MAX_TASK_MINUTES

    def test_every_task_within_file_budget(self):
        plan = _plan_for("Build Patient Management")
        for task in plan.tasks:
            assert task.estimated_files <= MAX_TASK_FILES


class TestDescribe:
    def test_describe_plan_lists_tasks(self):
        plan = _plan_for("Build Patient Management")
        text = describe_plan(plan)
        assert plan.plan_id in text
        assert "GULA Engineering Program" in text

    def test_describe_mentions_surfaces(self):
        plan = _plan_for("Build Patient Management")
        assert "backend" in describe_plan(plan).lower()


class TestTemplates:
    def test_all_mission_types_produce_tasks(self):
        for objective, expected in [
            ("Build X", "feature"),
            ("Fix the crash", "bug"),
            ("Refactor the module", "refactor"),
            ("Deploy to staging", "deployment"),
            ("Harden auth", "security"),
            ("Improve latency", "performance"),
            ("Write an ADR for the module boundary", "architecture"),
            ("Document the API", "documentation"),
            ("Learn the lesson and index it", "knowledge"),
            ("Apply the docker change", "infrastructure"),
            ("Add coverage for the service", "testing"),
            ("Investigate the options", "research"),
        ]:
            plan = _plan_for(objective)
            assert len(plan.tasks) > 0, f"{expected} produced no tasks"
