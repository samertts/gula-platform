"""Unit tests for GULA-BUILDER-001 Phase 2 — Mission Planner."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.builder.analyzer import analyze
from scripts.builder.core import MAX_TASK_FILES, MAX_TASK_MINUTES
from scripts.builder.planner import (
    EXECUTION_ORDER,
    PHASE_FILES,
    PHASE_MINUTES,
    PHASE_NAMES,
    budget_violations,
    decompose,
    describe_plan,
    is_within_budget,
    plan_mission,
    total_files,
    total_minutes,
)


class TestDecompose:
    def test_full_hierarchy(self):
        analysis = analyze("Build Patient Management")
        plan = decompose(analysis)
        assert plan.mission_id == analysis.mission_id
        assert plan.program == "feature-program"
        assert len(plan.phases) == len(EXECUTION_ORDER)

    def test_each_phase_has_microphase_and_task(self):
        analysis = analyze("Build Patient Management")
        plan = decompose(analysis)
        for phase in plan.phases:
            assert phase.microphases
            assert phase.microphases[0].tasks

    def test_phase_names_match_execution_order(self):
        analysis = analyze("Build Patient Management")
        plan = decompose(analysis)
        names = [phase.name for phase in plan.phases]
        assert names == [PHASE_NAMES[step] for step in EXECUTION_ORDER]

    def test_tasks_have_verification_and_checkpoint(self):
        analysis = analyze("Build Patient Management")
        plan = decompose(analysis)
        for task in plan.all_tasks():
            assert task.verification
            assert task.checkpoint

    def test_all_tasks_unique_ids(self):
        analysis = analyze("Build Patient Management")
        plan = decompose(analysis)
        ids = [task.task_id for task in plan.all_tasks()]
        assert len(ids) == len(set(ids))

    def test_to_dict_roundtrip(self):
        analysis = analyze("Build Patient Management")
        data = decompose(analysis).to_dict()
        assert data["program"] == "feature-program"
        assert len(data["phases"]) == 10


class TestBudget:
    def test_all_tasks_within_budget(self):
        analysis = analyze("Build Patient Management")
        plan = decompose(analysis)
        for task in plan.all_tasks():
            assert task.estimated_minutes <= MAX_TASK_MINUTES
            assert task.estimated_files <= MAX_TASK_FILES

    def test_no_violations(self):
        analysis = analyze("Build Patient Management")
        plan = decompose(analysis)
        assert budget_violations(plan) == []
        assert is_within_budget(plan)

    def test_phase_files_and_minutes_positive(self):
        for step in EXECUTION_ORDER:
            assert PHASE_MINUTES[step] > 0
            assert PHASE_FILES[step] > 0

    def test_totals(self):
        analysis = analyze("Build Patient Management")
        plan = decompose(analysis)
        assert total_minutes(plan) == sum(PHASE_MINUTES.values())
        assert total_files(plan) == sum(PHASE_FILES.values())


class TestPlanMission:
    def test_plan_mission_returns_pair(self):
        analysis, plan = plan_mission("Fix the login crash")
        assert analysis.mission_type == "bug"
        assert plan.mission_id == analysis.mission_id

    def test_custom_plan_id(self):
        _, plan = plan_mission("Build X", plan_id="PLN-TEST")
        assert plan.plan_id == "PLN-TEST"

    def test_describe_plan_contains_phases(self):
        _, plan = plan_mission("Build X")
        text = describe_plan(plan)
        assert "PHASE-1" in text
        assert "budget" in text

    def test_execution_order_complete(self):
        assert len(EXECUTION_ORDER) == 10
        assert EXECUTION_ORDER[0] == "analyze"
        assert EXECUTION_ORDER[-1] == "continue"
