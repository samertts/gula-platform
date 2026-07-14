from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.kernel.event_bus.bus import EventBus
from app.kernel.event_bus.events import Event
from app.national.background_platform.application.interfaces import (
    JobExecutor,
    ScheduleCalculator,
    SimpleScheduleCalculator,
)
from app.national.background_platform.domain.entities import (
    JobDefinition,
    JobDependency,
    JobExecution,
    JobSchedule,
)
from app.national.background_platform.domain.enums import (
    DependencyType,
    JobCategory,
    JobPriority,
    JobStatus,
    ScheduleType,
)
from app.national.background_platform.domain.events import (
    JobCancelledEvent,
    JobCompletedEvent,
    JobCreatedEvent,
    JobFailedEvent,
    JobPausedEvent,
    JobResumedEvent,
    JobScheduledEvent,
    JobStartedEvent,
    JobTimedOutEvent,
)
from app.national.background_platform.domain.repository import (
    JobDependencyRepository,
    JobExecutionRepository,
    JobRepository,
    JobScheduleRepository,
)
from app.national.background_platform.exceptions import (
    JobDependencyError,
    JobExecutionError,
    JobNotFoundError,
    JobScheduleNotFoundError,
    JobStateTransitionError,
    JobValidationError,
)
from app.notifications.service import NotificationService
from app.tasks.queue import task_queue
from app.tasks.schema import TaskPayload

logger = logging.getLogger("gula.national.background_platform")


_ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.PENDING: {JobStatus.RUNNING, JobStatus.CANCELLED, JobStatus.PAUSED},
    JobStatus.RUNNING: {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.TIMED_OUT},
    JobStatus.PAUSED: {JobStatus.PENDING, JobStatus.CANCELLED},
    JobStatus.FAILED: {JobStatus.PENDING, JobStatus.RETRYING, JobStatus.CANCELLED},
    JobStatus.RETRYING: {JobStatus.PENDING, JobStatus.RUNNING, JobStatus.FAILED, JobStatus.DEAD},
    JobStatus.TIMED_OUT: {JobStatus.PENDING, JobStatus.CANCELLED},
    JobStatus.COMPLETED: set(),
    JobStatus.CANCELLED: set(),
    JobStatus.DEAD: set(),
}


class JobService:

    def __init__(
        self,
        job_repository: JobRepository,
        schedule_repository: JobScheduleRepository,
        execution_repository: JobExecutionRepository,
        dependency_repository: JobDependencyRepository,
        event_bus: EventBus,
        job_executor: JobExecutor | None = None,
        schedule_calculator: ScheduleCalculator | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.job_repository = job_repository
        self.schedule_repository = schedule_repository
        self.execution_repository = execution_repository
        self.dependency_repository = dependency_repository
        self.event_bus = event_bus
        self.job_executor = job_executor
        self.schedule_calculator = schedule_calculator or SimpleScheduleCalculator()
        self.notification_service = notification_service

    async def create_job(
        self,
        name: str,
        type: str,
        description: str = "",
        priority: JobPriority = JobPriority.MEDIUM,
        category: JobCategory = JobCategory.OTHER,
        max_retries: int = 3,
        timeout_s: int = 300,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        created_by: str = "",
        schedule: JobSchedule | None = None,
        dependencies: list[JobDependency] | None = None,
    ) -> JobDefinition:
        job = JobDefinition(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            type=type,
            priority=priority,
            category=category,
            max_retries=max_retries,
            timeout_s=timeout_s,
            tags=tags or [],
            metadata=metadata or {},
            created_by=created_by,
            status=JobStatus.PENDING,
        )
        errors = await self._validate_job(job)
        if errors:
            raise JobValidationError(job.id, "; ".join(errors))

        saved = await self.job_repository.save(job)

        if schedule:
            schedule.job_id = saved.id
            await self._save_schedule(schedule)

        if dependencies:
            for dep in dependencies:
                dep.job_id = saved.id
                dep.id = dep.id or str(uuid.uuid4())
                await self.dependency_repository.save(dep)

        self._publish_event(JobCreatedEvent(
            job_id=saved.id,
            name=saved.name,
            category=saved.category,
            priority=saved.priority,
            aggregate_id=saved.id,
            payload={
                "name": saved.name,
                "type": saved.type,
                "category": saved.category.value,
                "priority": saved.priority.value,
            },
        ))

        return saved

    async def get_job(self, job_id: str) -> JobDefinition:
        job = await self.job_repository.get(job_id)
        if not job:
            raise JobNotFoundError(job_id)
        return job

    async def list_jobs(
        self,
        status: str | None = None,
        category: str | None = None,
        priority: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobDefinition]:
        filters: dict[str, Any] = {}
        if status:
            filters["status"] = JobStatus(status)
        if category:
            filters["category"] = JobCategory(category)
        if priority:
            filters["priority"] = JobPriority(priority)
        jobs = await self.job_repository.list(skip=skip, limit=limit, **filters)
        if search:
            search_lower = search.lower()
            jobs = [
                j for j in jobs
                if search_lower in j.name.lower() or search_lower in j.description.lower()
            ]
        return jobs

    async def update_job(self, job_id: str, updates: dict[str, Any]) -> JobDefinition:
        job = await self.get_job(job_id)
        if job.status not in (JobStatus.PENDING, JobStatus.PAUSED, JobStatus.FAILED):
            raise JobStateTransitionError(job_id, job.status.value, "update")

        for key, value in updates.items():
            if hasattr(job, key) and key not in ("id", "created_at", "version"):
                if key == "priority" and isinstance(value, str):
                    value = JobPriority(value)
                elif key == "category" and isinstance(value, str):
                    value = JobCategory(value)
                elif key == "status" and isinstance(value, str):
                    value = JobStatus(value)
                setattr(job, key, value)

        job.version += 1
        saved = await self.job_repository.save(job)
        return saved

    async def delete_job(self, job_id: str) -> None:
        job = await self.get_job(job_id)
        schedules = await self.schedule_repository.find_by_job_id(job_id)
        for s in schedules:
            await self.schedule_repository.delete(s.id)
        deps = await self.dependency_repository.find_by_job_id(job_id)
        for d in deps:
            await self.dependency_repository.delete(d.id)
        await self.job_repository.delete(job_id)

    async def execute_job_now(self, job_id: str) -> JobExecution:
        job = await self.get_job(job_id)
        if job.is_paused:
            raise JobStateTransitionError(job_id, job.status.value, "execute")
        if job.is_running:
            raise JobStateTransitionError(job_id, job.status.value, "execute")

        dependencies = await self.dependency_repository.find_by_job_id(job_id)
        for dep in dependencies:
            resolved = await self._check_dependency_satisfied(dep)
            if not resolved:
                raise JobDependencyError(
                    job_id, dep.depends_on_job_id,
                    f"Dependency not satisfied: {dep.dependency_type.value}",
                )

        execution = JobExecution(
            id=str(uuid.uuid4()),
            job_id=job_id,
            scheduled_start=datetime.now(UTC),
            actual_start=datetime.now(UTC),
            status=JobStatus.RUNNING,
            attempt=1,
        )
        execution = await self.execution_repository.save(execution)

        job.status = JobStatus.RUNNING
        await self.job_repository.save(job)

        self._publish_event(JobStartedEvent(
            job_id=job_id,
            execution_id=execution.id,
            worker_id=execution.worker_id,
            aggregate_id=job_id,
            payload={"execution_id": execution.id, "attempt": 1},
        ))

        try:
            payload = TaskPayload(
                type=job.type,
                payload={
                    "job_id": job_id,
                    "execution_id": execution.id,
                    "metadata": job.metadata,
                },
                max_retries=job.max_retries,
                timeout_s=job.timeout_s,
            )
            await task_queue.enqueue(payload)
            logger.info(
                "Enqueued job %s (%s) as task %s",
                job_id, job.name, payload.task_id,
            )
        except Exception as exc:
            execution.status = JobStatus.FAILED
            execution.error = f"Enqueue failed: {exc}"
            execution.completed_at = datetime.now(UTC)
            execution.duration_ms = (datetime.now(UTC) - execution.actual_start).total_seconds() * 1000
            await self.execution_repository.save(execution)

            job.status = JobStatus.FAILED
            await self.job_repository.save(job)

            self._publish_event(JobFailedEvent(
                job_id=job_id,
                execution_id=execution.id,
                error=str(exc),
                attempt=1,
                will_retry=job.max_retries > 0,
                aggregate_id=job_id,
                payload={"error": str(exc), "attempt": 1},
            ))

        return execution

    async def cancel_job(self, job_id: str, reason: str = "") -> None:
        job = await self.get_job(job_id)
        if job.status not in (JobStatus.PENDING, JobStatus.RUNNING, JobStatus.PAUSED, JobStatus.FAILED, JobStatus.RETRYING):
            raise JobStateTransitionError(job_id, job.status.value, JobStatus.CANCELLED.value)

        old_status = job.status
        job.status = JobStatus.CANCELLED
        await self.job_repository.save(job)

        self._publish_event(JobCancelledEvent(
            job_id=job_id,
            execution_id="",
            reason=reason,
            aggregate_id=job_id,
            payload={"reason": reason, "previous_status": old_status.value},
        ))

    async def pause_job(self, job_id: str) -> None:
        job = await self.get_job(job_id)
        if job.status != JobStatus.PENDING:
            raise JobStateTransitionError(job_id, job.status.value, JobStatus.PAUSED.value)

        job.status = JobStatus.PAUSED
        await self.job_repository.save(job)

        self._publish_event(JobPausedEvent(
            job_id=job_id,
            aggregate_id=job_id,
            payload={},
        ))

    async def resume_job(self, job_id: str) -> None:
        job = await self.get_job(job_id)
        if job.status != JobStatus.PAUSED:
            raise JobStateTransitionError(job_id, job.status.value, JobStatus.PENDING.value)

        job.status = JobStatus.PENDING
        await self.job_repository.save(job)

        self._publish_event(JobResumedEvent(
            job_id=job_id,
            aggregate_id=job_id,
            payload={},
        ))

    async def get_execution_history(
        self,
        job_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobExecution]:
        await self.get_job(job_id)
        return await self.execution_repository.find_by_job_id(job_id, skip=skip, limit=limit)

    async def get_schedules_for_job(self, job_id: str) -> list[JobSchedule]:
        await self.get_job(job_id)
        return await self.schedule_repository.find_by_job_id(job_id)

    async def create_schedule(
        self,
        job_id: str,
        schedule_type: ScheduleType,
        cron_expression: str = "",
        interval_seconds: int = 0,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        timezone: str = "UTC",
        enabled: bool = True,
    ) -> JobSchedule:
        await self.get_job(job_id)

        schedule = JobSchedule(
            id=str(uuid.uuid4()),
            job_id=job_id,
            schedule_type=schedule_type,
            cron_expression=cron_expression,
            interval_seconds=interval_seconds,
            start_at=start_at,
            end_at=end_at,
            timezone=timezone,
            enabled=enabled,
        )

        if schedule_type == ScheduleType.CRON and cron_expression:
            if not self.schedule_calculator.validate_expression(cron_expression):
                raise JobValidationError(
                    job_id, f"Invalid cron expression: {cron_expression}",
                )
            schedule.next_run_at = self.schedule_calculator.calculate_next_run(
                cron_expression,
                after=start_at or datetime.now(UTC),
            )
        elif schedule_type == ScheduleType.INTERVAL and interval_seconds > 0:
            schedule.next_run_at = (start_at or datetime.now(UTC))
        elif schedule_type == ScheduleType.ONCE:
            schedule.next_run_at = start_at or datetime.now(UTC)

        saved = await self.schedule_repository.save(schedule)

        self._publish_event(JobScheduledEvent(
            job_id=job_id,
            schedule_id=saved.id,
            next_run_at=saved.next_run_at.isoformat() if saved.next_run_at else "",
            aggregate_id=job_id,
            payload={
                "schedule_id": saved.id,
                "schedule_type": saved.schedule_type.value,
                "next_run_at": saved.next_run_at.isoformat() if saved.next_run_at else None,
            },
        ))

        return saved

    async def delete_schedule(self, job_id: str, schedule_id: str) -> None:
        await self.get_job(job_id)
        schedule = await self.schedule_repository.get(schedule_id)
        if not schedule or schedule.job_id != job_id:
            raise JobScheduleNotFoundError(schedule_id)
        await self.schedule_repository.delete(schedule_id)

    async def get_job_stats(self) -> dict[str, Any]:
        all_statuses = list(JobStatus)
        stats: dict[str, Any] = {"by_status": {}}
        for status in all_statuses:
            stats["by_status"][status.value] = await self.job_repository.count_by_status(status)
        stats["total"] = sum(stats["by_status"].values())
        recent = await self.execution_repository.find_recent(limit=20)
        stats["recent_executions"] = [
            {
                "id": e.id,
                "job_id": e.job_id,
                "status": e.status.value,
                "duration_ms": e.duration_ms,
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
            }
            for e in recent
        ]
        return stats

    async def get_due_jobs(self, limit: int = 100) -> list[dict[str, Any]]:
        now = datetime.now(UTC)
        schedules = await self.schedule_repository.find_due_schedules(before=now, limit=limit)
        result: list[dict[str, Any]] = []
        for s in schedules:
            job = await self.job_repository.get(s.job_id)
            if not job or job.status in (JobStatus.CANCELLED, JobStatus.DEAD, JobStatus.COMPLETED):
                continue
            result.append({
                "schedule": s,
                "job": job,
            })
        return result

    async def get_dashboard_stats(self) -> dict[str, Any]:
        stats = await self.get_job_stats()
        recent = await self.execution_repository.find_recent(limit=10)
        exec_stats = await self.execution_repository.get_stats()
        schedules = await self.schedule_repository.list(limit=1000)
        active_schedules = sum(1 for s in schedules if s.enabled)

        return {
            "jobs": stats,
            "executions": exec_stats,
            "active_schedules": active_schedules,
            "total_schedules": len(schedules),
            "recent_executions": [
                {
                    "id": e.id,
                    "job_id": e.job_id,
                    "status": e.status.value,
                    "duration_ms": e.duration_ms,
                    "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in recent[:10]
            ],
        }

    async def validate_cron_expression(self, expression: str) -> dict[str, Any]:
        valid = self.schedule_calculator.validate_expression(expression)
        if not valid:
            return {"valid": False, "expression": expression, "error": "Invalid cron expression format"}
        next_run = self.schedule_calculator.calculate_next_run(expression)
        return {
            "valid": True,
            "expression": expression,
            "next_run_at": next_run.isoformat(),
        }

    async def _save_schedule(self, schedule: JobSchedule) -> JobSchedule:
        if schedule.schedule_type == ScheduleType.CRON and schedule.cron_expression:
            schedule.next_run_at = self.schedule_calculator.calculate_next_run(
                schedule.cron_expression,
                after=schedule.start_at or datetime.now(UTC),
            )
        elif schedule.schedule_type == ScheduleType.INTERVAL and schedule.interval_seconds > 0:
            schedule.next_run_at = schedule.start_at or datetime.now(UTC)
        elif schedule.schedule_type == ScheduleType.ONCE:
            schedule.next_run_at = schedule.start_at or datetime.now(UTC)

        schedule.id = schedule.id or str(uuid.uuid4())
        saved = await self.schedule_repository.save(schedule)

        self._publish_event(JobScheduledEvent(
            job_id=saved.job_id,
            schedule_id=saved.id,
            next_run_at=saved.next_run_at.isoformat() if saved.next_run_at else "",
            aggregate_id=saved.job_id,
            payload={
                "schedule_id": saved.id,
                "schedule_type": saved.schedule_type.value,
            },
        ))
        return saved

    async def _check_dependency_satisfied(self, dep: JobDependency) -> bool:
        depends_on = await self.job_repository.get(dep.depends_on_job_id)
        if not depends_on:
            return False

        if dep.dependency_type == DependencyType.FINISHED:
            return depends_on.status in (
                JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.DEAD, JobStatus.TIMED_OUT,
            )
        elif dep.dependency_type == DependencyType.SUCCESS:
            return depends_on.status == JobStatus.COMPLETED
        elif dep.dependency_type == DependencyType.FAILURE:
            return depends_on.status in (JobStatus.FAILED, JobStatus.DEAD, JobStatus.TIMED_OUT)
        return False

    async def _validate_job(self, job: JobDefinition) -> list[str]:
        errors: list[str] = []
        if not job.name or not job.name.strip():
            errors.append("Job name is required")
        if not job.type or not job.type.strip():
            errors.append("Job type is required")
        if job.max_retries < 0:
            errors.append("max_retries must be >= 0")
        if job.timeout_s < 1:
            errors.append("timeout_s must be >= 1")
        return errors

    def _publish_event(self, domain_event: Any) -> None:
        try:
            event = Event(
                name=domain_event.event_type,
                data=domain_event.payload if hasattr(domain_event, "payload") else {},
                correlation_id=getattr(domain_event, "correlation_id", ""),
                tenant_id=getattr(domain_event, "tenant_id", ""),
            )
            self.event_bus.publish(event)
        except Exception as exc:
            logger.error(
                "Failed to publish event %s: %s",
                getattr(domain_event, "event_type", "unknown"),
                exc,
            )
