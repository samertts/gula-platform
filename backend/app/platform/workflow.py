"""Standardized workflow module — wraps national/workflow_runtime.

IA-058. Every method here used to call ``WorkflowRuntimeService()`` with none
of its eight required repository arguments, so all four raised

    TypeError: WorkflowRuntimeService.__init__() missing 8 required
    positional arguments: 'definition_repo', 'execution_repo', 'step_repo',
    'approval_repo', 'compensation_repo', 'timer_repo', 'saga_repo' and
    'template_repo'

while ``GET /platform/capabilities`` advertised all four as available. The
registration happens at import time, so the advertisement was live even though
nothing could run.

The repositories are deliberately NOT wired in, for two measured reasons:

1. ``SagaLogRepository`` has no implementation. ``infrastructure/repository.py``
   provides seven ``SQLAlchemy*`` repositories; the eighth exists only as an
   ABC at ``domain/repository.py:141``. The subsystem's own router shows this
   plainly: ``api/routes.py::_get_service`` constructs the service with seven
   real repositories and ``saga_repo=None`` -- against a parameter annotated
   ``SagaLogRepository``, not ``SagaLogRepository | None``. So the one working
   construction site in the codebase satisfies that argument with a value its
   own type says is not allowed. Copying that here would propagate the hole,
   not close it.
2. No migration creates any of the eight tables this subsystem needs --
   ``national_workflow_definitions``, ``_executions``, ``_execution_steps``,
   ``_approvals``, ``_compensations``, ``_timers``, ``_templates`` and
   ``national_saga_logs``. Checked individually against
   ``migrations/versions/``: zero creating migrations each.

So wiring seven of eight repositories would turn a TypeError into a
``no such table`` error at the first query. That is not a repair, it is the
same unavailability wearing a different exception. Instead the failure is made
accurate and the capability stops claiming to exist. Making this work is a
real piece of build-out -- one repository implementation and one migration --
not a defect to patch here.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from . import PlatformRegistry

logger = logging.getLogger("gula.platform.workflow")

#: Why the workflow capability cannot serve a request. Stated once, raised by
#: every entry point, and published by the registry so the capability listing
#: and the runtime error cannot drift apart.
UNAVAILABLE_REASON = (
    "the national workflow runtime is not wired: SagaLogRepository has no "
    "implementation (7 of its 8 repositories do), and no migration creates any "
    "of its 8 tables. See IA-058."
)


class WorkflowRuntimeUnavailable(RuntimeError):
    """Raised instead of constructing a service that cannot be constructed."""


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
    """The platform-facing workflow façade.

    Each method raises ``WorkflowRuntimeUnavailable``. The method bodies that
    would do the real work are preserved below each raise, unreachable but
    intact, so whoever wires the runtime does not have to reconstruct the
    mapping from the runtime's return values to this façade's dict shape --
    that mapping was correct, it was only the construction that was not.
    """

    def _unavailable(self, operation: str) -> WorkflowRuntimeUnavailable:
        logger.warning("[PLATFORM] workflow.%s refused: %s", operation, UNAVAILABLE_REASON)
        return WorkflowRuntimeUnavailable(f"workflow.{operation} is unavailable: {UNAVAILABLE_REASON}")

    def start(self, workflow_type: str, input_data: dict, created_by: str | None = None) -> dict:
        raise self._unavailable("start")
        # Once the runtime is wired, the service is constructed with its eight
        # repositories and the body is:
        #     execution = service.start_execution(
        #         workflow_type=workflow_type, input_data=input_data,
        #         trigger=WorkflowTrigger.MANUAL, created_by=created_by,
        #     )
        #     return {"id": execution.id, "status": execution.status.value}

    def cancel(self, execution_id: str, reason: str | None = None) -> dict:
        raise self._unavailable("cancel")
        #     execution = service.cancel_execution(execution_id, reason)
        #     return {"id": execution.id, "status": execution.status.value}

    def get_status(self, execution_id: str) -> dict | None:
        raise self._unavailable("get_status")
        # Deliberately NOT `return None`. None is this method's documented
        # "no such execution" answer, so returning it here would report a
        # missing execution when the truth is that the subsystem cannot run --
        # turning an outage into a successful empty result.
        #     execution = service.get_execution(execution_id)
        #     if execution is None:
        #         return None
        #     return {"id": execution.id, "status": ..., "current_step": ...,
        #             "error": ..., "started_at": ..., "completed_at": ...}

    def get_tasks(self, execution_id: str) -> list[dict]:
        raise self._unavailable("get_tasks")
        # Deliberately NOT `return []`. An empty list is indistinguishable from
        # an execution with no steps.
        #     steps = service.get_execution_steps(execution_id)
        #     return [{"id": s.id, "name": s.step_name, ...} for s in steps]


PlatformRegistry.register(
    "workflow",
    WorkflowService(),
    capabilities=[
        {"name": "start", "description": "Start a new workflow execution"},
        {"name": "cancel", "description": "Cancel a running workflow"},
        {"name": "get_status", "description": "Get the status of a workflow execution"},
        {"name": "get_tasks", "description": "Get the tasks/steps of a workflow execution"},
    ],
    available=False,
    unavailable_reason=UNAVAILABLE_REASON,
)
