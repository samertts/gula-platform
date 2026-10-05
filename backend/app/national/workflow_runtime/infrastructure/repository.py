from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import desc, text

from app._compat import UTC
from app.database import SessionLocal
from app.national.workflow_runtime.domain.entities import (
    WorkflowDefinition,
    WorkflowExecution,
)
from app.national.workflow_runtime.domain.repository import (
    WorkflowApprovalRepository,
    WorkflowCompensationRepository,
    WorkflowDefinitionRepository,
    WorkflowExecutionRepository,
    WorkflowExecutionStepRepository,
    WorkflowTemplateRepository,
    WorkflowTimerRepository,
)
from app.national.workflow_runtime.infrastructure.models import (
    NationalWorkflowDefinition,
    NationalWorkflowExecution,
)

logger = logging.getLogger("gula.workflow_runtime.repository")


class SQLAlchemyWorkflowDefinitionRepository(WorkflowDefinitionRepository):
    async def save(self, definition: WorkflowDefinition) -> WorkflowDefinition:
        async with SessionLocal() as session:
            model = NationalWorkflowDefinition(
                id=definition.id,
                name=definition.name,
                description=definition.description,
                type=definition.type,
                version=definition.version,
                steps=[s.__dict__ for s in definition.steps],
                input_schema=definition.input_schema,
                output_schema=definition.output_schema,
                tags=definition.tags,
                extra_metadata=definition.metadata,
                status=definition.status,
                created_by=definition.created_by,
            )
            session.add(model)
            await session.commit()
            return definition

    async def get(self, definition_id: str) -> WorkflowDefinition | None:
        async with SessionLocal() as session:
            model = await session.get(NationalWorkflowDefinition, definition_id)
            if not model:
                return None
            return model.to_domain()

    async def list(
        self, skip: int = 0, limit: int = 100, filters: dict | None = None,
    ) -> list[WorkflowDefinition]:
        async with SessionLocal() as session:
            query = session.query(NationalWorkflowDefinition)
            if filters:
                if "type" in filters:
                    query = query.filter(NationalWorkflowDefinition.type == filters["type"])
                if "status" in filters:
                    query = query.filter(NationalWorkflowDefinition.status == filters["status"])
                if "search" in filters:
                    search = f"%{filters['search']}%"
                    query = query.filter(NationalWorkflowDefinition.name.like(search))
            query = query.order_by(desc(NationalWorkflowDefinition.created_at))
            query = query.offset(skip).limit(limit)
            results = await session.execute(query)
            return [row[0].to_domain() for row in results]

    async def find_by_type(self, type: str) -> list[WorkflowDefinition]:
        return await self.list(filters={"type": type})

    async def find_by_status(self, status: str) -> list[WorkflowDefinition]:
        return await self.list(filters={"status": status})

    async def find_by_tags(self, tags: list[str]) -> list[WorkflowDefinition]:
        async with SessionLocal() as session:
            query = session.query(NationalWorkflowDefinition)
            for tag in tags:
                query = query.filter(
                    NationalWorkflowDefinition.tags.contains(json.dumps(tag)),
                )
            results = await session.execute(query)
            return [row[0].to_domain() for row in results]

    async def find_active_version(self, type: str) -> WorkflowDefinition | None:
        async with SessionLocal() as session:
            model = await session.execute(
                session.query(NationalWorkflowDefinition)
                .filter(
                    NationalWorkflowDefinition.type == type,
                    NationalWorkflowDefinition.status == "active",
                )
                .order_by(desc(NationalWorkflowDefinition.version))
                .limit(1),
            )
            row = model.scalar_one_or_none()
            return row.to_domain() if row else None

    async def list_versions(self, type: str) -> list[WorkflowDefinition]:
        return await self.list(filters={"type": type})

    async def delete(self, definition_id: str) -> bool:
        async with SessionLocal() as session:
            model = await session.get(NationalWorkflowDefinition, definition_id)
            if not model:
                return False
            await session.delete(model)
            await session.commit()
            return True

    async def count(self, filters: dict | None = None) -> int:
        async with SessionLocal() as session:
            query = session.query(NationalWorkflowDefinition)
            if filters:
                if "type" in filters:
                    query = query.filter(NationalWorkflowDefinition.type == filters["type"])
                if "status" in filters:
                    query = query.filter(NationalWorkflowDefinition.status == filters["status"])
            result = await session.execute(query)
            return len(result.all())


class SQLAlchemyWorkflowExecutionRepository(WorkflowExecutionRepository):
    async def save(self, execution: WorkflowExecution) -> WorkflowExecution:
        async with SessionLocal() as session:
            model = await session.get(NationalWorkflowExecution, execution.id)
            if model:
                model.status = execution.status.value
                model.current_step = execution.current_step
                model.completed_at = execution.completed_at
                model.error = execution.error
                model.output_data = execution.output_data
                model.context = execution.context
                model.updated_at = datetime.now(UTC)
            else:
                model = NationalWorkflowExecution(
                    id=execution.id,
                    workflow_id=execution.workflow_id,
                    workflow_version=execution.workflow_version,
                    status=execution.status.value,
                    trigger=execution.trigger.value,
                    started_at=execution.started_at,
                    completed_at=execution.completed_at,
                    context=execution.context,
                    input_data=execution.input_data,
                    output_data=execution.output_data,
                    current_step=execution.current_step,
                    error=execution.error,
                    correlation_id=execution.correlation_id,
                    created_by=execution.created_by,
                    tenant_id=execution.tenant_id,
                )
                session.add(model)
            await session.commit()
            return execution

    async def get(self, execution_id: str) -> WorkflowExecution | None:
        async with SessionLocal() as session:
            model = await session.get(NationalWorkflowExecution, execution_id)
            if not model:
                return None
            return model.to_domain()

    async def list(
        self, skip: int = 0, limit: int = 100, filters: dict | None = None,
    ) -> list[WorkflowExecution]:
        async with SessionLocal() as session:
            query = session.query(NationalWorkflowExecution)
            if filters:
                for key, value in filters.items():
                    if hasattr(NationalWorkflowExecution, key):
                        query = query.filter(
                            getattr(NationalWorkflowExecution, key) == value,
                        )
            query = query.order_by(desc(NationalWorkflowExecution.created_at))
            query = query.offset(skip).limit(limit)
            results = await session.execute(query)
            return [row[0].to_domain() for row in results]

    async def find_by_status(self, status: str) -> list[WorkflowExecution]:
        return await self.list(filters={"status": status})

    async def find_by_trigger(self, trigger: str) -> list[WorkflowExecution]:
        return await self.list(filters={"trigger": trigger})

    async def find_by_correlation_id(
        self, correlation_id: str,
    ) -> list[WorkflowExecution]:
        return await self.list(filters={"correlation_id": correlation_id})

    async def find_stalled(
        self, timeout_minutes: int = 30,
    ) -> list[WorkflowExecution]:
        cutoff = datetime.now(UTC) - timedelta(minutes=timeout_minutes)
        async with SessionLocal() as session:
            query = session.query(NationalWorkflowExecution).filter(
                NationalWorkflowExecution.status == "running",
                NationalWorkflowExecution.updated_at < cutoff,
            )
            results = await session.execute(query)
            return [row[0].to_domain() for row in results]

    async def get_stats(self) -> dict[str, Any]:
        async with SessionLocal() as session:
            result = await session.execute(
                session.query(
                    NationalWorkflowExecution.status,
                    text("count(*) as cnt"),
                ).group_by(NationalWorkflowExecution.status),
            )
            stats = {"total": 0, "by_status": {}}
            for row in result:
                status = row[0]
                count = row[1]
                stats["by_status"][status] = count
                stats["total"] += count
            return stats

    async def count(self, filters: dict | None = None) -> int:
        async with SessionLocal() as session:
            query = session.query(NationalWorkflowExecution)
            if filters:
                for key, value in filters.items():
                    if hasattr(NationalWorkflowExecution, key):
                        query = query.filter(
                            getattr(NationalWorkflowExecution, key) == value,
                        )
            result = await session.execute(query)
            return len(result.all())


#: IA-071. Everything from here down persisted nothing, and unlike the
#: task_engine equivalent (IA-070) it was REACHABLE AND SERVED.
#:
#: Five of this file's seven repository classes contained no SQLAlchemy at all.
#: Measured by AST over the file: SQLAlchemyWorkflowDefinitionRepository (7
#: db-touching methods of 10) and SQLAlchemyWorkflowExecutionRepository (6 of
#: 9) are real; the other five had 20 methods between them and 0 that issue a
#: query. ``save`` returned its argument, ``get`` returned None, finders
#: returned [], and ``SQLAlchemyWorkflowTemplateRepository.delete`` returned
#: ``True`` -- reporting a deletion that never happened.
#:
#: The served consequence, measured over HTTP with an authenticated admin:
#:
#:     POST /national/workflows/templates
#:       -> 200 {"success":true,"id":"b4ebd8c9-4a67-440b-bb85-8173b19695a6"}
#:     GET  /national/workflows/templates
#:       -> 200 {"items":[],"total":0}
#:
#: The endpoint reported success AND minted an id the client could keep, while
#: storing nothing. GET /national/workflows/approvals/pending likewise answers
#: 200 {"approvals":[]} whatever has been approved, so an approval can be
#: recorded as saved and never appear in the pending queue it governs.
#:
#: Why this was not repaired by writing queries: no migration creates any of
#: this subsystem's eight tables (national_workflow_definitions, _executions,
#: _execution_steps, _approvals, _compensations, _timers, _templates,
#: national_saga_logs) -- each checked individually against
#: migrations/versions/, zero creating migrations. Real SQLAlchemy here would
#: raise "no such table", which is the honest answer but is reached more
#: cheaply, and without guessing at column names, by refusing outright.
#:
#: Correction to IA-058: that finding said this file "provides seven
#: SQLAlchemy* repositories" and treated the absent SagaLogRepository as the
#: only gap. Only two of the seven are real. IA-058's conclusion -- do not wire
#: these into app/platform/workflow.py -- holds and is strengthened; its stated
#: reason was incomplete.

WORKFLOW_UNAVAILABLE_REASON = (
    "the national workflow runtime has no persistence: none of its 8 tables "
    "has a creating migration, and 5 of its 7 repositories were never "
    "implemented. See IA-071."
)


class WorkflowRepositoryUnavailable(RuntimeError):
    """Raised instead of reporting a write, a deletion or a read that did not happen."""


class _UnavailableWorkflowRepository:
    """Every method refuses, naming itself.

    Methods are listed explicitly rather than caught by ``__getattr__`` so that
    a method added to an ABC later surfaces as a normal TypeError at
    instantiation instead of being absorbed into a refusal.
    """

    def _refuse(self, operation: str):
        name = f"{type(self).__name__}.{operation}"
        logger.warning("[WORKFLOW-RUNTIME] %s refused: %s", name, WORKFLOW_UNAVAILABLE_REASON)
        return WorkflowRepositoryUnavailable(f"{name} is unavailable: {WORKFLOW_UNAVAILABLE_REASON}")


class SQLAlchemyWorkflowExecutionStepRepository(
    _UnavailableWorkflowRepository, WorkflowExecutionStepRepository,
):
    async def save(self, step: Any) -> Any:
        raise self._refuse("save")

    async def get(self, step_id: str) -> Any:
        raise self._refuse("get")

    async def find_by_execution(self, execution_id: str) -> list:
        raise self._refuse("find_by_execution")

    async def find_by_status(self, status: str) -> list:
        raise self._refuse("find_by_status")

    async def find_by_execution_and_step(self, execution_id: str, step_id: str) -> Any:
        raise self._refuse("find_by_execution_and_step")


class SQLAlchemyWorkflowApprovalRepository(
    _UnavailableWorkflowRepository, WorkflowApprovalRepository,
):
    async def save(self, approval: Any) -> Any:
        raise self._refuse("save")

    async def get(self, approval_id: str) -> Any:
        raise self._refuse("get")

    async def find_pending_for_user(self, user_id: str) -> list:
        # Answered [] unconditionally, so an approval could be "saved" and then
        # never appear in the queue that governs it.
        raise self._refuse("find_pending_for_user")

    async def find_by_execution(self, execution_id: str) -> list:
        raise self._refuse("find_by_execution")


class SQLAlchemyWorkflowCompensationRepository(
    _UnavailableWorkflowRepository, WorkflowCompensationRepository,
):
    async def save(self, compensation: Any) -> Any:
        raise self._refuse("save")

    async def get(self, compensation_id: str) -> Any:
        raise self._refuse("get")

    async def find_by_execution(self, execution_id: str) -> list:
        raise self._refuse("find_by_execution")


class SQLAlchemyWorkflowTimerRepository(
    _UnavailableWorkflowRepository, WorkflowTimerRepository,
):
    async def save(self, timer: Any) -> Any:
        raise self._refuse("save")

    async def get(self, timer_id: str) -> Any:
        raise self._refuse("get")

    async def find_due_timers(self) -> list:
        raise self._refuse("find_due_timers")

    async def find_by_execution(self, execution_id: str) -> list:
        raise self._refuse("find_by_execution")


class SQLAlchemyWorkflowTemplateRepository(
    _UnavailableWorkflowRepository, WorkflowTemplateRepository,
):
    async def save(self, template: Any) -> Any:
        raise self._refuse("save")

    async def get(self, template_id: str) -> Any:
        raise self._refuse("get")

    async def list(self, skip: int = 0, limit: int = 100, filters: dict | None = None) -> list:
        raise self._refuse("list")

    async def delete(self, template_id: str) -> bool:
        # Returned True. A caller had no way to tell this from a real deletion.
        raise self._refuse("delete")
