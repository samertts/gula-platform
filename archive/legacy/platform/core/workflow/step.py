from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    status: StepStatus = StepStatus.PENDING
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class WorkflowStep:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def execute(self, context: dict[str, Any]) -> StepResult:
        raise NotImplementedError
