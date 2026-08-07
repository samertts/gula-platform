"""Archived Shared Core `workflow_engine` reimplementation (ADR-028 / ADR-036).

PROGRAM-01 Wave 4 order 19 — finding #44
(`rule_id: workflow_engine`, signal `def\\s+execute_workflow\\s*\\(`).

Source: `backend/app/national/workflow_runtime/domain/enums.py` (moved by `git mv` in Commit 3.6).

The national workflow_runtime package was wired-but-broken: its
`application/service.py` was 0 bytes, so every `/national/workflows/*` handler
raised ImportError (HTTP 500). It reimplemented (by shadowing) the canonical
live `backend/app/workflows/engine.py::WorkflowEngine`, exposed at
`/niam/workflows`. The package was archived per ADR-028 (archive-first, every
migration independently reversible via a single `git revert`). Content is
preserved byte-for-byte (with the imports required for standalone execution).
Canonical provider: `backend/app/workflows` + `backend/app/identity/workflows/routes.py`.
"""

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
