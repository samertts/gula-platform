from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.national.background_platform.domain.enums import JobCategory, JobPriority
from app.national.events.base import NationalDomainEvent


@dataclass
class JobCreatedEvent(NationalDomainEvent):
    event_type: str = "national.background_platform.job.created"
    aggregate_type: str = "JobDefinition"
    job_id: str = ""
    name: str = ""
    category: JobCategory | None = None
    priority: JobPriority | None = None


@dataclass
class JobStartedEvent(NationalDomainEvent):
    event_type: str = "national.background_platform.job.started"
    aggregate_type: str = "JobExecution"
    job_id: str = ""
    execution_id: str = ""
    worker_id: str = ""


@dataclass
class JobCompletedEvent(NationalDomainEvent):
    event_type: str = "national.background_platform.job.completed"
    aggregate_type: str = "JobExecution"
    job_id: str = ""
    execution_id: str = ""
    duration_ms: float = 0.0
    result: dict[str, Any] | None = None


@dataclass
class JobFailedEvent(NationalDomainEvent):
    event_type: str = "national.background_platform.job.failed"
    aggregate_type: str = "JobExecution"
    job_id: str = ""
    execution_id: str = ""
    error: str = ""
    attempt: int = 0
    will_retry: bool = False


@dataclass
class JobCancelledEvent(NationalDomainEvent):
    event_type: str = "national.background_platform.job.cancelled"
    aggregate_type: str = "JobDefinition"
    job_id: str = ""
    execution_id: str = ""
    reason: str = ""


@dataclass
class JobScheduledEvent(NationalDomainEvent):
    event_type: str = "national.background_platform.job.scheduled"
    aggregate_type: str = "JobSchedule"
    job_id: str = ""
    schedule_id: str = ""
    next_run_at: str = ""


@dataclass
class JobPausedEvent(NationalDomainEvent):
    event_type: str = "national.background_platform.job.paused"
    aggregate_type: str = "JobDefinition"
    job_id: str = ""


@dataclass
class JobResumedEvent(NationalDomainEvent):
    event_type: str = "national.background_platform.job.resumed"
    aggregate_type: str = "JobDefinition"
    job_id: str = ""


@dataclass
class JobTimedOutEvent(NationalDomainEvent):
    event_type: str = "national.background_platform.job.timed_out"
    aggregate_type: str = "JobExecution"
    job_id: str = ""
    execution_id: str = ""
    timeout_s: int = 0
