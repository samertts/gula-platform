"""Unit tests for GULA-ORCHESTRATOR-001 — Phase 3 Router."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.orchestrator.classifier import classify
from scripts.orchestrator.planner import plan_mission
from scripts.orchestrator.router import route_plan


def _routed(objective: str):
    return route_plan(plan_mission(classify(objective)))


class TestRouting:
    def test_every_task_gets_an_engine(self):
        plan = _routed("Build Patient Management")
        assert all(task.engine for task in plan.tasks)

    def test_backend_surface_routes_to_builder(self):
        plan = _routed("Build Patient Management")
        for task in plan.tasks:
            if task.surface == "backend":
                assert task.engine == "builder"

    def test_verification_surface_routes_to_reviewer(self):
        plan = _routed("Build Patient Management")
        for task in plan.tasks:
            if task.surface == "verification":
                assert task.engine == "reviewer"

    def test_knowledge_surface_routes_to_learner(self):
        plan = _routed("Build Patient Management")
        for task in plan.tasks:
            if task.surface == "knowledge":
                assert task.engine == "learner"

    def test_feature_plan_uses_builder_reviewer_learner(self):
        plan = _routed("Build Patient Management")
        engines = {t.engine for t in plan.tasks}
        assert engines == {"builder", "reviewer", "learner"}

    def test_deployment_surface_falls_back_without_deployer(self):
        plan = route_plan(
            plan_mission(classify("Deploy the release to staging")),
            available={"builder", "reviewer", "learner", "kernel"},
        )
        engines = {t.engine for t in plan.tasks}
        assert "deployer" not in engines
        for task in plan.tasks:
            assert task.engine in {"builder", "reviewer", "learner", "kernel"}

    def test_available_engines_respected(self):
        plan = plan_mission(classify("Build Patient Management"))
        routed = route_plan(plan, available={"builder", "reviewer", "kernel"})
        engines = {t.engine for t in routed.tasks}
        assert engines <= {"builder", "reviewer", "kernel"}


class TestRoutingDeterminism:
    def test_router_is_deterministic(self):
        assert {t.engine for t in _routed("Build Patient Management").tasks} == {
            t.engine for t in _routed("Build Patient Management").tasks
        }
