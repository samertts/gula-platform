from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.national.task_engine.domain.enums import (
    AssignmentStrategy,
    EscalationLevel,
    TaskCategory,
    TaskPriority,
    TaskSLAStatus,
    TaskStatus,
)


@dataclass
class NationalTask:
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    category: TaskCategory = TaskCategory.GENERAL
    task_type: str = "general"
    assigned_to: str | None = None
    assigned_by: str | None = None
    queue_id: str | None = None
    workflow_id: str | None = None
    workflow_execution_id: str | None = None
    parent_task_id: str | None = None
    sla_due_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    escalation_level: EscalationLevel = EscalationLevel.LEVEL_1
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None
    created_by: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: int = 1

    @property
    def is_overdue(self) -> bool:
        if self.sla_due_at and self.status not in (
            TaskStatus.COMPLETED,
            TaskStatus.CANCELLED,
            TaskStatus.FAILED,
        ):
            return datetime.now(UTC) > self.sla_due_at
        return False

    @property
    def sla_status(self) -> TaskSLAStatus:
        if not self.sla_due_at or self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.CANCELLED,
            TaskStatus.FAILED,
        ):
            return TaskSLAStatus.ON_TRACK
        remaining = (self.sla_due_at - datetime.now(UTC)).total_seconds()
        if remaining < 0:
            return TaskSLAStatus.BREACHED
        if remaining < 3600:
            return TaskSLAStatus.WARNING
        return TaskSLAStatus.ON_TRACK


@dataclass
class TaskQueue:
    id: str
    name: str
    description: str = ""
    assignment_strategy: AssignmentStrategy = AssignmentStrategy.MANUAL
    max_concurrent: int = 10
    max_waiting_time_s: float = 3600.0
    allowed_roles: list[str] = field(default_factory=list)
    allowed_categories: list[TaskCategory] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TaskAssignment:
    id: str
    task_id: str
    assignee_id: str
    assigned_by: str | None = None
    assigned_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    assignment_strategy: str = "manual"
    accepted_at: datetime | None = None
    completed_at: datetime | None = None
    status: str = "assigned"


@dataclass
class TaskEscalation:
    id: str
    task_id: str
    level: EscalationLevel = EscalationLevel.LEVEL_1
    escalated_to: str | None = None
    escalated_by: str | None = None
    reason: str = ""
    escalated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None
    status: str = "active"


@dataclass
class TaskSLADefinition:
    id: str
    task_category: TaskCategory = TaskCategory.GENERAL
    task_type: str = "general"
    priority: TaskPriority = TaskPriority.MEDIUM
    warning_threshold_s: float = 3600.0
    breach_threshold_s: float = 7200.0
    notification_enabled: bool = True
    escalation_enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TaskComment:
    id: str
    task_id: str
    author_id: str
    author_name: str = ""
    content: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TaskAuditLog:
    id: str
    task_id: str
    action: str = ""
    actor_id: str | None = None
    previous_status: str | None = None
    new_status: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
