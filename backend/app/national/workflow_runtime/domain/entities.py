from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.national.workflow_runtime.domain.enums import (
    CompensationStrategy,
    WorkflowApprovalStrategy,
    WorkflowExecutionStatus,
    WorkflowRetryPolicy,
    WorkflowStepStatus,
    WorkflowTimeoutPolicy,
    WorkflowTrigger,
)


@dataclass
class RetryPolicyConfig:
    max_retries: int = 3
    backoff_delay_s: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay_s: float = 60.0
    policy: WorkflowRetryPolicy = WorkflowRetryPolicy.EXPONENTIAL


@dataclass
class WorkflowStepDefinition:
    id: str
    name: str
    type: str = "task"
    handler: str = ""
    order: int = 0
    retry_policy: RetryPolicyConfig | None = None
    timeout_s: float = 300.0
    compensation_handler: str | None = None
    depends_on: list[str] = field(default_factory=list)
    approval_required: bool = False
    approval_strategy: WorkflowApprovalStrategy = WorkflowApprovalStrategy.ANY
    assigned_roles: list[str] = field(default_factory=list)
    input_mapping: dict[str, str] = field(default_factory=dict)
    output_mapping: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    id: str
    name: str
    description: str = ""
    type: str = ""
    version: int = 1
    steps: list[WorkflowStepDefinition] = field(default_factory=list)
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "active"
    timeout_policy: WorkflowTimeoutPolicy = WorkflowTimeoutPolicy.FAIL
    compensation_strategy: CompensationStrategy = CompensationStrategy.REVERSE_ORDER
    created_by: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def step_count(self) -> int:
        return len(self.steps)

    def get_step(self, step_id: str) -> WorkflowStepDefinition | None:
        for s in self.steps:
            if s.id == step_id:
                return s
        return None

    def ordered_steps(self) -> list[WorkflowStepDefinition]:
        return sorted(self.steps, key=lambda s: s.order)


@dataclass
class WorkflowExecution:
    id: str
    workflow_id: str
    workflow_version: int = 1
    status: WorkflowExecutionStatus = WorkflowExecutionStatus.PENDING
    trigger: WorkflowTrigger = WorkflowTrigger.MANUAL
    started_at: datetime | None = None
    completed_at: datetime | None = None
    context: dict[str, Any] = field(default_factory=dict)
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    current_step: str = ""
    error: str | None = None
    correlation_id: str | None = None
    created_by: str | None = None
    tenant_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def duration_ms(self) -> float:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return 0.0

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            WorkflowExecutionStatus.COMPLETED,
            WorkflowExecutionStatus.FAILED,
            WorkflowExecutionStatus.CANCELLED,
            WorkflowExecutionStatus.TIMED_OUT,
            WorkflowExecutionStatus.COMPENSATED,
            WorkflowExecutionStatus.ROLLED_BACK,
        )

    @property
    def is_active(self) -> bool:
        return self.status in (
            WorkflowExecutionStatus.RUNNING,
            WorkflowExecutionStatus.PAUSED,
            WorkflowExecutionStatus.SUSPENDED,
        )


@dataclass
class WorkflowExecutionStep:
    id: str
    execution_id: str
    step_id: str
    step_name: str = ""
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    attempt: int = 0
    assigned_to: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    duration_ms: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowApproval:
    id: str
    execution_id: str
    step_id: str
    approver_id: str | None = None
    approver_name: str | None = None
    status: str = "pending"
    comments: str | None = None
    assigned_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    responded_at: datetime | None = None


@dataclass
class WorkflowCompensation:
    id: str
    execution_id: str
    step_id: str
    status: str = "pending"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowTimer:
    id: str
    execution_id: str
    step_id: str
    fire_at: datetime
    action: str = "timeout"
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SagaLog:
    id: str
    saga_id: str
    step_id: str
    step_type: str = "task"
    action: str = "forward"
    status: str = "pending"
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowTemplate:
    id: str
    name: str
    description: str = ""
    definition: dict[str, Any] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    category: str = "general"
    tags: list[str] = field(default_factory=list)
    created_by: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
