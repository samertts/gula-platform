from __future__ import annotations

from backend.app.national.workflow_runtime.domain.enums import WorkflowExecutionStatus
from backend.app.national.workflow_runtime.exceptions import WorkflowInvalidTransitionError


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
