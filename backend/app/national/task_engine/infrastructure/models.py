from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON

from app.national.base import BaseEntity, NationalBase


class NationalTaskModel(BaseEntity, NationalBase):
    __tablename__ = "national_tasks"

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending", nullable=False, index=True)
    priority = Column(String(50), default="medium", nullable=False, index=True)
    category = Column(String(50), default="general", nullable=False, index=True)
    task_type = Column(String(100), default="general", nullable=True, index=True)
    assigned_to = Column(String(100), nullable=True, index=True)
    assigned_by = Column(String(100), nullable=True)
    queue_id = Column(String(26), nullable=True, index=True)
    workflow_id = Column(String(100), nullable=True)
    workflow_execution_id = Column(String(100), nullable=True)
    parent_task_id = Column(String(26), nullable=True)
    sla_due_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    escalation_level = Column(Integer, default=1, nullable=True)
    tags = Column(JSON, default=list, nullable=True)
    extra_metadata = Column(JSON, default=dict, nullable=True)
    correlation_id = Column(String(255), nullable=True, index=True)
    created_by = Column(String(100), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    version = Column(Integer, default=1, nullable=False)


class NationalTaskQueueModel(BaseEntity, NationalBase):
    __tablename__ = "national_task_queues"

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assignment_strategy = Column(String(50), default="manual", nullable=False)
    max_concurrent = Column(Integer, default=10, nullable=True)
    max_waiting_time_s = Column(Integer, default=3600, nullable=True)
    allowed_roles = Column(JSON, default=list, nullable=True)
    allowed_categories = Column(JSON, default=list, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class NationalTaskAssignmentModel(BaseEntity, NationalBase):
    __tablename__ = "national_task_assignments"

    task_id = Column(String(26), nullable=False, index=True)
    assignee_id = Column(String(100), nullable=False, index=True)
    assigned_by = Column(String(100), nullable=True)
    assigned_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    assignment_strategy = Column(String(50), default="manual", nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="assigned", nullable=True)


class NationalTaskEscalationModel(BaseEntity, NationalBase):
    __tablename__ = "national_task_escalations"

    task_id = Column(String(26), nullable=False, index=True)
    level = Column(Integer, default=1, nullable=True)
    escalated_to = Column(String(100), nullable=True, index=True)
    escalated_by = Column(String(100), nullable=True)
    reason = Column(Text, nullable=True)
    escalated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="active", nullable=True)


class NationalTaskSLAModel(BaseEntity, NationalBase):
    __tablename__ = "national_task_sla_definitions"

    task_category = Column(String(50), nullable=False, index=True)
    task_type = Column(String(100), nullable=True)
    priority = Column(String(50), nullable=False, index=True)
    warning_threshold_s = Column(Integer, default=3600, nullable=True)
    breach_threshold_s = Column(Integer, default=7200, nullable=True)
    notification_enabled = Column(Integer, default=1, nullable=True)
    escalation_enabled = Column(Integer, default=1, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class NationalTaskCommentModel(BaseEntity, NationalBase):
    __tablename__ = "national_task_comments"

    task_id = Column(String(26), nullable=False, index=True)
    author_id = Column(String(100), nullable=True)
    author_name = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class NationalTaskAuditLogModel(BaseEntity, NationalBase):
    __tablename__ = "national_task_audit_logs"

    task_id = Column(String(26), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    actor_id = Column(String(100), nullable=True)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    details = Column(JSON, default=dict, nullable=True)
