from __future__ import annotations

from app._compat import StrEnum


class WorkflowExecutionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    COMPENSATED = "compensated"
    ROLLED_BACK = "rolled_back"
    SUSPENDED = "suspended"


class WorkflowStepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    COMPENSATED = "compensated"
    RETRYING = "retrying"


class WorkflowTrigger(StrEnum):
    MANUAL = "manual"
    EVENT = "event"
    SCHEDULE = "schedule"
    API = "api"
    CHAIN = "chain"
    SYSTEM = "system"


class WorkflowTimeoutPolicy(StrEnum):
    NONE = "none"
    RETRY = "retry"
    FAIL = "fail"
    COMPENSATE = "compensate"
    ESCALATE = "escalate"


class WorkflowRetryPolicy(StrEnum):
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIXED = "fixed"
    CUSTOM = "custom"


class WorkflowApprovalStrategy(StrEnum):
    ANY = "any"
    ALL = "all"
    SEQUENTIAL = "sequential"
    CONSENSUS = "consensus"
    ESCALATION = "escalation"


class CompensationStrategy(StrEnum):
    NONE = "none"
    REVERSE_ORDER = "reverse_order"
    PARALLEL = "parallel"
    CUSTOM = "custom"
