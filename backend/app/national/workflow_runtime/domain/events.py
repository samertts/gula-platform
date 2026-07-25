from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class WorkflowStarted:
    workflow_id: str
    execution_id: str
    trigger: str = "manual"
    input_summary: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowStepCompleted:
    workflow_id: str
    execution_id: str
    step_id: str
    step_name: str = ""
    duration_ms: float = 0.0
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowStepFailed:
    workflow_id: str
    execution_id: str
    step_id: str
    step_name: str = ""
    error: str | None = None
    attempt: int = 0
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowCompleted:
    workflow_id: str
    execution_id: str
    duration_ms: float = 0.0
    output_summary: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowFailed:
    workflow_id: str
    execution_id: str
    error: str | None = None
    failed_step: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowCancelled:
    workflow_id: str
    execution_id: str
    reason: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowCompensated:
    workflow_id: str
    execution_id: str
    steps_compensated: int = 0
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowPaused:
    workflow_id: str
    execution_id: str
    reason: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowTimedOut:
    workflow_id: str
    execution_id: str
    step_id: str | None = None
    timeout_s: float = 0.0
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowApprovalRequired:
    workflow_id: str
    execution_id: str
    step_id: str
    assignee_roles: list[str] = field(default_factory=list)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowApprovalCompleted:
    workflow_id: str
    execution_id: str
    step_id: str
    approver_id: str | None = None
    approved: bool = False
    comments: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowSagaAction:
    saga_id: str
    workflow_id: str
    step_id: str
    action: str = "forward"
    status: str = "pending"
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
