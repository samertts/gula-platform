"""Archived Shared Core `workflow_engine` reimplementation (ADR-028 / ADR-036).

PROGRAM-01 Wave 4 order 19 — finding #44
(`rule_id: workflow_engine`, signal `def\\s+execute_workflow\\s*\\(`).

Source: `backend/app/national/workflow_runtime/domain/events.py` (moved by `git mv` in Commit 3.6).

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

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class WorkflowStarted:
    workflow_id: str
    execution_id: str
    trigger: str = "manual"
    input_summary: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowStepCompleted:
    workflow_id: str
    execution_id: str
    step_id: str
    step_name: str = ""
    duration_ms: float = 0.0
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowStepFailed:
    workflow_id: str
    execution_id: str
    step_id: str
    step_name: str = ""
    error: str | None = None
    attempt: int = 0
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowCompleted:
    workflow_id: str
    execution_id: str
    duration_ms: float = 0.0
    output_summary: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowFailed:
    workflow_id: str
    execution_id: str
    error: str | None = None
    failed_step: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowCancelled:
    workflow_id: str
    execution_id: str
    reason: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowCompensated:
    workflow_id: str
    execution_id: str
    steps_compensated: int = 0
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowPaused:
    workflow_id: str
    execution_id: str
    reason: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowTimedOut:
    workflow_id: str
    execution_id: str
    step_id: str | None = None
    timeout_s: float = 0.0
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowApprovalRequired:
    workflow_id: str
    execution_id: str
    step_id: str
    assignee_roles: list[str] = field(default_factory=list)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowApprovalCompleted:
    workflow_id: str
    execution_id: str
    step_id: str
    approver_id: str | None = None
    approved: bool = False
    comments: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkflowSagaAction:
    saga_id: str
    workflow_id: str
    step_id: str
    action: str = "forward"
    status: str = "pending"
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
