from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from app._compat import UTC
from app.national.workflow_runtime.application.interfaces import (
    WorkflowApprovalHandler,
    WorkflowNotifier,
    WorkflowStepExecutor,
    WorkflowTimerHandler,
)
from app.national.workflow_runtime.domain.entities import (
    RetryPolicyConfig,
    WorkflowApproval,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowExecutionStep,
    WorkflowStepDefinition,
    WorkflowTemplate,
)
from app.national.workflow_runtime.domain.enums import (
    CompensationStrategy,
    WorkflowExecutionStatus,
    WorkflowStepStatus,
    WorkflowTrigger,
)
from app.national.workflow_runtime.domain.repository import (
    SagaLogRepository,
    WorkflowApprovalRepository,
    WorkflowCompensationRepository,
    WorkflowDefinitionRepository,
    WorkflowExecutionRepository,
    WorkflowExecutionStepRepository,
    WorkflowTemplateRepository,
    WorkflowTimerRepository,
)
from app.national.workflow_runtime.domain.saga_engine import SagaEngine
from app.national.workflow_runtime.domain.workflow_state_machine import (
    WorkflowStateMachine,
)
from app.national.workflow_runtime.exceptions import (
    WorkflowExecutionNotFoundError,
    WorkflowNotFoundError,
    WorkflowStepFailedError,
)

logger = logging.getLogger("gula.workflow_runtime.service")


class WorkflowRuntimeService:
    def __init__(
        self,
        definition_repo: WorkflowDefinitionRepository,
        execution_repo: WorkflowExecutionRepository,
        step_repo: WorkflowExecutionStepRepository,
        approval_repo: WorkflowApprovalRepository,
        compensation_repo: WorkflowCompensationRepository,
        timer_repo: WorkflowTimerRepository,
        saga_repo: SagaLogRepository,
        template_repo: WorkflowTemplateRepository,
        step_executor: WorkflowStepExecutor | None = None,
        approval_handler: WorkflowApprovalHandler | None = None,
        timer_handler: WorkflowTimerHandler | None = None,
        notifier: WorkflowNotifier | None = None,
    ) -> None:
        self._def_repo = definition_repo
        self._exec_repo = execution_repo
        self._step_repo = step_repo
        self._approval_repo = approval_repo
        self._comp_repo = compensation_repo
        self._timer_repo = timer_repo
        self._saga_repo = saga_repo
        self._template_repo = template_repo
        self._step_executor = step_executor
        self._approval_handler = approval_handler
        self._timer_handler = timer_handler
        self._notifier = notifier
        self._state_machine = WorkflowStateMachine()
        self._saga_engine = SagaEngine()

    def create_definition(
        self, definition: WorkflowDefinition,
    ) -> WorkflowDefinition:
        existing = self._def_repo.find_active_version(definition.type)
        if existing:
            definition.version = existing.version + 1
        return self._def_repo.save(definition)

    def get_definition(self, definition_id: str) -> WorkflowDefinition | None:
        return self._def_repo.get(definition_id)

    def list_definitions(
        self, skip: int = 0, limit: int = 100, filters: dict | None = None,
    ) -> list[WorkflowDefinition]:
        return self._def_repo.list(skip=skip, limit=limit, filters=filters)

    def list_versions(self, workflow_type: str) -> list[WorkflowDefinition]:
        return self._def_repo.list_versions(workflow_type)

    def delete_definition(self, definition_id: str) -> bool:
        return self._def_repo.delete(definition_id)

    def start_execution(
        self,
        workflow_type: str,
        input_data: dict[str, Any],
        trigger: WorkflowTrigger = WorkflowTrigger.MANUAL,
        correlation_id: str | None = None,
        created_by: str | None = None,
        tenant_id: str | None = None,
    ) -> WorkflowExecution:
        definition = self._def_repo.find_active_version(workflow_type)
        if not definition:
            raise WorkflowNotFoundError(workflow_type)

        saga_id = str(uuid.uuid4())
        execution = WorkflowExecution(
            id=str(uuid.uuid4()),
            workflow_id=definition.id,
            workflow_version=definition.version,
            status=WorkflowExecutionStatus.RUNNING,
            trigger=trigger,
            started_at=datetime.now(UTC),
            input_data=input_data,
            correlation_id=correlation_id,
            created_by=created_by,
            tenant_id=tenant_id,
            context={"saga_id": saga_id},
        )
        execution = self._exec_repo.save(execution)

        try:
            self._execute_steps(execution, definition)
        except Exception as e:
            execution.status = WorkflowExecutionStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.now(UTC)
            self._exec_repo.save(execution)
            if definition.compensation_strategy != CompensationStrategy.NONE:
                self._compensate(execution, definition)

        return execution

    def _execute_steps(
        self, execution: WorkflowExecution, definition: WorkflowDefinition,
    ) -> None:
        steps = definition.ordered_steps()
        completed_step_ids: list[str] = []

        for step_def in steps:
            if execution.status != WorkflowExecutionStatus.RUNNING:
                break

            execution.current_step = step_def.id
            self._exec_repo.save(execution)

            step_exec = WorkflowExecutionStep(
                id=str(uuid.uuid4()),
                execution_id=execution.id,
                step_id=step_def.id,
                step_name=step_def.name,
                status=WorkflowStepStatus.RUNNING,
                started_at=datetime.now(UTC),
            )
            step_exec = self._step_repo.save(step_exec)

            if step_def.approval_required and self._approval_handler:
                step_exec.status = WorkflowStepStatus.PENDING
                self._step_repo.save(step_exec)
                self._approval_handler.request_approval(
                    execution.id, step_def.id, step_def.assigned_roles, execution.context,
                )
                if self._notifier:
                    self._notifier.notify_approval_required(
                        execution.id, step_def.name, step_def.assigned_roles,
                )
                continue

            try:
                result = self._execute_step(step_def, execution, step_exec)
                step_exec.status = WorkflowStepStatus.COMPLETED
                step_exec.result = result
                step_exec.completed_at = datetime.now(UTC)
                if step_exec.started_at:
                    step_exec.duration_ms = (
                        step_exec.completed_at - step_exec.started_at
                    ).total_seconds() * 1000
                self._step_repo.save(step_exec)

                if execution.context.get("saga_id"):
                    saga_id = execution.context["saga_id"]
                    self._saga_engine.complete_step(saga_id, step_def.id, result)
                completed_step_ids.append(step_def.id)

            except Exception as e:
                step_exec.status = WorkflowStepStatus.FAILED
                step_exec.error = str(e)
                step_exec.attempt += 1
                step_exec.completed_at = datetime.now(UTC)
                self._step_repo.save(step_exec)

                if execution.context.get("saga_id"):
                    saga_id = execution.context["saga_id"]
                    self._saga_engine.fail_step(saga_id, step_def.id, str(e))

                retry_policy = step_def.retry_policy or RetryPolicyConfig()
                if step_exec.attempt < retry_policy.max_retries:
                    step_exec.status = WorkflowStepStatus.RETRYING
                    self._step_repo.save(step_exec)
                    raise WorkflowStepFailedError(execution.id, step_def.id, str(e)) from e

                execution.status = WorkflowExecutionStatus.FAILED
                execution.error = f"Step {step_def.name} failed: {e}"
                execution.completed_at = datetime.now(UTC)
                self._exec_repo.save(execution)
                return

        execution.status = WorkflowExecutionStatus.COMPLETED
        execution.completed_at = datetime.now(UTC)
        self._exec_repo.save(execution)

    def _execute_step(
        self,
        step_def: WorkflowStepDefinition,
        execution: WorkflowExecution,
        step_exec: WorkflowExecutionStep,
    ) -> dict[str, Any]:
        input_data = dict(execution.input_data)
        input_data.update(execution.context)

        if self._step_executor:
            return self._step_executor.execute(
                step_def.type, step_def.name, input_data, execution.context,
            )
        return {"executed": True, "step": step_def.name}

    def _compensate(
        self, execution: WorkflowExecution, definition: WorkflowDefinition,
    ) -> None:
        steps = self._step_repo.find_by_execution(execution.id)
        completed = [s for s in steps if s.status == WorkflowStepStatus.COMPLETED]

        saga_id = execution.context.get("saga_id", str(uuid.uuid4()))
        self._saga_engine.compensate(saga_id, [s.step_id for s in completed])

        execution.status = WorkflowExecutionStatus.COMPENSATED
        execution.completed_at = datetime.now(UTC)
        self._exec_repo.save(execution)

    def cancel_execution(self, execution_id: str, reason: str | None = None) -> WorkflowExecution:
        execution = self._exec_repo.get(execution_id)
        if not execution:
            raise WorkflowExecutionNotFoundError(execution_id)
        execution.status = self._state_machine.transition(
            execution_id, execution.status, WorkflowExecutionStatus.CANCELLED,
        )
        execution.completed_at = datetime.now(UTC)
        execution.error = reason
        return self._exec_repo.save(execution)

    def pause_execution(self, execution_id: str, reason: str | None = None) -> WorkflowExecution:
        execution = self._exec_repo.get(execution_id)
        if not execution:
            raise WorkflowExecutionNotFoundError(execution_id)
        execution.status = self._state_machine.transition(
            execution_id, execution.status, WorkflowExecutionStatus.PAUSED,
        )
        return self._exec_repo.save(execution)

    def resume_execution(self, execution_id: str) -> WorkflowExecution:
        execution = self._exec_repo.get(execution_id)
        if not execution:
            raise WorkflowExecutionNotFoundError(execution_id)
        execution.status = self._state_machine.transition(
            execution_id, execution.status, WorkflowExecutionStatus.RUNNING,
        )
        return self._exec_repo.save(execution)

    def retry_step(
        self, execution_id: str, step_id: str,
    ) -> WorkflowExecutionStep:
        step = self._step_repo.find_by_execution_and_step(execution_id, step_id)
        if not step:
            raise WorkflowStepFailedError(execution_id, step_id, "Step not found")
        step.status = WorkflowStepStatus.RUNNING
        step.attempt += 1
        step.error = None
        step.started_at = datetime.now(UTC)
        return self._step_repo.save(step)

    def approve_step(
        self,
        execution_id: str,
        step_id: str,
        approver_id: str,
        comments: str | None = None,
    ) -> WorkflowApproval:
        approval = WorkflowApproval(
            id=str(uuid.uuid4()),
            execution_id=execution_id,
            step_id=step_id,
            approver_id=approver_id,
            status="approved",
            comments=comments,
            responded_at=datetime.now(UTC),
        )
        return self._approval_repo.save(approval)

    def reject_step(
        self,
        execution_id: str,
        step_id: str,
        approver_id: str,
        comments: str | None = None,
    ) -> WorkflowApproval:
        approval = WorkflowApproval(
            id=str(uuid.uuid4()),
            execution_id=execution_id,
            step_id=step_id,
            approver_id=approver_id,
            status="rejected",
            comments=comments,
            responded_at=datetime.now(UTC),
        )
        return self._approval_repo.save(approval)

    def get_execution(self, execution_id: str) -> WorkflowExecution | None:
        return self._exec_repo.get(execution_id)

    def list_executions(
        self, skip: int = 0, limit: int = 100, filters: dict | None = None,
    ) -> list[WorkflowExecution]:
        return self._exec_repo.list(skip=skip, limit=limit, filters=filters)

    def get_execution_steps(self, execution_id: str) -> list[WorkflowExecutionStep]:
        return self._step_repo.find_by_execution(execution_id)

    def get_pending_approvals(self, user_id: str) -> list[WorkflowApproval]:
        return self._approval_repo.find_pending_for_user(user_id)

    def create_template(
        self, template: WorkflowTemplate,
    ) -> WorkflowTemplate:
        return self._template_repo.save(template)

    def list_templates(
        self, skip: int = 0, limit: int = 100, filters: dict | None = None,
    ) -> list[WorkflowTemplate]:
        return self._template_repo.list(skip=skip, limit=limit, filters=filters)

    def instantiate_template(
        self,
        template_id: str,
        parameters: dict[str, Any],
        created_by: str | None = None,
    ) -> WorkflowDefinition:
        template = self._template_repo.get(template_id)
        if not template:
            raise WorkflowNotFoundError(template_id)
        definition_data = dict(template.definition)
        for key, value in parameters.items():
            if key in template.parameters:
                definition_data[key] = value
        definition = WorkflowDefinition(
            id=str(uuid.uuid4()),
            name=template.name,
            description=template.description,
            type=template.category,
            created_by=created_by,
        )
        return self._def_repo.save(definition)

    def get_stats(self) -> dict[str, Any]:
        return self._exec_repo.get_stats()
