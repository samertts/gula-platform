from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

from .engine import WorkflowEngine

router = APIRouter(prefix="/workflows", tags=["NIAM Workflows"])


@router.post("/definitions")
async def create_definition(
    def_id: str,
    name: str,
    workflow_type: str,
    steps: list[dict[str, Any]],
    description: Optional[str] = None,
    version: str = "1.0",
    timeout_hours: Optional[int] = None,
    escalation_step: Optional[str] = None,
    retry_policy: Optional[dict[str, Any]] = None,
    notification_triggers: Optional[dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    engine = WorkflowEngine(db)
    definition = await engine.create_definition(
        def_id=def_id,
        name=name,
        workflow_type=workflow_type,
        steps=steps,
        description=description,
        version=version,
        timeout_hours=timeout_hours,
        escalation_step=escalation_step,
        retry_policy=retry_policy,
        notification_triggers=notification_triggers,
    )
    return definition.to_dict()


@router.get("/definitions")
async def list_definitions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    engine = WorkflowEngine(db)
    definitions = await engine.list_definitions(skip=skip, limit=limit)
    return [d.to_dict() for d in definitions]


@router.get("/definitions/{def_id}")
async def get_definition(
    def_id: str,
    db: AsyncSession = Depends(get_db),
):
    engine = WorkflowEngine(db)
    definition = await engine.get_definition(def_id)
    if not definition:
        return {"error": "not_found"}
    return definition.to_dict()


@router.post("/instances")
async def start_instance(
    def_id: str,
    trigger_type: str,
    trigger_id: str,
    initiator_id: str,
    context: Optional[dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    engine = WorkflowEngine(db)
    instance = await engine.start_instance(
        def_id=def_id,
        trigger_type=trigger_type,
        trigger_id=trigger_id,
        initiator_id=initiator_id,
        context=context,
    )
    if not instance:
        return {"error": "definition_not_found_or_inactive"}
    return instance.to_dict()


@router.get("/instances/{instance_id}")
async def get_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
):
    engine = WorkflowEngine(db)
    instance = await engine.get_instance(instance_id)
    if not instance:
        return {"error": "not_found"}
    return instance.to_dict()


@router.post("/instances/{instance_id}/approve")
async def submit_approval(
    instance_id: str,
    approver_id: str,
    decision: str,
    comments: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    engine = WorkflowEngine(db)
    approval = await engine.submit_approval(
        instance_id=instance_id,
        approver_id=approver_id,
        decision=decision,
        comments=comments,
    )
    if not approval:
        return {"error": "instance_not_found"}
    return approval.to_dict()


@router.post("/instances/{instance_id}/cancel")
async def cancel_instance(
    instance_id: str,
    reason: str = "manual_cancellation",
    db: AsyncSession = Depends(get_db),
):
    engine = WorkflowEngine(db)
    instance = await engine.cancel_instance(
        instance_id=instance_id,
        reason=reason,
    )
    if not instance:
        return {"error": "not_found"}
    return {"instance_id": instance.instance_id, "status": instance.status}


@router.get("/approvals/pending/{approver_id}")
async def get_pending_approvals(
    approver_id: str,
    db: AsyncSession = Depends(get_db),
):
    engine = WorkflowEngine(db)
    approvals = await engine.get_pending_approvals(approver_id)
    return [a.to_dict() for a in approvals]