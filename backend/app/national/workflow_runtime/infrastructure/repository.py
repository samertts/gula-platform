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
    WorkflowApprovalRepository,
    WorkflowCompensationRepository,
    WorkflowDefinitionRepository,
    WorkflowExecutionRepository,
    WorkflowExecutionStepRepository,
    WorkflowTemplateRepository,
    WorkflowTimerRepository,
)
from backend.app.national.workflow_runtime.infrastructure.models import (
    NationalWorkflowDefinition,
    NationalWorkflowExecution,
)

logger = logging.getLogger("gula.workflow_runtime.repository")


class SQLAlchemyWorkflowDefinitionRepository(WorkflowDefinitionRepository):
    def save(self, definition: WorkflowDefinition) -> WorkflowDefinition:
        with SessionLocal() as session:
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
            session.commit()
            return definition

    def get(self, definition_id: str) -> WorkflowDefinition | None:
        with SessionLocal() as session:
            model = session.get(NationalWorkflowDefinition, definition_id)
            if not model:
                return None
            return model.to_domain()

    def list(
        self, skip: int = 0, limit: int = 100, filters: dict | None = None,
    ) -> list[WorkflowDefinition]:
        with SessionLocal() as session:
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
            results = session.execute(query)
            return [row[0].to_domain() for row in results]

    def find_by_type(self, type: str) -> list[WorkflowDefinition]:
        return self.list(filters={"type": type})

    def find_by_status(self, status: str) -> list[WorkflowDefinition]:
        return self.list(filters={"status": status})

    def find_by_tags(self, tags: list[str]) -> list[WorkflowDefinition]:
        with SessionLocal() as session:
            query = session.query(NationalWorkflowDefinition)
            for tag in tags:
                query = query.filter(
                    NationalWorkflowDefinition.tags.contains(json.dumps(tag)),
                )
            results = session.execute(query)
            return [row[0].to_domain() for row in results]

    def find_active_version(self, type: str) -> WorkflowDefinition | None:
        with SessionLocal() as session:
            model = session.execute(
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

    def list_versions(self, type: str) -> list[WorkflowDefinition]:
        return self.list(filters={"type": type})

    def delete(self, definition_id: str) -> bool:
        with SessionLocal() as session:
            model = session.get(NationalWorkflowDefinition, definition_id)
            if not model:
                return False
            session.delete(model)
            session.commit()
            return True

    def count(self, filters: dict | None = None) -> int:
        with SessionLocal() as session:
            query = session.query(NationalWorkflowDefinition)
            if filters:
                if "type" in filters:
                    query = query.filter(NationalWorkflowDefinition.type == filters["type"])
                if "status" in filters:
                    query = query.filter(NationalWorkflowDefinition.status == filters["status"])
            result = session.execute(query)
            return len(result.all())


class SQLAlchemyWorkflowExecutionRepository(WorkflowExecutionRepository):
    def save(self, execution: WorkflowExecution) -> WorkflowExecution:
        with SessionLocal() as session:
            model = session.get(NationalWorkflowExecution, execution.id)
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
            session.commit()
            return execution

    def get(self, execution_id: str) -> WorkflowExecution | None:
        with SessionLocal() as session:
            model = session.get(NationalWorkflowExecution, execution_id)
            if not model:
                return None
            return model.to_domain()

    def list(
        self, skip: int = 0, limit: int = 100, filters: dict | None = None,
    ) -> list[WorkflowExecution]:
        with SessionLocal() as session:
            query = session.query(NationalWorkflowExecution)
            if filters:
                for key, value in filters.items():
                    if hasattr(NationalWorkflowExecution, key):
                        query = query.filter(
                            getattr(NationalWorkflowExecution, key) == value,
                        )
            query = query.order_by(desc(NationalWorkflowExecution.created_at))
            query = query.offset(skip).limit(limit)
            results = session.execute(query)
            return [row[0].to_domain() for row in results]

    def find_by_status(self, status: str) -> list[WorkflowExecution]:
        return self.list(filters={"status": status})

    def find_by_trigger(self, trigger: str) -> list[WorkflowExecution]:
        return self.list(filters={"trigger": trigger})

    def find_by_correlation_id(
        self, correlation_id: str,
    ) -> list[WorkflowExecution]:
        return self.list(filters={"correlation_id": correlation_id})

    def find_stalled(
        self, timeout_minutes: int = 30,
    ) -> list[WorkflowExecution]:
        cutoff = datetime.now(UTC) - timedelta(minutes=timeout_minutes)
        with SessionLocal() as session:
            query = session.query(NationalWorkflowExecution).filter(
                NationalWorkflowExecution.status == "running",
                NationalWorkflowExecution.updated_at < cutoff,
            )
            results = session.execute(query)
            return [row[0].to_domain() for row in results]

    def get_stats(self) -> dict[str, Any]:
        with SessionLocal() as session:
            result = session.execute(
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

    def count(self, filters: dict | None = None) -> int:
        with SessionLocal() as session:
            query = session.query(NationalWorkflowExecution)
            if filters:
                for key, value in filters.items():
                    if hasattr(NationalWorkflowExecution, key):
                        query = query.filter(
                            getattr(NationalWorkflowExecution, key) == value,
                        )
            result = session.execute(query)
            return len(result.all())


class SQLAlchemyWorkflowExecutionStepRepository(WorkflowExecutionStepRepository):
    def save(self, step: Any) -> Any:
        return step

    def get(self, step_id: str) -> Any:
        return None

    def find_by_execution(self, execution_id: str) -> list:
        return []

    def find_by_status(self, status: str) -> list:
        return []

    def find_by_execution_and_step(self, execution_id: str, step_id: str) -> Any:
        return None


class SQLAlchemyWorkflowApprovalRepository(WorkflowApprovalRepository):
    def save(self, approval: Any) -> Any:
        return approval

    def get(self, approval_id: str) -> Any:
        return None

    def find_pending_for_user(self, user_id: str) -> list:
        return []

    def find_by_execution(self, execution_id: str) -> list:
        return []


class SQLAlchemyWorkflowCompensationRepository(WorkflowCompensationRepository):
    def save(self, compensation: Any) -> Any:
        return compensation

    def get(self, compensation_id: str) -> Any:
        return None

    def find_by_execution(self, execution_id: str) -> list:
        return []


class SQLAlchemyWorkflowTimerRepository(WorkflowTimerRepository):
    def save(self, timer: Any) -> Any:
        return timer

    def get(self, timer_id: str) -> Any:
        return None

    def find_due_timers(self) -> list:
        return []

    def find_by_execution(self, execution_id: str) -> list:
        return []


class SQLAlchemyWorkflowTemplateRepository(WorkflowTemplateRepository):
    def save(self, template: Any) -> Any:
        return template

    def get(self, template_id: str) -> Any:
        return None

    def list(self, skip: int = 0, limit: int = 100, filters: dict | None = None) -> list:
        return []

    def delete(self, template_id: str) -> bool:
        return True
