from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import desc, text

from backend.app._compat import UTC
from backend.app.database import SessionLocal
from backend.app.national.workflow_runtime.domain.entities import (
    WorkflowDefinition,
    WorkflowExecution,
)
from backend.app.national.workflow_runtime.domain.repository import (
    WorkflowDefinitionRepository,
    WorkflowExecutionRepository,
)
from backend.app.national.workflow_runtime.infrastructure.models import (
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
                metadata=definition.metadata,
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
        self, skip: int = 0, limit: int = 100, filters: dict | None = None
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
                    NationalWorkflowDefinition.tags.contains(json.dumps(tag))
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
                .limit(1)
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
        self, skip: int = 0, limit: int = 100, filters: dict | None = None
    ) -> list[WorkflowExecution]:
        async with SessionLocal() as session:
            query = session.query(NationalWorkflowExecution)
            if filters:
                for key, value in filters.items():
                    if hasattr(NationalWorkflowExecution, key):
                        query = query.filter(
                            getattr(NationalWorkflowExecution, key) == value
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
        self, correlation_id: str
    ) -> list[WorkflowExecution]:
        return await self.list(filters={"correlation_id": correlation_id})

    async def find_stalled(
        self, timeout_minutes: int = 30
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
                ).group_by(NationalWorkflowExecution.status)
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
                            getattr(NationalWorkflowExecution, key) == value
                        )
            result = await session.execute(query)
            return len(result.all())
