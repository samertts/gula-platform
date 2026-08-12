from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from backend.app._compat import UTC


@dataclass
class TaskCreated:
    task_id: str
    title: str
    priority: str = "medium"
    category: str = "general"
    assigned_to: str | None = None
    queue: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TaskAssigned:
    task_id: str
    assignee_id: str
    assigned_by: str | None = None
    strategy: str = "manual"
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TaskStarted:
    task_id: str
    assignee_id: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TaskCompleted:
    task_id: str
    assignee_id: str | None = None
    completed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    duration_ms: float = 0.0


@dataclass
class TaskFailed:
    task_id: str
    error: str | None = None
    attempt: int = 0
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TaskCancelled:
    task_id: str
    reason: str | None = None
    cancelled_by: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TaskEscalated:
    task_id: str
    level: str = "level_1"
    escalated_to: str | None = None
    reason: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TaskSLABreached:
    task_id: str
    sla_due_at: datetime | None = None
    actual_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    priority: str = "medium"


@dataclass
class TaskDelegated:
    task_id: str
    from_user: str | None = None
    to_user: str | None = None
    reason: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TaskCommentAdded:
    task_id: str
    author_id: str | None = None
    comment_preview: str = ""
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TaskStatusChanged:
    task_id: str
    previous_status: str | None = None
    new_status: str | None = None
    changed_by: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
