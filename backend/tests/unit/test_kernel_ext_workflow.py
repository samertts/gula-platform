"""Unit tests for GULA-KERNEL-EXT-001 Phase 6 — Workflow Engine."""

from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from scripts.kernel.ext.event_bus import EventBus
from scripts.kernel.ext.workflow import (
    STEP_KINDS,
    WORKFLOW_STATES,
    Workflow,
    WorkflowEngine,
    WorkflowError,
    WorkflowStep,
    _demo_workflow,
)


def _step(step_id: str = "s1", **overrides) -> WorkflowStep:
    base = {
        "id": step_id,
        "kind": "task",
        "description": "test step",
        "fn": lambda _ctx: None,
    }
    base.update(overrides)
    return WorkflowStep(**base)


def _workflow(**overrides) -> Workflow:
    base = {
        "id": "WF-100001",
        "name": "test workflow",
        "steps": [_step()],
    }
    base.update(overrides)
    return Workflow(**base)


class TestStep:
    def test_valid_task(self):
        assert _step().status == "pending"

    def test_task_requires_handler(self):
        with pytest.raises(WorkflowError):
            _step(fn=None)

    def test_approval_rejects_handler(self):
        with pytest.raises(WorkflowError):
            _step(kind="approval", fn=lambda _ctx: None)

    def test_approval_valid(self):
        step = _step(kind="approval", fn=None)
        assert step.kind == "approval"

    def test_bad_kind(self):
        with pytest.raises(WorkflowError):
            _step(kind="nope")

    def test_negative_retries(self):
        with pytest.raises(WorkflowError):
            _step(max_retries=-1)

    def test_step_kinds_valid(self):
        for kind in STEP_KINDS:
            fn = None if kind == "approval" else (lambda _ctx: None)
            step = _step(kind=kind, fn=fn)
            assert step.kind == kind


class TestWorkflow:
    def test_valid_workflow(self):
        assert _workflow().state == "pending"

    def test_bad_id(self):
        with pytest.raises(WorkflowError):
            _workflow(id="BAD-1")

    def test_duplicate_step_ids(self):
        with pytest.raises(WorkflowError):
            _workflow(steps=[_step("s1"), _step("s1")])

    def test_cycle_detected(self):
        with pytest.raises(WorkflowError):
            _workflow(steps=[
                _step("a", requires=["b"]),
                _step("b", requires=["a"]),
            ])

    def test_unknown_requirement(self):
        with pytest.raises(WorkflowError):
            _workflow(steps=[_step("a", requires=["ghost"])])

    def test_bad_state(self):
        with pytest.raises(WorkflowError):
            _workflow(state="bogus")

    def test_states_valid(self):
        for state in WORKFLOW_STATES:
            assert _workflow(state=state).state == state


class TestEngine:
    def test_register_and_run_task(self):
        engine = WorkflowEngine()
        workflow = engine.register(_workflow())
        engine.run(workflow.id)
        assert workflow.state == "completed"
        assert workflow.steps[0].status == "completed"

    def test_duplicate_register_raises(self):
        engine = WorkflowEngine()
        engine.register(_workflow())
        with pytest.raises(WorkflowError):
            engine.register(_workflow())

    def test_approval_gate_halts(self):
        engine = WorkflowEngine()
        workflow = engine.register(_workflow(steps=[
            _step("prep"),
            _step("review", kind="approval", fn=None, requires=["prep"]),
        ]))
        engine.run(workflow.id)
        assert workflow.state == "awaiting_approval"
        assert workflow.step("review").status == "awaiting_approval"

    def test_approval_gate_continues(self):
        engine = WorkflowEngine()
        workflow = engine.register(_workflow(steps=[
            _step("prep"),
            _step("review", kind="approval", fn=None, requires=["prep"]),
            _step("finalize", requires=["review"]),
        ]))
        engine.run(workflow.id)
        engine.approve(workflow.id, "review")
        assert workflow.state == "completed"
        assert workflow.step("finalize").status == "completed"

    def test_approve_non_approval_step(self):
        engine = WorkflowEngine()
        workflow = engine.register(_workflow())
        with pytest.raises(WorkflowError):
            engine.approve(workflow.id, "s1")

    def test_approve_wrong_state(self):
        engine = WorkflowEngine()
        workflow = engine.register(_workflow(steps=[
            _step("review", kind="approval", fn=None),
        ]))
        with pytest.raises(WorkflowError):
            engine.approve(workflow.id, "review")

    def test_retry_until_success(self):
        engine = WorkflowEngine()
        attempts = {"count": 0}

        def flaky(_ctx) -> None:
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise RuntimeError("transient")

        workflow = engine.register(_workflow(steps=[_step(fn=flaky, max_retries=3)]))
        engine.run(workflow.id)
        assert workflow.state == "completed"
        assert attempts["count"] == 3

    def test_retry_exhausted_fails(self):
        engine = WorkflowEngine()
        attempts = {"count": 0}

        def always_broken(_ctx) -> None:
            attempts["count"] += 1
            raise RuntimeError("boom")

        workflow = engine.register(_workflow(steps=[_step(fn=always_broken, max_retries=1)]))
        engine.run(workflow.id)
        assert workflow.state == "failed"
        assert workflow.steps[0].status == "failed"
        assert attempts["count"] == 2

    def test_cancel(self):
        engine = WorkflowEngine()
        workflow = engine.register(_workflow(steps=[
            _step("a"),
            _step("b", requires=["a"]),
        ]))
        engine.cancel(workflow.id)
        assert workflow.state == "rolled_back"

    def test_run_after_completed_raises(self):
        engine = WorkflowEngine()
        workflow = engine.register(_workflow())
        engine.run(workflow.id)
        with pytest.raises(WorkflowError):
            engine.run(workflow.id)

    def test_workflows_by_state(self):
        engine = WorkflowEngine()
        engine.register(_workflow())
        engine.register(_workflow(id="WF-100002"))
        engine.run("WF-100001")
        assert len(engine.workflows("completed")) == 1
        assert len(engine.workflows("pending")) == 1

    def test_emits_events_to_bus(self):
        bus = EventBus()
        engine = WorkflowEngine(event_bus=bus)
        workflow = engine.register(_workflow())
        engine.run(workflow.id)
        assert len(bus.events()) >= 1
        assert bus.events()[0].name == "workflow.WF-100001.completed"

    def test_history_recorded(self):
        engine = WorkflowEngine()
        workflow = engine.register(_workflow())
        engine.run(workflow.id)
        events = [h["event"] for h in engine.snapshot()["history"]]
        assert "registered" in events and "completed" in events

    def test_save_persists(self, tmp_path):
        engine = WorkflowEngine()
        workflow = engine.register(_workflow())
        engine.run(workflow.id)
        path = engine.save(tmp_path / "workflows.json")
        data = path.read_text(encoding="utf-8")
        assert "WF-100001" in data
        assert "completed" in data


class TestDemo:
    def test_demo_full_run(self):
        engine = WorkflowEngine()
        workflow = engine.register(_demo_workflow())
        engine.run(workflow.id)
        assert workflow.state == "awaiting_approval"
        engine.approve(workflow.id, "review")
        assert workflow.state == "completed"
