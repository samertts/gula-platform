from __future__ import annotations


class WorkflowRuntimeError(Exception):
    pass


class WorkflowNotFoundError(WorkflowRuntimeError):
    def __init__(self, workflow_id: str) -> None:
        self.workflow_id = workflow_id
        super().__init__(f"Workflow not found: {workflow_id}")


class WorkflowExecutionNotFoundError(WorkflowRuntimeError):
    def __init__(self, execution_id: str) -> None:
        self.execution_id = execution_id
        super().__init__(f"Workflow execution not found: {execution_id}")


class WorkflowInvalidTransitionError(WorkflowRuntimeError):
    def __init__(self, execution_id: str, current: str, target: str) -> None:
        self.execution_id = execution_id
        self.current = current
        self.target = target
        super().__init__(f"Invalid workflow transition: {execution_id} from {current} to {target}")


class WorkflowStepFailedError(WorkflowRuntimeError):
    def __init__(self, execution_id: str, step_id: str, error: str) -> None:
        self.execution_id = execution_id
        self.step_id = step_id
        self.error = error
        super().__init__(f"Workflow step failed: {execution_id} step {step_id}: {error}")


class WorkflowCompensationError(WorkflowRuntimeError):
    def __init__(self, execution_id: str, step_id: str, error: str) -> None:
        self.execution_id = execution_id
        self.step_id = step_id
        self.error = error
        super().__init__(f"Workflow compensation failed: {execution_id} step {step_id}: {error}")


class WorkflowTimeoutError(WorkflowRuntimeError):
    def __init__(self, execution_id: str, step_id: str, timeout_s: float) -> None:
        self.execution_id = execution_id
        self.step_id = step_id
        self.timeout_s = timeout_s
        super().__init__(
            f"Workflow step timed out: {execution_id} step {step_id} after {timeout_s}s"
        )


class WorkflowVersionError(WorkflowRuntimeError):
    def __init__(self, workflow_id: str, version: int) -> None:
        self.workflow_id = workflow_id
        self.version = version
        super().__init__(f"Workflow version not found: {workflow_id} v{version}")


class WorkflowApprovalError(WorkflowRuntimeError):
    def __init__(self, execution_id: str, step_id: str, reason: str) -> None:
        self.execution_id = execution_id
        self.step_id = step_id
        self.reason = reason
        super().__init__(f"Workflow approval error: {execution_id} step {step_id}: {reason}")
