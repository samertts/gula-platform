"""GULA-KERNEL-EXT-001 Phase 6 — Workflow Engine.

AI-operational workflows for missions: sequential/parallel steps with
dependency ordering, approval gates, bounded retries, and rollback.
Per 18_WORKFLOW_CONSTITUTION: states are explicit and testable, workflow
state is persisted, exceptions (cancel/rollback) are first-class, and
workflows emit events on transitions (via the Phase 5 Event Bus).

Reuses Kernel scheduling (scripts/kernel/scheduler.py find_cycle) and
decision/approval semantics (governor/decision_governance.py); no I/O at
import time.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..core import utcnow
from ..scheduler import find_cycle
from .event_bus import Event, EventBus

WORKFLOW_DIR = ".ai/core/workflows/"

STEP_KINDS = ("task", "approval")
WORKFLOW_STATES = ("pending", "running", "awaiting_approval", "completed", "failed", "rolled_back")

StepFn = Callable[[dict[str, Any]], None]


class WorkflowError(Exception):
    """Raised for invalid workflows or execution failures."""


class _StepProxy:
    """Duck-typed proxy exposing the scheduler's expected task attributes."""

    def __init__(self, task_id: str, dependencies: list[str]) -> None:
        self.task_id = task_id
        self.dependencies = dependencies


def _cycle_names(steps: list[WorkflowStep]) -> list[str]:
    """Reuse Kernel scheduler cycle detection via duck-typed proxies."""
    return find_cycle([_StepProxy(s.id, s.requires) for s in steps])


@dataclass
class WorkflowStep:
    """One step of a workflow: a task or an approval gate."""

    id: str
    kind: str
    description: str
    fn: StepFn | None = None
    requires: list[str] = field(default_factory=list)
    max_retries: int = 0
    status: str = "pending"

    def __post_init__(self) -> None:
        if self.kind not in STEP_KINDS:
            raise WorkflowError(f"unknown step kind: {self.kind!r}")
        if self.kind == "task" and self.fn is None:
            raise WorkflowError(f"task step {self.id!r} requires a handler")
        if self.kind == "approval" and self.fn is not None:
            raise WorkflowError(f"approval step {self.id!r} must not have a handler")
        if self.max_retries < 0:
            raise WorkflowError(f"max_retries cannot be negative: {self.max_retries}")


@dataclass
class Workflow:
    """A versioned, resumable, auditable workflow."""

    id: str
    name: str
    steps: list[WorkflowStep]
    state: str = "pending"
    created_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.id.startswith("WF-"):
            raise WorkflowError(f"workflow id must start with WF-: {self.id!r}")
        if self.state not in WORKFLOW_STATES:
            raise WorkflowError(f"unknown workflow state: {self.state!r}")
        ids = [s.id for s in self.steps]
        if len(ids) != len(set(ids)):
            raise WorkflowError(f"duplicate step ids in workflow {self.id}")
        cycle = _cycle_names(self.steps)
        if cycle:
            raise WorkflowError(f"workflow {self.id} has dependency cycle: {cycle}")
        for step in self.steps:
            for required in step.requires:
                if required not in ids:
                    raise WorkflowError(
                        f"step {step.id} requires unknown step {required}"
                    )

    def step(self, step_id: str) -> WorkflowStep:
        for step in self.steps:
            if step.id == step_id:
                return step
        raise WorkflowError(f"unknown step {step_id!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "state": self.state,
            "steps": [
                {"id": s.id, "kind": s.kind, "description": s.description,
                 "requires": s.requires, "max_retries": s.max_retries, "status": s.status}
                for s in self.steps
            ],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class WorkflowEngine:
    """Executes workflows with dependency ordering, approval, retry, rollback."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._workflows: dict[str, Workflow] = {}
        self._history: list[dict[str, Any]] = []
        self.event_bus = event_bus

    def register(self, workflow: Workflow) -> Workflow:
        if workflow.id in self._workflows:
            raise WorkflowError(f"workflow already registered: {workflow.id}")
        self._workflows[workflow.id] = workflow
        self._record("registered", workflow.id)
        return workflow

    def get(self, workflow_id: str) -> Workflow:
        try:
            return self._workflows[workflow_id]
        except KeyError:
            raise WorkflowError(f"unknown workflow: {workflow_id}") from None

    def _record(self, event: str, workflow_id: str, detail: str = "") -> None:
        self._history.append({
            "event": event, "workflow": workflow_id, "at": utcnow(), "detail": detail,
        })

    def _emit(self, workflow: Workflow, name: str) -> None:
        if self.event_bus is None:
            return
        self.event_bus.publish(Event(
            id=f"EVT-{workflow.id.replace('-', '')}-{len(self.event_bus.events()) + 1:06d}",
            name=name,
            publisher="workflow",
            payload={"workflow": workflow.id, "state": workflow.state},
        ))

    def _ready_steps(self, workflow: Workflow) -> list[WorkflowStep]:
        ready: list[WorkflowStep] = []
        for step in workflow.steps:
            if step.status != "pending":
                continue
            deps_done = all(workflow.step(d).status == "completed" for d in step.requires)
            if deps_done:
                ready.append(step)
        return ready

    def run(self, workflow_id: str) -> Workflow:
        workflow = self.get(workflow_id)
        if workflow.state not in {"pending", "awaiting_approval"}:
            raise WorkflowError(f"workflow {workflow_id} cannot run from state {workflow.state!r}")
        workflow.state = "running"
        self._record("started", workflow_id)
        while True:
            ready = self._ready_steps(workflow)
            if not ready:
                break
            for step in ready:
                if step.kind == "approval":
                    step.status = "awaiting_approval"
                    workflow.state = "awaiting_approval"
                    self._record("awaiting_approval", workflow_id, step.id)
                    self._emit(workflow, f"workflow.{workflow.id}.awaiting_approval")
                    return workflow
                self._execute_task(workflow, step)
        if all(s.status == "completed" for s in workflow.steps):
            workflow.state = "completed"
            self._record("completed", workflow_id)
            self._emit(workflow, f"workflow.{workflow.id}.completed")
        return workflow

    def _execute_task(self, workflow: Workflow, step: WorkflowStep) -> None:
        step.status = "running"
        attempts = 0
        while attempts <= step.max_retries:
            try:
                assert step.fn is not None
                step.fn({})
                step.status = "completed"
                self._record("step_completed", workflow.id, step.id)
                return
            except Exception as exc:
                attempts += 1
                if attempts > step.max_retries:
                    step.status = "failed"
                    workflow.state = "failed"
                    self._record("step_failed", workflow.id, f"{step.id}: {exc}")
                    self._emit(workflow, f"workflow.{workflow.id}.failed")
                    return
                self._record("step_retried", workflow.id, f"{step.id} attempt {attempts}")

    def approve(self, workflow_id: str, step_id: str) -> Workflow:
        workflow = self.get(workflow_id)
        step = workflow.step(step_id)
        if step.kind != "approval":
            raise WorkflowError(f"step {step_id} is not an approval gate")
        if step.status != "awaiting_approval":
            raise WorkflowError(f"step {step_id} is not awaiting approval")
        step.status = "completed"
        self._record("approved", workflow_id, step_id)
        return self.run(workflow_id)

    def cancel(self, workflow_id: str) -> Workflow:
        workflow = self.get(workflow_id)
        for step in workflow.steps:
            if step.status == "pending":
                step.status = "cancelled"
        workflow.state = "rolled_back"
        workflow.updated_at = utcnow()
        self._record("cancelled", workflow_id)
        return workflow

    def workflows(self, state: str | None = None) -> list[Workflow]:
        if state is None:
            return list(self._workflows.values())
        return [w for w in self._workflows.values() if w.state == state]

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "workflows": [w.to_dict() for w in self._workflows.values()],
            "history": list(self._history),
        }

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.snapshot(), indent=2) + "\n", encoding="utf-8")
        return path


def _demo_workflow() -> Workflow:
    """Deterministic demo workflow: task -> approval -> task (CLI/tests)."""

    def prepare(_ctx: dict[str, Any]) -> None:
        pass

    def finalize(_ctx: dict[str, Any]) -> None:
        pass

    return Workflow(
        id="WF-000001",
        name="demo mission workflow",
        steps=[
            WorkflowStep("prep", "task", "prepare mission", fn=prepare),
            WorkflowStep("review", "approval", "governor review gate", requires=["prep"]),
            WorkflowStep("finalize", "task", "finalize mission", fn=finalize, requires=["review"]),
        ],
    )
