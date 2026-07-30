from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

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
    TaskNotFoundError,
    TaskQueueNotFoundError,
)

logger = logging.getLogger("gula.task_engine.service")


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

    async def create_task(self, task: NationalTask) -> NationalTask:
        task.version = 1
        task = await self._task_repo.save(task)
        if task.queue_id:
            await self._auto_assign(task)
        await self._audit("CREATED", task, None, task.status.value)
        return task

    async def bulk_create(self, tasks: list[NationalTask]) -> list[NationalTask]:
        results = []
        for task in tasks:
            result = await self.create_task(task)
            results.append(result)
        return results

    async def get_task(self, task_id: str) -> NationalTask | None:
        return await self._task_repo.get(task_id)

    async def list_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: dict | None = None,
    ) -> list[NationalTask]:
        return await self._task_repo.list(skip=skip, limit=limit, filters=filters)

    async def update_task(self, task_id: str, updates: dict[str, Any]) -> NationalTask:
        task = await self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        for key, value in updates.items():
            if hasattr(task, key) and key not in ("id", "created_at", "version"):
                setattr(task, key, value)
        task.version += 1
        task.updated_at = datetime.now(UTC)
        result = await self._task_repo.save(task)
        if old_status != result.status.value:
            await self._audit("STATUS_CHANGED", task, old_status, result.status.value)
        return result

    async def delete_task(self, task_id: str) -> bool:
        task = await self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        if task.status in (TaskStatus.IN_PROGRESS,):
            raise ValueError("Cannot delete a task that is in progress")
        return await self._task_repo.delete(task_id)

    async def assign_task(
        self,
        task_id: str,
        assignee_id: str,
        assigned_by: str | None = None,
    ) -> NationalTask:
        task = await self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        task.assigned_to = assignee_id
        task.assigned_by = assigned_by
        task.status = TaskStatus.ASSIGNED
        task.updated_at = datetime.now(UTC)
        result = await self._task_repo.save(task)
        assignment = TaskAssignment(
            id=str(uuid.uuid4()),
            task_id=task_id,
            assignee_id=assignee_id,
            assigned_by=assigned_by,
        )
        await self._assignment_repo.save(assignment)
        await self._audit("ASSIGNED", task, old_status, task.status.value)
        return result

    async def start_task(self, task_id: str, assignee_id: str | None = None) -> NationalTask:
        task = await self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now(UTC)
        if assignee_id:
            task.assigned_to = assignee_id
        task.updated_at = datetime.now(UTC)
        result = await self._task_repo.save(task)
        await self._audit("STARTED", task, old_status, task.status.value)
        return result

    async def complete_task(self, task_id: str, result_data: dict | None = None) -> NationalTask:
        task = await self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(UTC)
        if result_data:
            task.metadata.update(result_data)
        task.updated_at = datetime.now(UTC)
        result = await self._task_repo.save(task)
        await self._audit("COMPLETED", task, old_status, task.status.value)
        return result

    async def fail_task(self, task_id: str, error: str) -> NationalTask:
        task = await self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        task.status = TaskStatus.FAILED
        task.metadata["error"] = error
        task.updated_at = datetime.now(UTC)
        result = await self._task_repo.save(task)
        await self._audit("FAILED", task, old_status, task.status.value)
        return result

    async def cancel_task(self, task_id: str, reason: str | None = None) -> NationalTask:
        task = await self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        task.status = TaskStatus.CANCELLED
        if reason:
            task.metadata["cancel_reason"] = reason
        task.updated_at = datetime.now(UTC)
        result = await self._task_repo.save(task)
        await self._audit("CANCELLED", task, old_status, task.status.value)
        return result

    async def escalate_task(
        self,
        task_id: str,
        reason: str,
        escalated_to: str | None = None,
    ) -> NationalTask:
        task = await self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        task.status = TaskStatus.ESCALATED
        task.updated_at = datetime.now(UTC)
        result = await self._task_repo.save(task)
        escalation = TaskEscalation(
            id=str(uuid.uuid4()),
            task_id=task_id,
            escalated_to=escalated_to,
            reason=reason,
        )
        await self._escalation_repo.save(escalation)
        await self._audit("ESCALATED", task, old_status, task.status.value)
        return result

    async def delegate_task(
        self,
        task_id: str,
        to_user: str,
        reason: str | None = None,
    ) -> NationalTask:
        task = await self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        task.assigned_to = to_user
        task.status = TaskStatus.DELEGATED
        task.updated_at = datetime.now(UTC)
        result = await self._task_repo.save(task)
        await self._audit("DELEGATED", task, old_status, task.status.value)
        return result

    async def hold_task(self, task_id: str) -> NationalTask:
        task = await self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        task.status = TaskStatus.ON_HOLD
        task.updated_at = datetime.now(UTC)
        result = await self._task_repo.save(task)
        await self._audit("ON_HOLD", task, old_status, task.status.value)
        return result

    async def resume_task(self, task_id: str) -> NationalTask:
        task = await self._task_repo.get(task_id)
        if not task:
            raise TaskNotFoundError(task_id)
        old_status = task.status.value
        task.status = TaskStatus.IN_PROGRESS
        task.updated_at = datetime.now(UTC)
        result = await self._task_repo.save(task)
        await self._audit("RESUMED", task, old_status, task.status.value)
        return result

    async def add_comment(
        self,
        task_id: str,
        author_id: str,
        author_name: str,
        content: str,
    ) -> TaskComment:
        comment = TaskComment(
            id=str(uuid.uuid4()),
            task_id=task_id,
            author_id=author_id,
            author_name=author_name,
            content=content,
        )
        return await self._comment_repo.save(comment)

    async def get_comments(self, task_id: str) -> list[TaskComment]:
        return await self._comment_repo.find_by_task(task_id)

    async def get_history(self, task_id: str) -> list[TaskAuditLog]:
        return await self._audit_repo.find_by_task(task_id)

    async def create_queue(self, queue: TaskQueue) -> TaskQueue:
        return await self._queue_repo.save(queue)

    async def list_queues(self) -> list[TaskQueue]:
        return await self._queue_repo.list()

    async def update_queue(self, queue_id: str, updates: dict) -> TaskQueue:
        queue = await self._queue_repo.get(queue_id)
        if not queue:
            raise TaskQueueNotFoundError(queue_id)
        for key, value in updates.items():
            if hasattr(queue, key) and key not in ("id", "created_at"):
                setattr(queue, key, value)
        queue.updated_at = datetime.now(UTC)
        return await self._queue_repo.save(queue)

    async def create_sla(self, sla: TaskSLADefinition) -> TaskSLADefinition:
        return await self._sla_repo.save(sla)

    async def list_slas(self) -> list[TaskSLADefinition]:
        return await self._sla_repo.list()

    async def update_sla(self, sla_id: str, updates: dict) -> TaskSLADefinition:
        sla = await self._sla_repo.get(sla_id)
        if not sla:
            raise TaskNotFoundError(sla_id)
        for key, value in updates.items():
            if hasattr(sla, key) and key not in ("id", "created_at"):
                setattr(sla, key, value)
        sla.updated_at = datetime.now(UTC)
        return await self._sla_repo.save(sla)

    async def get_pending_tasks(self, user_id: str) -> list[NationalTask]:
        return await self._task_repo.find_by_assignee(user_id)

    async def get_overdue_tasks(self) -> list[NationalTask]:
        return await self._task_repo.find_overdue()

    async def get_stats(self) -> dict[str, Any]:
        return await self._task_repo.get_stats()

    async def get_dashboard(self) -> dict[str, Any]:
        stats = await self._task_repo.get_stats()
        tasks = await self._task_repo.list(limit=1000)
        kpis = await self._kpi_engine.calculate(tasks)
        return {"stats": stats, "kpis": kpis}

    async def _auto_assign(self, task: NationalTask) -> None:
        queue = await self._queue_repo.get(task.queue_id)
        if not queue:
            return
        if queue.assignment_strategy == AssignmentStrategy.MANUAL:
            return
        candidates = queue.allowed_roles
        if candidates:
            assignee = await self._assignment_engine.assign(task, candidates)
            if assignee:
                task.assigned_to = assignee
                task.status = TaskStatus.ASSIGNED
                await self._task_repo.save(task)

    async def _audit(
        self,
        action: str,
        task: NationalTask,
        previous: str | None,
        new: str | None,
    ) -> None:
        log = TaskAuditLog(
            id=str(uuid.uuid4()),
            task_id=task.id,
            action=action,
            previous_status=previous,
            new_status=new,
            details={"title": task.title, "priority": task.priority.value},
        )
        await self._audit_repo.save(log)
