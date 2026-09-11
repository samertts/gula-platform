from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app._compat import UTC

from .models import WorkflowApproval, WorkflowDefinition, WorkflowInstance


class WorkflowEngine:

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_definition(
        self,
        def_id: str,
        name: str,
        workflow_type: str,
        steps: list[dict[str, Any]],
        description: str | None = None,
        version: str = "1.0",
        timeout_hours: int | None = None,
        escalation_step: str | None = None,
        retry_policy: dict[str, Any] | None = None,
        notification_triggers: dict[str, Any] | None = None,
    ) -> WorkflowDefinition:
        definition = WorkflowDefinition(
            id=...,
            uuid=str(uuid.uuid4()),
            def_id=def_id,
            name=name,
            description=description,
            workflow_type=workflow_type,
            version=version,
            status="draft",
            steps=steps,
            timeout_hours=timeout_hours,
            escalation_step=escalation_step,
            retry_policy=retry_policy or {},
            notification_triggers=notification_triggers or {},
            is_active=False,
        )
        self.session.add(definition)
        self.session.flush()
        return definition

    def get_definition(self, def_id: str) -> WorkflowDefinition | None:
        stmt = select(WorkflowDefinition).where(
            WorkflowDefinition.def_id == def_id,
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def activate_definition(self, def_id: str) -> WorkflowDefinition | None:
        stmt = select(WorkflowDefinition).where(
            WorkflowDefinition.def_id == def_id,
        )
        result = self.session.execute(stmt)
        definition = result.scalar_one_or_none()
        if not definition:
            return None
        definition.status = "active"
        definition.is_active = True
        self.session.flush()
        return definition

    def start_instance(
        self,
        def_id: str,
        trigger_type: str,
        trigger_id: str,
        initiator_id: str,
        context: dict[str, Any] | None = None,
    ) -> WorkflowInstance | None:
        definition = self.get_definition(def_id)
        if not definition or definition.status != "active":
            return None

        now = datetime.now(UTC)
        instance_id = str(uuid.uuid4()).replace("-", "").upper()[:26]

        instance = WorkflowInstance(
            id=...,
            uuid=str(uuid.uuid4()),
            instance_id=instance_id,
            def_id=def_id,
            trigger_type=trigger_type,
            trigger_id=trigger_id,
            initiator_id=initiator_id,
            status="running",
            current_step=definition.steps[0].get("step_name") if definition.steps else None,
            state={},
            context=context or {},
            assigned_to=None,
            started_at=now,
            last_action_at=now,
            completed_at=None,
            sla_deadline=(
                now.replace(hour=now.hour + definition.timeout_hours)
                if definition.timeout_hours
                else None
            ),
            is_active=True,
        )
        self.session.add(instance)
        self.session.flush()
        return instance

    def get_instance(self, instance_id: str) -> WorkflowInstance | None:
        stmt = select(WorkflowInstance).where(
            WorkflowInstance.instance_id == instance_id,
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def submit_approval(
        self,
        instance_id: str,
        approver_id: str,
        decision: str,
        comments: str | None = None,
    ) -> WorkflowApproval | None:
        instance = self.get_instance(instance_id)
        if not instance:
            return None

        approval_id = str(uuid.uuid4()).replace("-", "").upper()[:26]
        now = datetime.now(UTC)

        approval = WorkflowApproval(
            id=...,
            uuid=str(uuid.uuid4()),
            approval_id=approval_id,
            instance_id=instance_id,
            step_name=instance.current_step or "",
            approver_id=approver_id,
            status=decision,
            comments=comments,
            assigned_at=now,
            action_at=now,
            delegated_to=None,
            escalation_reason=None,
            is_active=True,
        )
        self.session.add(approval)

        instance.status = "approved" if decision == "approved" else "rejected"
        instance.last_action_at = now
        self.session.flush()
        return approval

    def cancel_instance(
        self,
        instance_id: str,
        reason: str,
    ) -> WorkflowInstance | None:
        instance = self.get_instance(instance_id)
        if not instance:
            return None
        instance.status = "cancelled"
        instance.completed_at = datetime.now(UTC)
        instance.last_action_at = datetime.now(UTC)
        instance.is_active = False
        self.session.flush()
        return instance

    def advance_step(self, instance_id: str) -> WorkflowInstance | None:
        instance = self.get_instance(instance_id)
        if not instance:
            return None

        definition = self.get_definition(instance.def_id)
        if not definition or not definition.steps:
            instance.status = "completed"
            instance.completed_at = datetime.now(UTC)
            instance.last_action_at = datetime.now(UTC)
            self.session.flush()
            return instance

        steps = definition.steps
        current_idx = -1
        for i, step in enumerate(steps):
            if step.get("step_name") == instance.current_step:
                current_idx = i
                break

        if current_idx < 0 or current_idx >= len(steps) - 1:
            instance.status = "completed"
            instance.completed_at = datetime.now(UTC)
            instance.last_action_at = datetime.now(UTC)
            self.session.flush()
            return instance

        next_step = steps[current_idx + 1]
        instance.current_step = next_step.get("step_name")
        instance.last_action_at = datetime.now(UTC)

        step_type = next_step.get("type", "")
        if step_type == "approval":
            instance.status = "waiting_for_approval"
        elif step_type == "notification":
            instance.status = "running"

        self.session.flush()
        return instance

    def get_pending_approvals(self, approver_id: str) -> list[WorkflowApproval]:
        stmt = (
            select(WorkflowApproval)
            .where(
                WorkflowApproval.approver_id == approver_id,
                WorkflowApproval.status == "pending",
                WorkflowApproval.is_active.is_(True),
            )
            .order_by(WorkflowApproval.assigned_at)
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def list_definitions(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[WorkflowDefinition]:
        stmt = (
            select(WorkflowDefinition)
            .order_by(WorkflowDefinition.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())
