from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.national.background_platform.application.service import JobService
from app.national.background_platform.domain.entities import JobDependency, JobSchedule
from app.national.background_platform.domain.enums import (
    DependencyType,
    JobCategory,
    JobPriority,
    ScheduleType,
)
from app.national.background_platform.exceptions import (
    InvalidCronExpressionError,
    JobDependencyError,
    JobNotFoundError,
    JobScheduleNotFoundError,
    JobStateTransitionError,
    JobValidationError,
)
from app.national.background_platform.infrastructure.repository import (
    SQLAlchemyJobDependencyRepository,
    SQLAlchemyJobExecutionRepository,
    SQLAlchemyJobRepository,
    SQLAlchemyJobScheduleRepository,
)

router = APIRouter(prefix="/national/jobs", tags=["National Background Platform"])


def _get_service(db: Session = Depends(get_db)) -> JobService:
    from app.kernel import Kernel
    from app.kernel.event_bus.bus import EventBus

    kernel = Kernel.get_instance()
    event_bus = kernel.event_bus if hasattr(kernel, "event_bus") else EventBus(kernel)
    job_repo = SQLAlchemyJobRepository(db)
    schedule_repo = SQLAlchemyJobScheduleRepository(db)
    execution_repo = SQLAlchemyJobExecutionRepository(db)
    dependency_repo = SQLAlchemyJobDependencyRepository(db)
    return JobService(
        job_repository=job_repo,
        schedule_repository=schedule_repo,
        execution_repository=execution_repo,
        dependency_repository=dependency_repo,
        event_bus=event_bus,
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_job(
    body: dict[str, Any],
    service: JobService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        schedule_data = body.pop("schedule", None)
        dependency_data = body.pop("dependencies", None)

        job = await service.create_job(
            name=body.get("name", ""),
            type=body.get("type", ""),
            description=body.get("description", ""),
            priority=JobPriority(body.get("priority", "medium")) if body.get("priority") else JobPriority.MEDIUM,
            category=JobCategory(body.get("category", "other")) if body.get("category") else JobCategory.OTHER,
            max_retries=body.get("max_retries", 3),
            timeout_s=body.get("timeout_s", 300),
            tags=body.get("tags", []),
            metadata=body.get("metadata", {}),
            created_by=body.get("created_by", ""),
        )

        if schedule_data:
            schedule = JobSchedule(
                id="",
                job_id=job.id,
                schedule_type=ScheduleType(schedule_data.get("schedule_type", "once")),
                cron_expression=schedule_data.get("cron_expression", ""),
                interval_seconds=schedule_data.get("interval_seconds", 0),
                start_at=datetime.fromisoformat(schedule_data["start_at"]) if schedule_data.get("start_at") else None,
                end_at=datetime.fromisoformat(schedule_data["end_at"]) if schedule_data.get("end_at") else None,
                timezone=schedule_data.get("timezone", "UTC"),
                enabled=schedule_data.get("enabled", True),
            )
            await service.create_schedule(
                job_id=job.id,
                schedule_type=schedule.schedule_type,
                cron_expression=schedule.cron_expression,
                interval_seconds=schedule.interval_seconds,
                start_at=schedule.start_at,
                end_at=schedule.end_at,
                timezone=schedule.timezone,
                enabled=schedule.enabled,
            )

        if dependency_data:
            for dep in dependency_data:
                await service._check_dependency_satisfied(
                    JobDependency(
                        id="",
                        job_id=job.id,
                        depends_on_job_id=dep.get("depends_on_job_id", ""),
                        dependency_type=DependencyType(dep.get("dependency_type", "success")),
                    ),
                )

        return {
            "id": job.id,
            "name": job.name,
            "type": job.type,
            "priority": job.priority.value,
            "category": job.category.value,
            "status": job.status.value,
        }
    except JobValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Validation error") from e


@router.get("/")
async def list_jobs(
    status: str | None = Query(None),
    category: str | None = Query(None),
    priority: str | None = Query(None),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: JobService = Depends(_get_service),
) -> list[dict[str, Any]]:
    jobs = await service.list_jobs(
        status=status,
        category=category,
        priority=priority,
        search=search,
        skip=skip,
        limit=limit,
    )
    return [
        {
            "id": j.id,
            "name": j.name,
            "description": j.description,
            "type": j.type,
            "priority": j.priority.value,
            "category": j.category.value,
            "max_retries": j.max_retries,
            "timeout_s": j.timeout_s,
            "tags": j.tags,
            "status": j.status.value,
            "version": j.version,
            "created_by": j.created_by,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        }
        for j in jobs
    ]


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    service: JobService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        job = await service.get_job(job_id)
        schedules = await service.get_schedules_for_job(job_id)
        return {
            "id": job.id,
            "name": job.name,
            "description": job.description,
            "type": job.type,
            "priority": job.priority.value,
            "category": job.category.value,
            "max_retries": job.max_retries,
            "timeout_s": job.timeout_s,
            "tags": job.tags,
            "metadata": job.metadata,
            "status": job.status.value,
            "version": job.version,
            "created_by": job.created_by,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "schedules": [
                {
                    "id": s.id,
                    "schedule_type": s.schedule_type.value,
                    "cron_expression": s.cron_expression,
                    "interval_seconds": s.interval_seconds,
                    "next_run_at": s.next_run_at.isoformat() if s.next_run_at else None,
                    "enabled": s.enabled,
                }
                for s in schedules
            ],
        }
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e


@router.put("/{job_id}")
async def update_job(
    job_id: str,
    body: dict[str, Any],
    service: JobService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        job = await service.update_job(job_id, body)
        return {
            "id": job.id,
            "name": job.name,
            "status": job.status.value,
            "version": job.version,
        }
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e
    except JobStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource conflict") from e
    except JobValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Validation error") from e


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_job(
    job_id: str,
    service: JobService = Depends(_get_service),
) -> None:
    try:
        await service.delete_job(job_id)
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e


@router.post("/{job_id}/execute")
async def execute_job_now(
    job_id: str,
    service: JobService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        execution = await service.execute_job_now(job_id)
        return {
            "execution_id": execution.id,
            "job_id": execution.job_id,
            "status": execution.status.value,
            "attempt": execution.attempt,
        }
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e
    except JobStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource conflict") from e
    except JobDependencyError as e:
        raise HTTPException(status_code=status.HTTP_424_FAILED_DEPENDENCY, detail="Dependency failed") from e


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    body: dict[str, Any] | None = None,
    service: JobService = Depends(_get_service),
) -> dict[str, str]:
    if body is None:
        body = {}
    try:
        await service.cancel_job(job_id, reason=body.get("reason", ""))
        return {"status": "cancelled", "job_id": job_id}
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e
    except JobStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource conflict") from e


@router.post("/{job_id}/pause")
async def pause_job(
    job_id: str,
    service: JobService = Depends(_get_service),
) -> dict[str, str]:
    try:
        await service.pause_job(job_id)
        return {"status": "paused", "job_id": job_id}
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e
    except JobStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource conflict") from e


@router.post("/{job_id}/resume")
async def resume_job(
    job_id: str,
    service: JobService = Depends(_get_service),
) -> dict[str, str]:
    try:
        await service.resume_job(job_id)
        return {"status": "pending", "job_id": job_id}
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e
    except JobStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource conflict") from e


@router.get("/{job_id}/executions")
async def get_execution_history(
    job_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: JobService = Depends(_get_service),
) -> list[dict[str, Any]]:
    try:
        executions = await service.get_execution_history(job_id, skip=skip, limit=limit)
        return [
            {
                "id": e.id,
                "job_id": e.job_id,
                "scheduled_start": e.scheduled_start.isoformat() if e.scheduled_start else None,
                "actual_start": e.actual_start.isoformat() if e.actual_start else None,
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "status": e.status.value,
                "worker_id": e.worker_id,
                "attempt": e.attempt,
                "error": e.error,
                "duration_ms": e.duration_ms,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in executions
        ]
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e


@router.get("/{job_id}/schedules")
async def get_schedules(
    job_id: str,
    service: JobService = Depends(_get_service),
) -> list[dict[str, Any]]:
    try:
        schedules = await service.get_schedules_for_job(job_id)
        return [
            {
                "id": s.id,
                "job_id": s.job_id,
                "schedule_type": s.schedule_type.value,
                "cron_expression": s.cron_expression,
                "interval_seconds": s.interval_seconds,
                "start_at": s.start_at.isoformat() if s.start_at else None,
                "end_at": s.end_at.isoformat() if s.end_at else None,
                "last_run_at": s.last_run_at.isoformat() if s.last_run_at else None,
                "next_run_at": s.next_run_at.isoformat() if s.next_run_at else None,
                "timezone": s.timezone,
                "enabled": s.enabled,
            }
            for s in schedules
        ]
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e


@router.post("/{job_id}/schedules", status_code=status.HTTP_201_CREATED)
async def create_schedule(
    job_id: str,
    body: dict[str, Any],
    service: JobService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        schedule = await service.create_schedule(
            job_id=job_id,
            schedule_type=ScheduleType(body.get("schedule_type", "once")),
            cron_expression=body.get("cron_expression", ""),
            interval_seconds=body.get("interval_seconds", 0),
            start_at=datetime.fromisoformat(body["start_at"]) if body.get("start_at") else None,
            end_at=datetime.fromisoformat(body["end_at"]) if body.get("end_at") else None,
            timezone=body.get("timezone", "UTC"),
            enabled=body.get("enabled", True),
        )
        return {
            "id": schedule.id,
            "job_id": schedule.job_id,
            "schedule_type": schedule.schedule_type.value,
            "next_run_at": schedule.next_run_at.isoformat() if schedule.next_run_at else None,
            "enabled": schedule.enabled,
        }
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e
    except JobValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Validation error") from e


@router.delete("/{job_id}/schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_schedule(
    job_id: str,
    schedule_id: str,
    service: JobService = Depends(_get_service),
) -> None:
    try:
        await service.delete_schedule(job_id, schedule_id)
    except (JobNotFoundError, JobScheduleNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e


@router.get("/stats")
async def get_job_stats(
    service: JobService = Depends(_get_service),
) -> dict[str, Any]:
    return await service.get_job_stats()


@router.get("/due")
async def get_due_jobs(
    limit: int = Query(100, ge=1, le=1000),
    service: JobService = Depends(_get_service),
) -> list[dict[str, Any]]:
    due = await service.get_due_jobs(limit=limit)
    return [
        {
            "schedule_id": d["schedule"].id,
            "job_id": d["job"].id,
            "job_name": d["job"].name,
            "job_type": d["job"].type,
            "schedule_type": d["schedule"].schedule_type.value,
            "next_run_at": d["schedule"].next_run_at.isoformat() if d["schedule"].next_run_at else None,
        }
        for d in due
    ]


@router.get("/dashboard")
async def get_dashboard(
    service: JobService = Depends(_get_service),
) -> dict[str, Any]:
    return await service.get_dashboard_stats()


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "module": "national_background_platform", "version": "1.0.0"}


@router.post("/cron/validate")
async def validate_cron(
    body: dict[str, str],
    service: JobService = Depends(_get_service),
) -> dict[str, Any]:
    expression = body.get("expression", "")
    if not expression:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="cron expression is required",
        )
    try:
        return await service.validate_cron_expression(expression)
    except InvalidCronExpressionError as e:
        return {"valid": False, "expression": expression, "error": str(e)}
