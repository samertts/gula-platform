"""Phase 4 — Execution Engine.

Execute a mission in the fixed order:

    Analyze -> Plan -> Validate -> Execute -> Test -> Verify
    -> Document -> Update Knowledge -> Checkpoint -> Continue

Each step is a callable handler receiving an execution context. The engine
is deterministic, logs a trace, and persists a checkpoint after every step
via the Failure Recovery module so the mission can resume without restart.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from scripts.builder.core import MissionStatus, utcnow
from scripts.builder.planner import EXECUTION_ORDER

StepHandler = Callable[[str, dict[str, Any]], dict[str, Any]]


class ExecutionError(Exception):
    """Raised when an execution step fails."""


@dataclass
class ExecutionResult:
    """Outcome of one mission execution run."""

    mission_id: str
    status: str = MissionStatus.EXECUTING.value
    completed_steps: list[str] = field(default_factory=list)
    failed_step: str = ""
    error: str = ""
    trace: list[str] = field(default_factory=list)
    started_at: str = field(default_factory=utcnow)
    finished_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "status": self.status,
            "completed_steps": self.completed_steps,
            "failed_step": self.failed_step,
            "error": self.error,
            "trace": self.trace,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


def default_handler(step: str, context: dict[str, Any]) -> dict[str, Any]:
    """Pass-through handler recording the step in the trace."""
    return {"step": step, "ok": True}


def execute_mission(
    mission_id: str,
    handlers: dict[str, StepHandler] | None = None,
    start_from: str | None = None,
    checkpoint_callback: Callable[[str, dict[str, Any]], None] | None = None,
) -> ExecutionResult:
    """Run the execution order, checkpointing after every step.

    handlers:        step name -> callable(step, context) -> result dict.
    start_from:      first step to run (resume support); steps before it are
                     considered already completed.
    checkpoint_callback: called with (step, context) after each successful
                     step so recovery can persist progress.
    """
    result = ExecutionResult(mission_id=mission_id)
    context: dict[str, Any] = {"mission_id": mission_id, "steps": {}}
    ordered = list(EXECUTION_ORDER)
    resume = start_from or ordered[0]
    if resume not in ordered:
        raise ExecutionError(f"unknown step: {resume}")

    start_index = ordered.index(resume)
    result.completed_steps.extend(ordered[:start_index])
    for step in ordered[start_index:]:
        handler = (handlers or {}).get(step, default_handler)
        result.trace.append(f"{step}:start")
        try:
            outcome = handler(step, context)
        except Exception as exc:
            result.status = MissionStatus.FAILED.value
            result.failed_step = step
            result.error = str(exc)
            result.trace.append(f"{step}:failed:{exc}")
            result.finished_at = utcnow()
            return result
        if not isinstance(outcome, dict) or not outcome.get("ok"):
            result.status = MissionStatus.FAILED.value
            result.failed_step = step
            result.error = str(outcome.get("error", "handler returned not-ok"))
            result.trace.append(f"{step}:failed:{result.error}")
            result.finished_at = utcnow()
            return result
        context["steps"][step] = outcome
        result.completed_steps.append(step)
        result.trace.append(f"{step}:ok")
        if checkpoint_callback is not None:
            checkpoint_callback(step, context)

    result.status = MissionStatus.COMPLETED.value
    result.finished_at = utcnow()
    return result


def make_mission_id(prefix: str = "MSN") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def resume_from(result: ExecutionResult) -> str | None:
    """Next step to run for a failed mission (None when completed)."""
    if result.status == MissionStatus.COMPLETED.value:
        return None
    if not result.completed_steps:
        return EXECUTION_ORDER[0]
    completed = set(result.completed_steps)
    for step in EXECUTION_ORDER:
        if step not in completed:
            return step
    return None
