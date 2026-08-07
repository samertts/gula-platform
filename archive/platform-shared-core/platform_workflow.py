"""Archived Shared Core `workflow_engine` reimplementation (ADR-028 / ADR-036).

PROGRAM-01 Wave 4 order 19 — finding #44
(`rule_id: workflow_engine`, signal `def\\s+execute_workflow\\s*\\(`).

Source: `backend/app/platform/workflow.py` (moved by `git mv` in Commit 3.6).

The national workflow_runtime package was wired-but-broken: its
`application/service.py` was 0 bytes, so every `/national/workflows/*` handler
raised ImportError (HTTP 500). It reimplemented (by shadowing) the canonical
live `backend/app/workflows/engine.py::WorkflowEngine`, exposed at
`/niam/workflows`. The package was archived per ADR-028 (archive-first, every
migration independently reversible via a single `git revert`). Content is
preserved byte-for-byte (with the imports required for standalone execution).
Canonical provider: `backend/app/workflows` + `backend/app/identity/workflows/routes.py`.
"""

"""Standardized workflow module — wraps national/workflow_runtime."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from . import PlatformRegistry

logger = logging.getLogger("gula.platform.workflow")


@dataclass
class WorkflowStatus:
    id: str = ""
    status: str = ""
    current_step: str = ""
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


@dataclass
class WorkflowTask:
    id: str = ""
    name: str = ""
    status: str = ""
    assigned_to: str | None = None


class WorkflowService:
    def start(self, workflow_type: str, input_data: dict, created_by: str | None = None) -> dict:
        from ..national.workflow_runtime import WorkflowRuntimeService
        from ..national.workflow_runtime.domain.enums import WorkflowTrigger

        service = WorkflowRuntimeService()
        execution = service.start_execution(
            workflow_type=workflow_type,
            input_data=input_data,
            trigger=WorkflowTrigger.MANUAL,
            created_by=created_by,
        )
        return {"id": execution.id, "status": execution.status.value}

    def cancel(self, execution_id: str, reason: str | None = None) -> dict:
        from ..national.workflow_runtime import WorkflowRuntimeService

        service = WorkflowRuntimeService()
        execution = service.cancel_execution(execution_id, reason)
        return {"id": execution.id, "status": execution.status.value}

    def get_status(self, execution_id: str) -> dict | None:
        from ..national.workflow_runtime import WorkflowRuntimeService

        service = WorkflowRuntimeService()
        execution = service.get_execution(execution_id)
        if execution is None:
            return None
        return {
            "id": execution.id,
            "status": execution.status.value
            if hasattr(execution.status, "value")
            else execution.status,
            "current_step": execution.current_step,
            "error": execution.error,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        }

    def get_tasks(self, execution_id: str) -> list[dict]:
        from ..national.workflow_runtime import WorkflowRuntimeService

        service = WorkflowRuntimeService()
        steps = service.get_execution_steps(execution_id)
        return [
            {
                "id": s.id,
                "name": s.step_name,
                "status": s.status.value if hasattr(s.status, "value") else s.status,
                "assigned_to": s.assigned_to,
                "error": s.error,
            }
            for s in steps
        ]


PlatformRegistry.register(
    "workflow",
    WorkflowService(),
    capabilities=[
        {"name": "start", "description": "Start a new workflow execution"},
        {"name": "cancel", "description": "Cancel a running workflow"},
        {"name": "get_status", "description": "Get the status of a workflow execution"},
        {"name": "get_tasks", "description": "Get the tasks/steps of a workflow execution"},
    ],
)
