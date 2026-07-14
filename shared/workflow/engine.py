from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("gula.workflow")


class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    name: str
    handler: Callable[..., Any]
    depends_on: list[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: str | None = None


@dataclass
class WorkflowDefinition:
    name: str
    steps: list[WorkflowStep] = field(default_factory=list)


class WorkflowInstance:
    def __init__(self, definition: WorkflowDefinition):
        self._def = definition
        self._results: dict[str, Any] = {}

    def execute(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        for step in self._def.steps:
            if step.status == StepStatus.SKIPPED:
                continue
            deps_met = all(d in self._results for d in step.depends_on)
            if not deps_met:
                logger.warning("Step '%s' dependencies not met, skipping", step.name)
                step.status = StepStatus.SKIPPED
                continue
            step.status = StepStatus.IN_PROGRESS
            try:
                step.result = step.handler(ctx, self._results)
                step.status = StepStatus.COMPLETED
                self._results[step.name] = step.result
            except Exception as exc:
                step.status = StepStatus.FAILED
                step.error = str(exc)
                logger.error("Workflow step '%s' failed: %s", step.name, exc)
                raise
        return self._results


class WorkflowEngine:
    def __init__(self):
        self._defs: dict[str, WorkflowDefinition] = {}

    def register(self, definition: WorkflowDefinition) -> None:
        self._defs[definition.name] = definition

    def create(self, name: str) -> WorkflowInstance:
        definition = self._defs.get(name)
        if not definition:
            raise ValueError(f"Unknown workflow: {name}")
        return WorkflowInstance(definition)
