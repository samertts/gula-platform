"""Archived Shared Core `workflow_engine` reimplementation (ADR-028 / ADR-036).

PROGRAM-01 Wave 4 order 19 — finding #44
(`rule_id: workflow_engine`, signal `def\\s+execute_workflow\\s*\\(`).

Source: `backend/app/national/workflow_runtime/domain/workflow_state_machine.py` (moved by `git mv` in Commit 3.6).

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

from app.national.workflow_runtime.domain.enums import WorkflowExecutionStatus
from app.national.workflow_runtime.exceptions import WorkflowInvalidTransitionError


class WorkflowStateMachine:
    _VALID_TRANSITIONS: dict[WorkflowExecutionStatus, list[WorkflowExecutionStatus]] = {
        WorkflowExecutionStatus.PENDING: [
            WorkflowExecutionStatus.RUNNING,
            WorkflowExecutionStatus.CANCELLED,
        ],
        WorkflowExecutionStatus.RUNNING: [
            WorkflowExecutionStatus.COMPLETED,
            WorkflowExecutionStatus.FAILED,
            WorkflowExecutionStatus.PAUSED,
            WorkflowExecutionStatus.CANCELLED,
            WorkflowExecutionStatus.SUSPENDED,
            WorkflowExecutionStatus.TIMED_OUT,
        ],
        WorkflowExecutionStatus.PAUSED: [
            WorkflowExecutionStatus.RUNNING,
            WorkflowExecutionStatus.CANCELLED,
            WorkflowExecutionStatus.FAILED,
        ],
        WorkflowExecutionStatus.SUSPENDED: [
            WorkflowExecutionStatus.RUNNING,
            WorkflowExecutionStatus.CANCELLED,
        ],
        WorkflowExecutionStatus.FAILED: [
            WorkflowExecutionStatus.RUNNING,
            WorkflowExecutionStatus.CANCELLED,
            WorkflowExecutionStatus.COMPENSATED,
            WorkflowExecutionStatus.ROLLED_BACK,
        ],
        WorkflowExecutionStatus.TIMED_OUT: [
            WorkflowExecutionStatus.RUNNING,
            WorkflowExecutionStatus.COMPENSATED,
            WorkflowExecutionStatus.ROLLED_BACK,
        ],
        WorkflowExecutionStatus.COMPLETED: [],
        WorkflowExecutionStatus.CANCELLED: [],
        WorkflowExecutionStatus.COMPENSATED: [],
        WorkflowExecutionStatus.ROLLED_BACK: [],
    }

    def validate_transition(
        self,
        current: WorkflowExecutionStatus,
        target: WorkflowExecutionStatus,
    ) -> bool:
        allowed = self._VALID_TRANSITIONS.get(current, [])
        return target in allowed

    def transition(
        self,
        execution_id: str,
        current: WorkflowExecutionStatus,
        target: WorkflowExecutionStatus,
    ) -> WorkflowExecutionStatus:
        if not self.validate_transition(current, target):
            raise WorkflowInvalidTransitionError(execution_id, current.value, target.value)
        return target

    def is_terminal(self, status: WorkflowExecutionStatus) -> bool:
        return status in (
            WorkflowExecutionStatus.COMPLETED,
            WorkflowExecutionStatus.FAILED,
            WorkflowExecutionStatus.CANCELLED,
            WorkflowExecutionStatus.COMPENSATED,
            WorkflowExecutionStatus.ROLLED_BACK,
            WorkflowExecutionStatus.TIMED_OUT,
        )

    def is_active(self, status: WorkflowExecutionStatus) -> bool:
        return status in (
            WorkflowExecutionStatus.RUNNING,
            WorkflowExecutionStatus.PAUSED,
            WorkflowExecutionStatus.SUSPENDED,
        )

    def can_retry(self, status: WorkflowExecutionStatus) -> bool:
        return status in (
            WorkflowExecutionStatus.FAILED,
            WorkflowExecutionStatus.TIMED_OUT,
        )
