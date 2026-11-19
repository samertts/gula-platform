from __future__ import annotations

from app._compat import StrEnum


class TaskStatus(StrEnum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    ESCALATED = "escalated"
    DELEGATED = "delegated"
    ON_HOLD = "on_hold"
    DECLINED = "declined"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class TaskCategory(StrEnum):
    CLINICAL = "clinical"
    ADMINISTRATIVE = "administrative"
    LABORATORY = "laboratory"
    APPROVAL = "approval"
    REVIEW = "review"
    VERIFICATION = "verification"
    FOLLOW_UP = "follow_up"
    COMPLIANCE = "compliance"
    TRAINING = "training"
    GENERAL = "general"


class AssignmentStrategy(StrEnum):
    MANUAL = "manual"
    ROUND_ROBIN = "round_robin"
    LEAST_BUSY = "least_busy"
    SKILL_BASED = "skill_based"
    RANDOM = "random"
    LOAD_BALANCED = "load_balanced"


class EscalationLevel(StrEnum):
    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"
    LEVEL_4 = "level_4"


class TaskSLAStatus(StrEnum):
    ON_TRACK = "on_track"
    WARNING = "warning"
    BREACHED = "breached"


class HandoverReason(StrEnum):
    SHIFT_CHANGE = "shift_change"
    ABSENCE = "absence"
    WORKLOAD = "workload"
    SKILL_MISMATCH = "skill_mismatch"
    OTHER = "other"
