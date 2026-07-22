from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

from app._compat import UTC

T = TypeVar("T")


class WorkflowState(Enum):
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"
    COMPENSATED = "compensated"


class WorkflowStepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    COMPENSATED = "compensated"


@dataclass
class WorkflowContext:
    workflow_id: str
    workflow_type: str
    state: WorkflowState = WorkflowState.INITIATED
    current_step: str = ""
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


@dataclass
class WorkflowStep:
    name: str
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: Any = None
    error: str | None = None
    compensation: str | None = None


class WorkflowEngine[T](ABC):
    def __init__(self) -> None:
        self._steps: list[WorkflowStep] = []
        self._compensation_stack: list[str] = []

    @abstractmethod
    async def execute(self, context: WorkflowContext, input_data: T) -> WorkflowContext: ...

    @abstractmethod
    async def compensate(self, context: WorkflowContext) -> None: ...

    @abstractmethod
    async def can_transition(self, from_state: WorkflowState, to_state: WorkflowState) -> bool: ...

    def add_step(self, step: WorkflowStep) -> None:
        self._steps.append(step)
        self._compensation_stack.append(step.name)

    def get_state_flow(self) -> dict[WorkflowState, list[WorkflowState]]:
        return {
            WorkflowState.INITIATED: [WorkflowState.IN_PROGRESS, WorkflowState.CANCELLED],
            WorkflowState.IN_PROGRESS: [WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED],
            WorkflowState.FAILED: [WorkflowState.ROLLED_BACK, WorkflowState.IN_PROGRESS],
            WorkflowState.COMPLETED: [],
            WorkflowState.CANCELLED: [WorkflowState.INITIATED],
            WorkflowState.ROLLED_BACK: [],
            WorkflowState.COMPENSATED: [],
        }
