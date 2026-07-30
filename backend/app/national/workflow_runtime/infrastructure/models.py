from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON

from app.national.base import BaseEntity, NationalBase


class NationalWorkflowDefinition(BaseEntity, NationalBase):
    __tablename__ = "national_workflow_definitions"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    type = Column(String(100), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    steps = Column(JSON, default=list, nullable=True)
    input_schema = Column(JSON, default=dict, nullable=True)
    output_schema = Column(JSON, default=dict, nullable=True)
    tags = Column(JSON, default=list, nullable=True)
    extra_metadata = Column(JSON, default=dict, nullable=True)
    status = Column(String(50), default="active", nullable=False, index=True)
    timeout_policy = Column(String(50), default="fail", nullable=True)
    compensation_strategy = Column(String(50), default="reverse_order", nullable=True)
    is_template = Column(Integer, default=0, nullable=False)
    created_by = Column(String(100), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    def to_domain(self) -> dict[str, Any]:
        from backend.app.national.workflow_runtime.domain.entities import (
            WorkflowDefinition,
            WorkflowStepDefinition,
        )

        steps = []
        for s in self.steps or []:
            steps.append(WorkflowStepDefinition(**s))
        return WorkflowDefinition(
            id=self.id,
            name=self.name,
            description=self.description or "",
            type=self.type,
            version=self.version,
            steps=steps,
            input_schema=self.input_schema or {},
            output_schema=self.output_schema or {},
            tags=self.tags or [],
            metadata=self.extra_metadata or {},
            status=self.status,
            created_by=self.created_by,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class NationalWorkflowExecution(BaseEntity, NationalBase):
    __tablename__ = "national_workflow_executions"

    workflow_id = Column(String(26), nullable=False, index=True)
    workflow_version = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default="pending", nullable=False, index=True)
    trigger = Column(String(50), default="manual", nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    context = Column(JSON, default=dict, nullable=True)
    input_data = Column(JSON, default=dict, nullable=True)
    output_data = Column(JSON, default=dict, nullable=True)
    current_step = Column(String(100), nullable=True)
    error = Column(Text, nullable=True)
    correlation_id = Column(String(255), nullable=True, index=True)
    created_by = Column(String(100), nullable=True)
    tenant_id = Column(String(100), nullable=True, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    def to_domain(self):
        from backend.app.national.workflow_runtime.domain.entities import (
            WorkflowExecution,
        )
        from backend.app.national.workflow_runtime.domain.enums import (
            WorkflowExecutionStatus,
            WorkflowTrigger,
        )

        return WorkflowExecution(
            id=self.id,
            workflow_id=self.workflow_id,
            workflow_version=self.workflow_version,
            status=WorkflowExecutionStatus(self.status),
            trigger=WorkflowTrigger(self.trigger),
            started_at=self.started_at,
            completed_at=self.completed_at,
            context=self.context or {},
            input_data=self.input_data or {},
            output_data=self.output_data or {},
            current_step=self.current_step or "",
            error=self.error,
            correlation_id=self.correlation_id,
            created_by=self.created_by,
            tenant_id=self.tenant_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class NationalWorkflowExecutionStep(BaseEntity, NationalBase):
    __tablename__ = "national_workflow_execution_steps"

    execution_id = Column(String(26), nullable=False, index=True)
    step_id = Column(String(100), nullable=False)
    step_name = Column(String(255), nullable=True)
    status = Column(String(50), default="pending", nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    result = Column(JSON, default=dict, nullable=True)
    error = Column(Text, nullable=True)
    attempt = Column(Integer, default=0, nullable=False)
    assigned_to = Column(String(100), nullable=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Integer, default=0, nullable=True)


class NationalWorkflowApproval(BaseEntity, NationalBase):
    __tablename__ = "national_workflow_approvals"

    execution_id = Column(String(26), nullable=False, index=True)
    step_id = Column(String(100), nullable=False)
    approver_id = Column(String(100), nullable=True, index=True)
    approver_name = Column(String(255), nullable=True)
    status = Column(String(50), default="pending", nullable=False)
    comments = Column(Text, nullable=True)
    assigned_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    responded_at = Column(DateTime(timezone=True), nullable=True)


class NationalWorkflowCompensation(BaseEntity, NationalBase):
    __tablename__ = "national_workflow_compensations"

    execution_id = Column(String(26), nullable=False, index=True)
    step_id = Column(String(100), nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)


class NationalWorkflowTimer(BaseEntity, NationalBase):
    __tablename__ = "national_workflow_timers"

    execution_id = Column(String(26), nullable=False, index=True)
    step_id = Column(String(100), nullable=False)
    fire_at = Column(DateTime(timezone=True), nullable=False, index=True)
    action = Column(String(50), default="timeout", nullable=False)
    status = Column(String(50), default="active", nullable=False, index=True)


class NationalSagaLog(BaseEntity, NationalBase):
    __tablename__ = "national_saga_logs"

    saga_id = Column(String(100), nullable=False, index=True)
    step_id = Column(String(100), nullable=False)
    step_type = Column(String(50), default="task", nullable=False)
    action = Column(String(50), default="forward", nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    data = Column(JSON, default=dict, nullable=True)
    error = Column(Text, nullable=True)


class NationalWorkflowTemplate(BaseEntity, NationalBase):
    __tablename__ = "national_workflow_templates"

    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    definition = Column(JSON, default=dict, nullable=False)
    parameters = Column(JSON, default=dict, nullable=True)
    category = Column(String(100), default="general", nullable=False, index=True)
    tags = Column(JSON, default=list, nullable=True)
    created_by = Column(String(100), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
