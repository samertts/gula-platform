from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import desc, text

from app._compat import UTC
from app.database import SessionLocal
from app.national.task_engine.domain.entities import (
    NationalTask,
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
from app.national.task_engine.infrastructure.models import (
    NationalTaskModel,
)


logger = logging.getLogger("gula.national.task_engine.repository")


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
        from app.national.task_engine.domain.enums import (
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


#: IA-070. Everything from here down persisted nothing. Six classes named
#: ``SQLAlchemy*Repository`` contained no SQLAlchemy at all: ``save`` returned
#: its argument without writing, ``get`` returned ``None``, and every finder
#: returned ``[]``. An AST pass over this file measured it -- of 7 repository
#: classes, only ``SQLAlchemyNationalTaskRepository`` touches the database; the
#: other 6 had 24 methods between them and 0 that issue a query.
#:
#: ``save`` returning the entity is the dangerous shape: a caller gets its
#: object back and has every reason to believe it was stored. One of these is
#: ``SQLAlchemyTaskAuditLogRepository``, so the audit log discarded every write
#: while reporting success -- against CLAUDE.md security invariant 2.
#:
#: WHY THIS WAS NOT REPAIRED BY IMPLEMENTING THE QUERIES. All 7 task_engine
#: tables -- national_tasks, _task_queues, _task_assignments, _task_escalations,
#: _task_sla_definitions, _task_comments, _task_audit_logs -- have zero
#: creating migrations, checked individually against migrations/versions/. So
#: writing real SQLAlchemy here would produce "no such table" rather than
#: persistence.
#:
#: WHY IT MATTERED ANYWAY, despite nothing reaching these today. All 29 routes
#: in api/routes.py call _get_service(), which constructs all seven and raises
#:
#:     TypeError: Can't instantiate abstract class
#:     SQLAlchemyTaskAssignmentRepository without an implementation for
#:     abstract method 'find_by_assignee'
#:
#: The two classes that left abstract methods unimplemented were acting as an
#: accidental circuit breaker in front of the other 24 silent methods. The
#: obvious repair for that TypeError -- implement the 3 missing methods so the
#: classes instantiate -- would have unblocked construction and exposed every
#: one of them, turning a loud failure into silent data loss across the whole
#: task engine, audit log included.
#:
#: So the missing methods ARE implemented, as refusals, and so is every other
#: method here. The classes are now constructible and honest: whichever path a
#: caller takes it fails loudly, and no later change can expose a discard that
#: no longer exists.

TASK_ENGINE_UNAVAILABLE_REASON = (
    "the national task engine has no persistence: none of its 7 tables has a "
    "creating migration, and 6 of its 7 repositories were never implemented. "
    "See IA-070."
)


class TaskEngineRepositoryUnavailable(RuntimeError):
    """Raised instead of silently discarding a write or inventing a read."""


class _UnavailableRepository:
    """Every method refuses, naming itself.

    Subclasses list their contract's methods explicitly rather than catching
    them with ``__getattr__``, so a method added to an ABC later shows up as a
    normal TypeError at instantiation instead of being silently absorbed into
    a refusal. A refusal must never be the thing that hides a contract change.
    """

    def _refuse(self, operation: str):
        name = f"{type(self).__name__}.{operation}"
        logger.warning("[TASK-ENGINE] %s refused: %s", name, TASK_ENGINE_UNAVAILABLE_REASON)
        return TaskEngineRepositoryUnavailable(f"{name} is unavailable: {TASK_ENGINE_UNAVAILABLE_REASON}")


class SQLAlchemyTaskQueueRepository(_UnavailableRepository, TaskQueueRepository):
    async def save(self, queue: Any) -> Any:
        raise self._refuse("save")

    async def get(self, queue_id: str) -> Any:
        raise self._refuse("get")

    async def list(self) -> list:
        raise self._refuse("list")

    async def delete(self, queue_id: str) -> bool:
        raise self._refuse("delete")


class SQLAlchemyTaskAssignmentRepository(_UnavailableRepository, TaskAssignmentRepository):
    async def save(self, assignment: Any) -> Any:
        raise self._refuse("save")

    async def get(self, assignment_id: str) -> Any:
        raise self._refuse("get")

    async def find_by_task(self, task_id: str) -> list:
        raise self._refuse("find_by_task")

    async def find_by_assignee(self, assignee_id: str) -> list:
        # The abstract method whose absence raised the TypeError above.
        raise self._refuse("find_by_assignee")

    async def find_by_user(self, user_id: str) -> list:
        raise self._refuse("find_by_user")

    async def find_active(self, user_id: str) -> list:
        raise self._refuse("find_active")


class SQLAlchemyTaskEscalationRepository(_UnavailableRepository, TaskEscalationRepository):
    async def save(self, escalation: Any) -> Any:
        raise self._refuse("save")

    async def get(self, escalation_id: str) -> Any:
        raise self._refuse("get")

    async def find_by_task(self, task_id: str) -> list:
        raise self._refuse("find_by_task")

    async def find_active(self) -> list:
        raise self._refuse("find_active")


class SQLAlchemyTaskSLARepository(_UnavailableRepository, TaskSLARepository):
    async def save(self, sla: Any) -> Any:
        raise self._refuse("save")

    async def get(self, sla_id: str) -> Any:
        raise self._refuse("get")

    async def find_by_task(self, task_id: str) -> Any:
        raise self._refuse("find_by_task")

    async def find_by_category_and_priority(self, category: str, priority: str) -> Any:
        # Abstract method that was missing.
        raise self._refuse("find_by_category_and_priority")

    async def list(self) -> list:
        # Abstract method that was missing.
        raise self._refuse("list")

    async def find_overdue(self) -> list:
        raise self._refuse("find_overdue")


class SQLAlchemyTaskCommentRepository(_UnavailableRepository, TaskCommentRepository):
    async def save(self, comment: Any) -> Any:
        raise self._refuse("save")

    async def get(self, comment_id: str) -> Any:
        raise self._refuse("get")

    async def find_by_task(self, task_id: str) -> list:
        raise self._refuse("find_by_task")


class SQLAlchemyTaskAuditLogRepository(_UnavailableRepository, TaskAuditLogRepository):
    """The audit log. This one discarded every write while reporting success."""

    async def save(self, log: Any) -> Any:
        raise self._refuse("save")

    async def find_by_task(self, task_id: str) -> list:
        raise self._refuse("find_by_task")

    async def find_by_user(self, user_id: str) -> list:
        raise self._refuse("find_by_user")

    async def list(self, skip: int = 0, limit: int = 100, filters: dict | None = None) -> list:
        raise self._refuse("list")
