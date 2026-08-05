"""Unit tests for GULA-ORCHESTRATOR-001 — Phase 8 Mission Dashboard."""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.orchestrator.classifier import classify
from scripts.orchestrator.core import MissionRecord, TaskStatus
from scripts.orchestrator.dashboard import (
    compute_progress,
    current_phase,
    remaining_minutes,
    render,
    write_status,
)
from scripts.orchestrator.dependencies import build_dependencies
from scripts.orchestrator.planner import plan_mission
from scripts.orchestrator.router import route_plan


def _record_and_plan(completed: int = 0):
    plan = build_dependencies(route_plan(plan_mission(classify("Build Patient Management"))))
    for i in range(completed):
        plan.tasks[i].status = TaskStatus.COMPLETED.value
    record = MissionRecord(
        mission_id="ORN-DASH", objective="Build Patient Management",
        mission_type="feature", status="executing",
    )
    return record, plan


class TestComputeProgress:
    def test_zero_progress(self):
        record, plan = _record_and_plan()
        compute_progress(record, plan)
        assert record.progress_percent == 0.0

    def test_partial_progress(self):
        record, plan = _record_and_plan(completed=2)
        compute_progress(record, plan)
        assert 0.0 < record.progress_percent < 100.0

    def test_full_progress(self):
        record, plan = _record_and_plan()
        for task in plan.tasks:
            task.status = TaskStatus.COMPLETED.value
        compute_progress(record, plan)
        assert record.progress_percent == 100.0

    def test_counts_assigned(self):
        record, plan = _record_and_plan()
        compute_progress(record, plan)
        assert record.assigned_tasks == len(plan.tasks)

    def test_health_starts_full(self):
        record, plan = _record_and_plan()
        compute_progress(record, plan)
        assert record.health_score == 100.0

    def test_blocked_penalizes_health(self):
        record, plan = _record_and_plan()
        plan.tasks[0].status = TaskStatus.BLOCKED.value
        compute_progress(record, plan)
        assert record.health_score < 100.0
        assert record.blocked_tasks == 1


class TestHelpers:
    def test_remaining_minutes_counts_unfinished(self):
        _, plan = _record_and_plan(completed=1)
        total = sum(t.estimated_minutes for t in plan.tasks)
        assert remaining_minutes(plan) < total

    def test_remaining_minutes_zero_when_done(self):
        _, plan = _record_and_plan()
        for task in plan.tasks:
            task.status = TaskStatus.COMPLETED.value
        assert remaining_minutes(plan) == 0

    def test_current_phase_foundation_initially(self):
        _, plan = _record_and_plan()
        assert current_phase(plan) == "Foundation"

    def test_current_phase_moves_forward(self):
        _, plan = _record_and_plan(completed=2)
        assert current_phase(plan) == "Core"

    def test_current_phase_complete_when_done(self):
        _, plan = _record_and_plan()
        for task in plan.tasks:
            task.status = TaskStatus.COMPLETED.value
        assert current_phase(plan) == "Complete"


class TestRender:
    def test_render_contains_mission_header(self):
        record, plan = _record_and_plan()
        text = render(record, plan)
        assert record.mission_id in text
        assert "MISSION_STATUS" in text

    def test_render_lists_every_task(self):
        record, plan = _record_and_plan()
        text = render(record, plan)
        for task in plan.tasks:
            assert task.name in text

    def test_write_status_persists(self, tmp_path):
        record, plan = _record_and_plan()
        path = write_status(record, plan, tmp_path / "MISSION_STATUS.md")
        assert path.exists()
        assert record.progress_percent >= 0.0
