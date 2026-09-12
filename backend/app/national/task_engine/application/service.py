from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.national.task_engine.application.interfaces import (
    AssignmentEngine,
    KPIEngine,
    RoundRobinAssigner,
    SimpleKPIEngine,
)
from app.national.task_engine.domain.entities import (
    NationalTask,
    TaskAssignment,
    TaskAuditLog,
    TaskComment,
    TaskEscalation,
    TaskQueue,
    TaskSLADefinition,
)
from app.national.task_engine.domain.enums import (
    AssignmentStrategy,
    TaskCategory,
    TaskPriority,
    TaskStatus,
)
from app.national.task_engine.domain.repository import (
    NationalTaskRepository,
    TaskAssignmentRepository,
    TaskAuditLogRepository,
    TaskCommentRepository,
    TaskEscalationRepository,
    TaskQueueRepository,
    TaskSLARepository,
)
from app.national.task_engine.exceptions import (
    TaskFieldNotUpdatableError,
    TaskNotFoundError,
    TaskQueueNotFoundError,
)

logger = logging.getLogger("gula.task_engine.service")

#: NR-070. Fields a PUT may change, allowlisted rather than filtered.
#:
#: What is absent is the point. `status` belongs to the transition methods --
#: start, complete, fail, cancel, escalate, delegate, hold, resume -- which is
#: where the state machine lives; `assigned_to` and `assigned_by` belong to
#: `assign_task` and `delegate_task`; `created_by` belongs to whoever actually
#: created the row; `started_at`, `completed_at`, `escalation_level`, `version`
#: and the workflow links are computed. The previous loop set any of them from
#: the request body.
_TASK_UPDATABLE_FIELDS = frozenset({
    "title", "description", "priority", "category", "task_type",
    "queue_id", "sla_due_at", "tags", "metadata",
})

#: The same two coercions `create_task` performs at the route. Without them an
#: update would store the raw string where the entity holds an enum, and
#: `task.priority.value` would raise on the next read.
_TASK_FIELD_TYPES = {"priority": TaskPriority, "category": TaskCategory}

#: A queue's `allowed_roles` and `allowed_categories` decide which principals a
#: task can be auto-assigned to, so the queue update carries the same rule.
_QUEUE_UPDATABLE_FIELDS = frozenset({
    "name", "description", "assignment_strategy", "max_concurrent",
    "max_waiting_time_s", "allowed_roles", "allowed_categories",
})

_SLA_UPDATABLE_FIELDS = frozenset({
    "task_category", "task_type", "priority", "warning_threshold_s",
    "breach_threshold_s", "notification_enabled", "escalation_enabled",
})


def _reject_unknown(updates: dict, allowed: frozenset[str]) -> None:
    rejected = sorted(set(updates) - allowed)
    if rejected:
        raise TaskFieldNotUpdatableError(rejected)


class TaskEngineService:
    def __init__(
        self,
        task_repo: NationalTaskRepository,
        queue_repo: TaskQueueRepository,
        assignment_repo: TaskAssignmentRepository,
        escalation_repo: TaskEscalationRepository,
        sla_repo: TaskSLARepository,
        comment_repo: TaskCommentRepository,
        audit_repo: TaskAuditLogRepository,
        assignment_engine: AssignmentEngine | None = None,
        kpi_engine: KPIEngine | None = None,
    ) -> None:
        self._task_repo = task_repo
        self._queue_repo = queue_repo
        self._assignment_repo = assignment_repo
        self._escalation_repo = escalation_repo
        self._sla_repo = sla_repo
        self._comment_repo = comment_repo
        self._audit_repo = audit_repo
        self._assignment_engine = assignment_engine or RoundRobinAssigner()
        self._kpi_engine = kpi_engine or SimpleKPIEngine()

    def create_task(
        self, task: NationalTask, actor_id: str | None = None,
    ) -> NationalTask:
        task.version = 1
        task = self._task_repo.save(task)
        if task.queue_id:
            self._auto_assign(task)
        self._audit("CREATED", task, None, task.status.value, actor_id)
        return task

    def bulk_create(
        self, tasks: list[NationalTask], actor_id: str | None = None,
    ) -> list[NationalTask]:
        results = []
        for task in tasks:
            result = self.create_task(task, actor_id)
            results.append(result)
        return results

    def get_task(self, task_id: str) -> NationalTask | None:
        return self._task_repo.get(task_id)

    def list_tasks(
        self, skip: int = 0, limit: int = 100, filters: dict | None = None,
    ) -> list[NationalTask]:
        return self._task_repo.list(skip=skip, limit=limit, filters=filters)

    def update_task(
        self,
        task_id: str,
        updates: dict[str, Any],
        actor_id: str | None = None,
    ) -> NationalTask:
        task = self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        _reject_unknown(updates, _TASK_UPDATABLE_FIELDS)
        for key, value in updates.items():
            field_type = _TASK_FIELD_TYPES.get(key)
            setattr(task, key, field_type(value) if field_type and value is not None else value)
        task.version += 1
        task.updated_at = datetime.now(UTC)
        result = self._task_repo.save(task)
        # An update used to be audited only when it changed the status, which it
        # can no longer do at all. Auditing the update itself is what keeps the
        # path represented in the history rather than dropping the entry.
        self._audit(
            "UPDATED", result, result.status.value, result.status.value, actor_id,
            details={"fields": sorted(updates)},
        )
        return result

    def delete_task(self, task_id: str) -> bool:
        task = self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        if task.status in (TaskStatus.IN_PROGRESS,):
            raise ValueError("Cannot delete a task that is in progress")
        return self._task_repo.delete(task_id)

    def assign_task(
        self, task_id: str, assignee_id: str, assigned_by: str | None = None,
    ) -> NationalTask:
        """`assigned_by` is the authenticated caller, resolved at the route.

        It used to be `data.get("assigned_by")` -- a claim the client made about
        itself, written into the field an audit reader would trust.
        """
        task = self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        task.assigned_to = assignee_id
        task.assigned_by = assigned_by
        task.status = TaskStatus.ASSIGNED
        task.updated_at = datetime.now(UTC)
        result = self._task_repo.save(task)
        assignment = TaskAssignment(
            id=str(uuid.uuid4()),
            task_id=task_id,
            assignee_id=assignee_id,
            assigned_by=assigned_by,
        )
        self._assignment_repo.save(assignment)
        self._audit("ASSIGNED", task, old_status, task.status.value, assigned_by)
        return result

    def start_task(
        self,
        task_id: str,
        assignee_id: str | None = None,
        actor_id: str | None = None,
    ) -> NationalTask:
        task = self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now(UTC)
        if assignee_id:
            task.assigned_to = assignee_id
        task.updated_at = datetime.now(UTC)
        result = self._task_repo.save(task)
        self._audit("STARTED", task, old_status, task.status.value, actor_id or assignee_id)
        return result

    def complete_task(
        self,
        task_id: str,
        result_data: dict | None = None,
        actor_id: str | None = None,
    ) -> NationalTask:
        task = self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(UTC)
        if result_data:
            task.metadata.update(result_data)
        task.updated_at = datetime.now(UTC)
        result = self._task_repo.save(task)
        self._audit("COMPLETED", task, old_status, task.status.value, actor_id)
        return result

    def fail_task(
        self, task_id: str, error: str, actor_id: str | None = None,
    ) -> NationalTask:
        task = self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        task.status = TaskStatus.FAILED
        task.metadata["error"] = error
        task.updated_at = datetime.now(UTC)
        result = self._task_repo.save(task)
        self._audit("FAILED", task, old_status, task.status.value, actor_id)
        return result

    def cancel_task(
        self, task_id: str, reason: str | None = None, actor_id: str | None = None,
    ) -> NationalTask:
        task = self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        task.status = TaskStatus.CANCELLED
        if reason:
            task.metadata["cancel_reason"] = reason
        task.updated_at = datetime.now(UTC)
        result = self._task_repo.save(task)
        self._audit("CANCELLED", task, old_status, task.status.value, actor_id)
        return result

    def escalate_task(
        self,
        task_id: str,
        reason: str,
        escalated_to: str | None = None,
        escalated_by: str | None = None,
    ) -> NationalTask:
        """`escalated_to` is a target and stays client-chosen; `escalated_by` is
        not, and was simply never written -- the entity and the column have
        carried the field all along."""
        task = self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        task.status = TaskStatus.ESCALATED
        task.updated_at = datetime.now(UTC)
        result = self._task_repo.save(task)
        escalation = TaskEscalation(
            id=str(uuid.uuid4()),
            task_id=task_id,
            escalated_to=escalated_to,
            escalated_by=escalated_by,
            reason=reason,
        )
        self._escalation_repo.save(escalation)
        self._audit("ESCALATED", task, old_status, task.status.value, escalated_by)
        return result

    def delegate_task(
        self,
        task_id: str,
        to_user: str,
        reason: str | None = None,
        delegated_by: str | None = None,
    ) -> NationalTask:
        task = self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        task.assigned_to = to_user
        task.assigned_by = delegated_by
        task.status = TaskStatus.DELEGATED
        task.updated_at = datetime.now(UTC)
        result = self._task_repo.save(task)
        self._audit(
            "DELEGATED", task, old_status, task.status.value, delegated_by,
            details={"reason": reason} if reason else None,
        )
        return result

    def hold_task(self, task_id: str, actor_id: str | None = None) -> NationalTask:
        task = self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        task.status = TaskStatus.ON_HOLD
        task.updated_at = datetime.now(UTC)
        result = self._task_repo.save(task)
        self._audit("ON_HOLD", task, old_status, task.status.value, actor_id)
        return result

    def resume_task(self, task_id: str, actor_id: str | None = None) -> NationalTask:
        task = self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = datetime.now(UTC)
        result = self._task_repo.save(task)
        self._audit("RESUMED", task, old_status, task.status.value, actor_id)
        return result

    def add_comment(
        self, task_id: str, author_id: str, author_name: str, content: str,
    ) -> TaskComment:
        comment = TaskComment(
            id=str(uuid.uuid4()),
            task_id=task_id,
            author_id=author_id,
            author_name=author_name,
            content=content,
        )
        return self._comment_repo.save(comment)

    def get_comments(self, task_id: str) -> list[TaskComment]:
        return self._comment_repo.find_by_task(task_id)

    def get_history(self, task_id: str) -> list[TaskAuditLog]:
        return self._audit_repo.find_by_task(task_id)

    def create_queue(self, queue: TaskQueue) -> TaskQueue:
        return self._queue_repo.save(queue)

    def list_queues(self) -> list[TaskQueue]:
        return self._queue_repo.list()

    def update_queue(self, queue_id: str, updates: dict) -> TaskQueue:
        queue = self._queue_repo.get(queue_id)
        if not queue:
            raise TaskQueueNotFoundError(queue_id)
        _reject_unknown(updates, _QUEUE_UPDATABLE_FIELDS)
        for key, value in updates.items():
            setattr(queue, key, value)
        queue.updated_at = datetime.now(UTC)
        return self._queue_repo.save(queue)

    def create_sla(self, sla: TaskSLADefinition) -> TaskSLADefinition:
        return self._sla_repo.save(sla)

    def list_slas(self) -> list[TaskSLADefinition]:
        return self._sla_repo.list()

    def update_sla(self, sla_id: str, updates: dict) -> TaskSLADefinition:
        sla = self._sla_repo.get(sla_id)
        if not sla:
            raise TaskNotFoundError(sla_id)
        _reject_unknown(updates, _SLA_UPDATABLE_FIELDS)
        for key, value in updates.items():
            setattr(sla, key, value)
        sla.updated_at = datetime.now(UTC)
        return self._sla_repo.save(sla)

    def get_pending_tasks(self, user_id: str) -> list[NationalTask]:
        return self._task_repo.find_by_assignee(user_id)

    def get_overdue_tasks(self) -> list[NationalTask]:
        return self._task_repo.find_overdue()

    def get_stats(self) -> dict[str, Any]:
        return self._task_repo.get_stats()

    def get_dashboard(self) -> dict[str, Any]:
        stats = self._task_repo.get_stats()
        tasks = self._task_repo.list(limit=1000)
        kpis = self._kpi_engine.calculate(tasks)
        return {"stats": stats, "kpis": kpis}

    def _auto_assign(self, task: NationalTask) -> None:
        queue = self._queue_repo.get(task.queue_id)
        if not queue:
            return
        if queue.assignment_strategy == AssignmentStrategy.MANUAL:
            return
        candidates = queue.allowed_roles
        if candidates:
            assignee = self._assignment_engine.assign(task, candidates)
            if assignee:
                task.assigned_to = assignee
                task.status = TaskStatus.ASSIGNED
                self._task_repo.save(task)

    def _audit(
        self,
        action: str,
        task: NationalTask,
        previous: str | None,
        new: str | None,
        actor_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """NR-070. `actor_id` is a column on `national_task_audit_logs` and a
        field on the entity, and every row written here left it NULL: the log
        recorded what happened and never who did it. The actor is the
        authenticated caller, resolved at the route and threaded down."""
        payload: dict[str, Any] = {"title": task.title, "priority": task.priority.value}
        if details:
            payload.update(details)
        log = TaskAuditLog(
            id=str(uuid.uuid4()),
            task_id=task.id,
            action=action,
            actor_id=actor_id,
            previous_status=previous,
            new_status=new,
            details=payload,
        )
        self._audit_repo.save(log)
