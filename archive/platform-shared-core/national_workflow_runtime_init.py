"""Archived Shared Core `workflow_engine` reimplementation (ADR-028 / ADR-036).

PROGRAM-01 Wave 4 order 19 — finding #44
(`rule_id: workflow_engine`, signal `def\\s+execute_workflow\\s*\\(`).

Source: `backend/app/national/workflow_runtime/__init__.py` (moved by `git mv` in Commit 3.6).

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

from app.national.workflow_runtime.domain.entities import (
    RetryPolicyConfig,
    SagaLog,
    WorkflowApproval,
    WorkflowCompensation,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowExecutionStep,
    WorkflowStepDefinition,
    WorkflowTimer,
)
from app.national.workflow_runtime.domain.enums import (
    CompensationStrategy,
    WorkflowApprovalStrategy,
    WorkflowExecutionStatus,
    WorkflowRetryPolicy,
    WorkflowStepStatus,
    WorkflowTimeoutPolicy,
    WorkflowTrigger,
)
from app.national.workflow_runtime.domain.saga_engine import SagaEngine
from app.national.workflow_runtime.domain.workflow_state_machine import (
    WorkflowStateMachine,
)

__all__ = [
    "CompensationStrategy",
    "RetryPolicyConfig",
    "SagaEngine",
    "SagaLog",
    "WorkflowApproval",
    "WorkflowApprovalStrategy",
    "WorkflowCompensation",
    "WorkflowDefinition",
    "WorkflowExecution",
    "WorkflowExecutionStatus",
    "WorkflowExecutionStep",
    "WorkflowRetryPolicy",
    "WorkflowStateMachine",
    "WorkflowStepDefinition",
    "WorkflowStepStatus",
    "WorkflowTimeoutPolicy",
    "WorkflowTimer",
    "WorkflowTrigger",
]
