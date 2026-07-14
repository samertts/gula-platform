from __future__ import annotations

from app._compat import StrEnum


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    RETRYING = "retrying"
    TIMED_OUT = "timed_out"
    DEAD = "dead"


class JobPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ScheduleType(StrEnum):
    ONCE = "once"
    INTERVAL = "interval"
    CRON = "cron"
    EVENT_DRIVEN = "event_driven"
    CHAINED = "chained"


class JobCategory(StrEnum):
    MAINTENANCE = "maintenance"
    REPORTING = "reporting"
    SYNC = "sync"
    CLEANUP = "cleanup"
    NOTIFICATION = "notification"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"
    DATA_PROCESSING = "data_processing"
    AI = "ai"
    OTHER = "other"


class DependencyType(StrEnum):
    FINISHED = "finished"
    SUCCESS = "success"
    FAILURE = "failure"
