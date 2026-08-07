"""Archived Shared Core `workflow_engine` reimplementation (ADR-028 / ADR-036).

PROGRAM-01 Wave 4 order 19 — finding #44
(`rule_id: workflow_engine`, signal `def\\s+execute_workflow\\s*\\(`).

Source: `backend/app/national/workflow_runtime/exceptions.py` (moved by `git mv` in Commit 3.6).

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
