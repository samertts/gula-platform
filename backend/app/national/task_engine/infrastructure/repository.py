from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import desc, text

from datetime import UTC
from backend.app.database import SessionLocal
from backend.app.national.task_engine.domain.entities import (
    NationalTask,
)
from backend.app.national.task_engine.domain.repository import (
    NationalTaskRepository,
    TaskAssignmentRepository,
    TaskAuditLogRepository,
    TaskCommentRepository,
    TaskEscalationRepository,
    TaskQueueRepository,
    TaskSLARepository,
)
from backend.app.national.task_engine.infrastructure.models import (
    NationalTaskModel,
)


class SQLAlchemyNationalTaskRepository(NationalTaskRepository):
    async def save(self, task: NationalTask) -> NationalTask:
        async with SessionLocal() as session:
            model = await session.get(NationalTaskModel, task.id)
            if not model:
                model = NationalTaskModel(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    status=task.status.value,
                    priority=task.priority.value,
                    category=task.category.value,
                    task_type=task.task_type,
                    assigned_to=task.assigned_to,
                    assigned_by=task.assigned_by,
                    queue_id=task.queue_id,
                    workflow_id=task.workflow_id,
                    workflow_execution_id=task.workflow_execution_id,
                    parent_task_id=task.parent_task_id,
                    sla_due_at=task.sla_due_at,
                    started_at=task.started_at,
                    completed_at=task.completed_at,
                    tags=task.tags,
                    extra_metadata=task.metadata,
                    correlation_id=task.correlation_id,
                    created_by=task.created_by,
                    version=task.version,
                )
                session.add(model)
            else:
                model.status = task.status.value
                model.priority = task.priority.value
                model.category = task.category.value
                model.title = task.title
                model.description = task.description
                model.assigned_to = task.assigned_to
                model.assigned_by = task.assigned_by
                model.started_at = task.started_at
                model.completed_at = task.completed_at
                model.escalation_level = 1
                model.extra_metadata = task.metadata
                model.version = task.version
            await session.commit()
            return task

    async def get(self, task_id: str) -> NationalTask | None:
        async with SessionLocal() as session:
            model = await session.get(NationalTaskModel, task_id)
            if not model:
                return None
            return self._model_to_domain(model)

    async def list(self, skip: int = 0, limit: int = 100, filters: dict | None = None) -> list[NationalTask]:
        async with SessionLocal() as session:
            query = session.query(NationalTaskModel)
            if filters:
                if "status" in filters:
                    query = query.filter(NationalTaskModel.status == filters["status"])
                if "priority" in filters:
                    query = query.filter(NationalTaskModel.priority == filters["priority"])
                if "category" in filters:
                    query = query.filter(NationalTaskModel.category == filters["category"])
                if "assignee" in filters:
                    query = query.filter(NationalTaskModel.assigned_to == filters["assignee"])
                if "queue_id" in filters:
                    query = query.filter(NationalTaskModel.queue_id == filters["queue_id"])
                if "search" in filters:
                    query = query.filter(NationalTaskModel.title.like(f"%{filters['search']}%"))
            query = query.order_by(desc(NationalTaskModel.created_at))
            query = query.offset(skip).limit(limit)
            results = await session.execute(query)
            return [self._model_to_domain(row[0]) for row in results]

    async def find_by_status(self, status: str) -> list[NationalTask]:
        return await self.list(filters={"status": status})

    async def find_by_assignee(self, assignee_id: str) -> list[NationalTask]:
        return await self.list(filters={"assignee": assignee_id})

    async def find_by_queue(self, queue_id: str) -> list[NationalTask]:
        return await self.list(filters={"queue_id": queue_id})

    async def find_by_priority(self, priority: str) -> list[NationalTask]:
        return await self.list(filters={"priority": priority})

    async def find_due(self, before: Any) -> list[NationalTask]:
        async with SessionLocal() as session:
            results = await session.execute(
                session.query(NationalTaskModel).filter(
                    NationalTaskModel.sla_due_at <= before,
                    NationalTaskModel.status.in_(["pending", "assigned", "in_progress"]),
                ),
            )
            return [self._model_to_domain(row[0]) for row in results]

    async def find_overdue(self) -> list[NationalTask]:
        return await self.find_due(datetime.now(UTC))

    async def find_escalated(self) -> list[NationalTask]:
        return await self.list(filters={"status": "escalated"})

    async def count_by_status(self) -> dict[str, int]:
        async with SessionLocal() as session:
            result = await session.execute(
                session.query(
                    NationalTaskModel.status, text("count(*) as cnt"),
                ).group_by(NationalTaskModel.status),
            )
            return {row[0]: row[1] for row in result}

    async def get_stats(self) -> dict[str, Any]:
        counts = await self.count_by_status()
        return {"total": sum(counts.values()), "by_status": counts}

    async def delete(self, task_id: str) -> bool:
        async with SessionLocal() as session:
            model = await session.get(NationalTaskModel, task_id)
            if not model:
                return False
            await session.delete(model)
            await session.commit()
            return True

    async def count(self, filters: dict | None = None) -> int:
        async with SessionLocal() as session:
            query = session.query(NationalTaskModel)
            if filters:
                for key, value in filters.items():
                    if hasattr(NationalTaskModel, key):
                        query = query.filter(getattr(NationalTaskModel, key) == value)
            result = await session.execute(query)
            return len(result.all())

    def _model_to_domain(self, model: Any) -> NationalTask:
        from backend.app.national.task_engine.domain.enums import (
            TaskCategory,
            TaskPriority,
            TaskStatus,
        )
        return NationalTask(
            id=model.id,
            title=model.title,
            description=model.description or "",
            status=TaskStatus(model.status),
            priority=TaskPriority(model.priority),
            category=TaskCategory(model.category),
            task_type=model.task_type or "general",
            assigned_to=model.assigned_to,
            assigned_by=model.assigned_by,
            queue_id=model.queue_id,
            workflow_id=model.workflow_id,
            workflow_execution_id=model.workflow_execution_id,
            parent_task_id=model.parent_task_id,
            sla_due_at=model.sla_due_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            tags=model.tags or [],
            metadata=model.extra_metadata or {},
            correlation_id=model.correlation_id,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )


class SQLAlchemyTaskQueueRepository(TaskQueueRepository):
    async def save(self, queue: Any) -> Any:
        return queue
    async def get(self, queue_id: str) -> Any:
        return None
    async def list(self, skip: int = 0, limit: int = 100, filters: dict | None = None) -> list:
        return []
    async def delete(self, queue_id: str) -> bool:
        return True

class SQLAlchemyTaskAssignmentRepository(TaskAssignmentRepository):
    async def save(self, assignment: Any) -> Any:
        return assignment
    async def get(self, assignment_id: str) -> Any:
        return None
    async def find_by_task(self, task_id: str) -> list:
        return []
    async def find_by_user(self, user_id: str) -> list:
        return []
    async def find_active(self, user_id: str) -> list:
        return []

class SQLAlchemyTaskEscalationRepository(TaskEscalationRepository):
    async def save(self, escalation: Any) -> Any:
        return escalation
    async def get(self, escalation_id: str) -> Any:
        return None
    async def find_by_task(self, task_id: str) -> list:
        return []
    async def find_active(self) -> list:
        return []

class SQLAlchemyTaskSLARepository(TaskSLARepository):
    async def save(self, sla: Any) -> Any:
        return sla
    async def get(self, sla_id: str) -> Any:
        return None
    async def find_by_task(self, task_id: str) -> Any:
        return None
    async def find_overdue(self) -> list:
        return []

class SQLAlchemyTaskCommentRepository(TaskCommentRepository):
    async def save(self, comment: Any) -> Any:
        return comment
    async def get(self, comment_id: str) -> Any:
        return None
    async def find_by_task(self, task_id: str) -> list:
        return []

class SQLAlchemyTaskAuditLogRepository(TaskAuditLogRepository):
    async def save(self, log: Any) -> Any:
        return log
    async def find_by_task(self, task_id: str) -> list:
        return []
    async def find_by_user(self, user_id: str) -> list:
        return []
    async def list(self, skip: int = 0, limit: int = 100, filters: dict | None = None) -> list:
        return []
