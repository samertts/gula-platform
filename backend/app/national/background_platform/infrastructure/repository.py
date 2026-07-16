from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC
from app.national.background_platform.domain.entities import (
    JobDefinition,
    JobDependency,
    JobExecution,
    JobSchedule,
)
from app.national.background_platform.domain.enums import JobCategory, JobPriority, JobStatus
from app.national.background_platform.domain.repository import (
    JobDependencyRepository,
    JobExecutionRepository,
    JobRepository,
    JobScheduleRepository,
)
from app.national.background_platform.infrastructure.models import (
    NationalJob,
    NationalJobDependency,
    NationalJobExecution,
    NationalJobSchedule,
)


class SQLAlchemyJobRepository(JobRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, job: JobDefinition) -> JobDefinition:
        model = self.db.query(NationalJob).filter(NationalJob.id == job.id).first()
        if model:
            model.name = job.name
            model.description = job.description
            model.type = job.type
            model.priority = job.priority
            model.category = job.category
            model.max_retries = job.max_retries
            model.timeout_s = job.timeout_s
            model.tags = job.tags
            model.metadata_ = job.metadata
            model.version = job.version
            model.status = job.status
            model.created_by = job.created_by
        else:
            model = NationalJob(
                id=job.id,
                name=job.name,
                description=job.description,
                type=job.type,
                priority=job.priority,
                category=job.category,
                max_retries=job.max_retries,
                timeout_s=job.timeout_s,
                tags=job.tags,
                metadata_=job.metadata,
                version=job.version,
                status=job.status,
                created_by=job.created_by,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, job_id: str) -> JobDefinition | None:
        model = self.db.query(NationalJob).filter(
            NationalJob.id == job_id,
            ~NationalJob.is_deleted,
        ).first()
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[JobDefinition]:
        query = self.db.query(NationalJob).filter(~~NationalJob.is_deleted)
        for key, value in filters.items():
            if hasattr(NationalJob, key) and value is not None:
                query = query.filter(getattr(NationalJob, key) == value)
        models = query.order_by(NationalJob.created_at.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def delete(self, job_id: str, soft: bool = True) -> None:
        model = self.db.query(NationalJob).filter(
            NationalJob.id == job_id,
            ~NationalJob.is_deleted,
        ).first()
        if model:
            if soft:
                model.is_deleted = True
                model.deleted_at = datetime.now(UTC)
            else:
                self.db.delete(model)
            self.db.commit()

    async def find_by_status(
        self,
        status: JobStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobDefinition]:
        models = self.db.query(NationalJob).filter(
            NationalJob.status == status,
            ~NationalJob.is_deleted,
        ).order_by(NationalJob.created_at.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def find_by_category(
        self,
        category: JobCategory,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobDefinition]:
        models = self.db.query(NationalJob).filter(
            NationalJob.category == category,
            ~NationalJob.is_deleted,
        ).order_by(NationalJob.created_at.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def find_by_priority(
        self,
        priority: JobPriority,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobDefinition]:
        models = self.db.query(NationalJob).filter(
            NationalJob.priority == priority,
            ~NationalJob.is_deleted,
        ).order_by(NationalJob.created_at.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def find_due(
        self,
        before: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobDefinition]:
        before or datetime.now(UTC)
        models = self.db.query(NationalJob).filter(
            NationalJob.status == JobStatus.PENDING,
            ~NationalJob.is_deleted,
        ).order_by(NationalJob.created_at.asc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def count_by_status(self, status: JobStatus) -> int:
        return self.db.query(NationalJob).filter(
            NationalJob.status == status,
            ~NationalJob.is_deleted,
        ).count()


class SQLAlchemyJobScheduleRepository(JobScheduleRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, schedule: JobSchedule) -> JobSchedule:
        model = self.db.query(NationalJobSchedule).filter(NationalJobSchedule.id == schedule.id).first()
        if model:
            model.job_id = schedule.job_id
            model.schedule_type = schedule.schedule_type
            model.cron_expression = schedule.cron_expression
            model.interval_seconds = schedule.interval_seconds
            model.start_at = schedule.start_at
            model.end_at = schedule.end_at
            model.last_run_at = schedule.last_run_at
            model.next_run_at = schedule.next_run_at
            model.timezone = schedule.timezone
            model.enabled = schedule.enabled
        else:
            model = NationalJobSchedule(
                id=schedule.id,
                job_id=schedule.job_id,
                schedule_type=schedule.schedule_type,
                cron_expression=schedule.cron_expression,
                interval_seconds=schedule.interval_seconds,
                start_at=schedule.start_at,
                end_at=schedule.end_at,
                last_run_at=schedule.last_run_at,
                next_run_at=schedule.next_run_at,
                timezone=schedule.timezone,
                enabled=schedule.enabled,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, schedule_id: str) -> JobSchedule | None:
        model = self.db.query(NationalJobSchedule).filter(
            NationalJobSchedule.id == schedule_id,
            ~NationalJobSchedule.is_deleted,
        ).first()
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[JobSchedule]:
        query = self.db.query(NationalJobSchedule).filter(~~NationalJobSchedule.is_deleted)
        for key, value in filters.items():
            if hasattr(NationalJobSchedule, key) and value is not None:
                query = query.filter(getattr(NationalJobSchedule, key) == value)
        models = query.order_by(NationalJobSchedule.created_at.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def delete(self, schedule_id: str) -> None:
        model = self.db.query(NationalJobSchedule).filter(
            NationalJobSchedule.id == schedule_id,
        ).first()
        if model:
            model.is_deleted = True
            model.deleted_at = datetime.now(UTC)
            self.db.commit()

    async def find_due_schedules(
        self,
        before: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobSchedule]:
        cutoff = before or datetime.now(UTC)
        models = self.db.query(NationalJobSchedule).filter(
            NationalJobSchedule.enabled,
            ~NationalJobSchedule.is_deleted,
            NationalJobSchedule.next_run_at <= cutoff,
            (NationalJobSchedule.end_at is None) | (NationalJobSchedule.end_at > cutoff),
        ).order_by(NationalJobSchedule.next_run_at.asc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def find_by_job_id(
        self,
        job_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobSchedule]:
        models = self.db.query(NationalJobSchedule).filter(
            NationalJobSchedule.job_id == job_id,
            ~NationalJobSchedule.is_deleted,
        ).order_by(NationalJobSchedule.created_at.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]


class SQLAlchemyJobExecutionRepository(JobExecutionRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, execution: JobExecution) -> JobExecution:
        model = self.db.query(NationalJobExecution).filter(NationalJobExecution.id == execution.id).first()
        if model:
            model.job_id = execution.job_id
            model.scheduled_start = execution.scheduled_start
            model.actual_start = execution.actual_start
            model.completed_at = execution.completed_at
            model.status = execution.status
            model.worker_id = execution.worker_id
            model.attempt = execution.attempt
            model.result = execution.result
            model.error = execution.error
            model.duration_ms = execution.duration_ms
        else:
            model = NationalJobExecution(
                id=execution.id,
                job_id=execution.job_id,
                scheduled_start=execution.scheduled_start,
                actual_start=execution.actual_start,
                completed_at=execution.completed_at,
                status=execution.status,
                worker_id=execution.worker_id,
                attempt=execution.attempt,
                result=execution.result,
                error=execution.error,
                duration_ms=execution.duration_ms,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, execution_id: str) -> JobExecution | None:
        model = self.db.query(NationalJobExecution).filter(
            NationalJobExecution.id == execution_id,
        ).first()
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[JobExecution]:
        query = self.db.query(NationalJobExecution)
        for key, value in filters.items():
            if hasattr(NationalJobExecution, key) and value is not None:
                query = query.filter(getattr(NationalJobExecution, key) == value)
        models = query.order_by(NationalJobExecution.created_at.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def find_by_job_id(
        self,
        job_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobExecution]:
        models = self.db.query(NationalJobExecution).filter(
            NationalJobExecution.job_id == job_id,
        ).order_by(NationalJobExecution.created_at.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def find_recent(
        self,
        limit: int = 50,
        status: JobStatus | None = None,
    ) -> list[JobExecution]:
        query = self.db.query(NationalJobExecution)
        if status is not None:
            query = query.filter(NationalJobExecution.status == status)
        models = query.order_by(NationalJobExecution.created_at.desc()).limit(limit).all()
        return [m.to_domain() for m in models]

    async def get_stats(self) -> dict[str, Any]:
        total = self.db.query(func.count(NationalJobExecution.id)).scalar() or 0
        avg_duration = self.db.query(
            func.avg(NationalJobExecution.duration_ms),
        ).filter(
            NationalJobExecution.status == JobStatus.COMPLETED,
        ).scalar() or 0.0

        by_status = {}
        for status in JobStatus:
            count = self.db.query(func.count(NationalJobExecution.id)).filter(
                NationalJobExecution.status == status,
            ).scalar() or 0
            if count > 0:
                by_status[status.value] = count

        return {
            "total": total,
            "avg_duration_ms": round(float(avg_duration), 2),
            "by_status": by_status,
        }


class SQLAlchemyJobDependencyRepository(JobDependencyRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, dependency: JobDependency) -> JobDependency:
        model = self.db.query(NationalJobDependency).filter(
            NationalJobDependency.id == dependency.id,
        ).first()
        if model:
            model.job_id = dependency.job_id
            model.depends_on_job_id = dependency.depends_on_job_id
            model.dependency_type = dependency.dependency_type
        else:
            model = NationalJobDependency(
                id=dependency.id,
                job_id=dependency.job_id,
                depends_on_job_id=dependency.depends_on_job_id,
                dependency_type=dependency.dependency_type,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, dependency_id: str) -> JobDependency | None:
        model = self.db.query(NationalJobDependency).filter(
            NationalJobDependency.id == dependency_id,
        ).first()
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[JobDependency]:
        query = self.db.query(NationalJobDependency)
        for key, value in filters.items():
            if hasattr(NationalJobDependency, key) and value is not None:
                query = query.filter(getattr(NationalJobDependency, key) == value)
        models = query.offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def delete(self, dependency_id: str) -> None:
        model = self.db.query(NationalJobDependency).filter(
            NationalJobDependency.id == dependency_id,
        ).first()
        if model:
            self.db.delete(model)
            self.db.commit()

    async def find_by_job_id(
        self,
        job_id: str,
    ) -> list[JobDependency]:
        models = self.db.query(NationalJobDependency).filter(
            NationalJobDependency.job_id == job_id,
        ).all()
        return [m.to_domain() for m in models]

    async def find_dependents(
        self,
        depends_on_job_id: str,
    ) -> list[JobDependency]:
        models = self.db.query(NationalJobDependency).filter(
            NationalJobDependency.depends_on_job_id == depends_on_job_id,
        ).all()
        return [m.to_domain() for m in models]
