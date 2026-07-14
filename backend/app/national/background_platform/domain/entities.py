from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.national.background_platform.domain.enums import (
    DependencyType,
    JobCategory,
    JobPriority,
    JobStatus,
    ScheduleType,
)


@dataclass
class JobDefinition:
    id: str
    name: str
    description: str = ""
    type: str = ""
    priority: JobPriority = JobPriority.MEDIUM
    category: JobCategory = JobCategory.OTHER
    max_retries: int = 3
    timeout_s: int = 300
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: int = 1
    status: JobStatus = JobStatus.PENDING

    @property
    def is_pending(self) -> bool:
        return self.status == JobStatus.PENDING

    @property
    def is_running(self) -> bool:
        return self.status == JobStatus.RUNNING

    @property
    def is_completed(self) -> bool:
        return self.status == JobStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        return self.status == JobStatus.FAILED

    @property
    def is_cancelled(self) -> bool:
        return self.status == JobStatus.CANCELLED

    @property
    def is_paused(self) -> bool:
        return self.status == JobStatus.PAUSED

    @property
    def is_retrying(self) -> bool:
        return self.status == JobStatus.RETRYING

    @property
    def is_timed_out(self) -> bool:
        return self.status == JobStatus.TIMED_OUT

    @property
    def is_dead(self) -> bool:
        return self.status == JobStatus.DEAD

    @property
    def is_active(self) -> bool:
        return self.status in (JobStatus.PENDING, JobStatus.RUNNING, JobStatus.RETRYING)


@dataclass
class JobSchedule:
    id: str
    job_id: str
    schedule_type: ScheduleType = ScheduleType.ONCE
    cron_expression: str = ""
    interval_seconds: int = 0
    start_at: datetime | None = None
    end_at: datetime | None = None
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    timezone: str = "UTC"
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_due(self) -> bool:
        if not self.enabled:
            return False
        if self.next_run_at is None:
            return False
        return datetime.now(UTC) >= self.next_run_at

    @property
    def is_expired(self) -> bool:
        if self.end_at is None:
            return False
        return datetime.now(UTC) >= self.end_at


@dataclass
class JobExecution:
    id: str
    job_id: str
    scheduled_start: datetime | None = None
    actual_start: datetime | None = None
    completed_at: datetime | None = None
    status: JobStatus = JobStatus.PENDING
    worker_id: str = ""
    attempt: int = 0
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    duration_ms: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_running(self) -> bool:
        return self.status == JobStatus.RUNNING

    @property
    def is_completed(self) -> bool:
        return self.status == JobStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        return self.status == JobStatus.FAILED

    @property
    def runtime_ms(self) -> float:
        if self.actual_start and self.completed_at:
            return (self.completed_at - self.actual_start).total_seconds() * 1000
        return 0.0


@dataclass
class JobDependency:
    id: str
    job_id: str
    depends_on_job_id: str
    dependency_type: DependencyType = DependencyType.SUCCESS


@dataclass
class CronExpression:
    expression: str

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        parts = self.expression.strip().split()
        if len(parts) != 5:
            raise ValueError(
                f"Invalid cron expression {self.expression!r}: "
                f"expected 5 fields, got {len(parts)}"
            )
        for part in parts:
            if not part or not part.strip():
                raise ValueError(f"Invalid cron expression {self.expression!r}: empty field")

    def next_fire_time(self, after: datetime | None = None) -> datetime:
        from app.national.background_platform.application.interfaces import SimpleScheduleCalculator

        calculator = SimpleScheduleCalculator()
        return calculator.calculate_next_run(
            cron_expression=self.expression,
            after=after or datetime.now(UTC),
        )

    def is_due(self, at: datetime | None = None) -> bool:
        return datetime.now(UTC) >= self.next_fire_time(after=at)
