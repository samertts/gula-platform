from __future__ import annotations

from datetime import datetime

from app._compat import UTC
from app.national.background_platform.domain.enums import (
    DependencyType,
    JobCategory,
    JobPriority,
    JobStatus,
    ScheduleType,
)
from app.national.base import BaseEntity, _ulid
from sqlalchemy import JSON, Boolean, Column, DateTime, Enum as SAEnum, Float, ForeignKey, Index, Integer, String, Text


class NationalJob(BaseEntity):
    __tablename__ = "national_background_jobs"

    id = Column(String(26), primary_key=True, default=_ulid)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True, default="")
    type = Column(String(100), nullable=False, index=True)
    priority = Column(SAEnum(JobPriority), nullable=False, default=JobPriority.MEDIUM, index=True)
    category = Column(SAEnum(JobCategory), nullable=False, default=JobCategory.OTHER, index=True)
    max_retries = Column(Integer, nullable=False, default=3)
    timeout_s = Column(Integer, nullable=False, default=300)
    tags = Column(JSON, nullable=True, default=list)
    metadata_ = Column("metadata", JSON, nullable=True, default=dict)
    version = Column(Integer, nullable=False, default=1)
    status = Column(SAEnum(JobStatus), nullable=False, default=JobStatus.PENDING, index=True)
    created_by = Column(String(100), nullable=True)

    __table_args__ = (
        Index("ix_nat_bg_jobs_status_category", "status", "category"),
        Index("ix_nat_bg_jobs_priority_status", "priority", "status"),
        Index("ix_nat_bg_jobs_type_category", "type", "category"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.background_platform.domain.entities import JobDefinition

        return JobDefinition(
            id=self.id,
            name=self.name,
            description=self.description or "",
            type=self.type,
            priority=self.priority,
            category=self.category,
            max_retries=self.max_retries,
            timeout_s=self.timeout_s,
            tags=self.tags or [],
            metadata=self.metadata_ or {},
            created_by=self.created_by or "",
            created_at=self.created_at,
            version=self.version,
            status=self.status,
        )


class NationalJobSchedule(BaseEntity):
    __tablename__ = "national_background_job_schedules"

    id = Column(String(26), primary_key=True, default=_ulid)
    job_id = Column(String(26), ForeignKey("national_background_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    schedule_type = Column(SAEnum(ScheduleType), nullable=False, default=ScheduleType.ONCE)
    cron_expression = Column(String(255), nullable=True, default="")
    interval_seconds = Column(Integer, nullable=False, default=0)
    start_at = Column(DateTime(timezone=True), nullable=True)
    end_at = Column(DateTime(timezone=True), nullable=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True)
    timezone = Column(String(50), nullable=False, default="UTC")
    enabled = Column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("ix_nat_bg_sched_job_enabled", "job_id", "enabled"),
        Index("ix_nat_bg_sched_due", "enabled", "next_run_at"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.background_platform.domain.entities import JobSchedule

        return JobSchedule(
            id=self.id,
            job_id=self.job_id,
            schedule_type=self.schedule_type,
            cron_expression=self.cron_expression or "",
            interval_seconds=self.interval_seconds,
            start_at=self.start_at,
            end_at=self.end_at,
            last_run_at=self.last_run_at,
            next_run_at=self.next_run_at,
            timezone=self.timezone,
            enabled=self.enabled,
            created_at=self.created_at,
        )


class NationalJobExecution(BaseEntity):
    __tablename__ = "national_background_job_executions"

    id = Column(String(26), primary_key=True, default=_ulid)
    job_id = Column(String(26), ForeignKey("national_background_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_start = Column(DateTime(timezone=True), nullable=True)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(SAEnum(JobStatus), nullable=False, default=JobStatus.PENDING, index=True)
    worker_id = Column(String(100), nullable=True, default="")
    attempt = Column(Integer, nullable=False, default=0)
    result = Column(JSON, nullable=True, default=dict)
    error = Column(Text, nullable=True, default="")
    duration_ms = Column(Float, nullable=False, default=0.0)

    __table_args__ = (
        Index("ix_nat_bg_exec_job_status", "job_id", "status"),
        Index("ix_nat_bg_exec_status_created", "status", "created_at"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.background_platform.domain.entities import JobExecution

        return JobExecution(
            id=self.id,
            job_id=self.job_id,
            scheduled_start=self.scheduled_start,
            actual_start=self.actual_start,
            completed_at=self.completed_at,
            status=self.status,
            worker_id=self.worker_id or "",
            attempt=self.attempt,
            result=self.result or {},
            error=self.error or "",
            duration_ms=self.duration_ms,
            created_at=self.created_at,
        )


class NationalJobDependency(BaseEntity):
    __tablename__ = "national_background_job_dependencies"

    id = Column(String(26), primary_key=True, default=_ulid)
    job_id = Column(String(26), ForeignKey("national_background_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    depends_on_job_id = Column(String(26), ForeignKey("national_background_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    dependency_type = Column(SAEnum(DependencyType), nullable=False, default=DependencyType.SUCCESS)

    __table_args__ = (
        Index("ix_nat_bg_dep_job_depends", "job_id", "depends_on_job_id", unique=True),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.background_platform.domain.entities import JobDependency

        return JobDependency(
            id=self.id,
            job_id=self.job_id,
            depends_on_job_id=self.depends_on_job_id,
            dependency_type=self.dependency_type,
        )
