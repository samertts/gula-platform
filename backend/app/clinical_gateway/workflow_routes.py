from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.clinical_gateway.access_context import ClinicalAccessContext
from app.clinical_gateway.context import ClinicalGatewayBlocked, ClinicalGatewayContextResolver
from app.clinical_gateway.workflow_service import ClinicalWorkflowService
from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync

router = APIRouter(prefix="/api/v1/clinical", tags=["Canonical Clinical Workflow"])


class ShiftStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shift_type: str = Field(min_length=1, max_length=20)
    department_id: int | None = Field(default=None, gt=0)


class PatientAssignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shift_id: str = Field(min_length=1, max_length=26)
    patient_id: int = Field(gt=0)
    encounter_id: str | None = Field(default=None, max_length=26)
    assignment_type: str = Field(default="primary", min_length=1, max_length=30)


class ClinicalTaskCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: int = Field(gt=0)
    task_type: str = Field(min_length=1, max_length=40)
    description: str = Field(min_length=1, max_length=4000)
    priority: str = Field(default="medium", min_length=1, max_length=20)
    encounter_id: str | None = Field(default=None, max_length=26)
    due_time: datetime | None = None


class ClinicalTaskCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notes: str | None = Field(default=None, max_length=4000)


def _workflow_permissions(context) -> frozenset[str]:
    """Derive workflow capabilities from reviewed membership relationship only."""
    relationship = str(context.membership.relationship_type or "").lower()
    if relationship in {"professional", "consultant", "manager"}:
        return frozenset({"shift:start", "shift:end", "patient:assign", "task:create", "update", "create"})
    raise ClinicalGatewayBlocked("workflow_role_not_authorized")


def _gateway(db: Session, actor: NiamActor):
    return ClinicalGatewayContextResolver(db).resolve(actor)


@router.post("/workflow/shifts/start", status_code=status.HTTP_201_CREATED)
def start_shift(
    payload: ShiftStartRequest,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
):
    try:
        gateway = _gateway(db, actor)
        permissions = _workflow_permissions(gateway)
        access = ClinicalAccessContext.from_gateway(gateway, purpose="workflow.shift.start", permissions=permissions)
        shift = ClinicalWorkflowService(db).start_shift(access=access, shift_type=payload.shift_type, department_id=payload.department_id)
        db.commit()
        return ClinicalWorkflowService.to_safe_dict(shift)
    except ClinicalGatewayBlocked as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Shift start is not authorized") from exc


@router.post("/workflow/shifts/{shift_id}/end")
def end_shift(
    shift_id: str,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
):
    try:
        gateway = _gateway(db, actor)
        permissions = _workflow_permissions(gateway)
        access = ClinicalAccessContext.from_gateway(gateway, purpose="workflow.shift.end", permissions=permissions)
        shift = ClinicalWorkflowService(db).end_shift(access=access, shift_id=shift_id)
        db.commit()
        return ClinicalWorkflowService.to_safe_dict(shift)
    except ClinicalGatewayBlocked as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Shift end is not authorized") from exc


@router.post("/workflow/patient-assignments", status_code=status.HTTP_201_CREATED)
def assign_patient(
    payload: PatientAssignRequest,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
):
    try:
        gateway = _gateway(db, actor)
        permissions = _workflow_permissions(gateway)
        access = ClinicalAccessContext.from_gateway(gateway, purpose="workflow.patient.assign", permissions=permissions)
        assignment = ClinicalWorkflowService(db).assign_patient(
            access=access,
            shift_id=payload.shift_id,
            patient_id=payload.patient_id,
            encounter_id=payload.encounter_id,
            assignment_type=payload.assignment_type,
        )
        db.commit()
        return ClinicalWorkflowService.to_safe_dict(assignment)
    except ClinicalGatewayBlocked as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patient assignment is not authorized") from exc


@router.post("/workflow/tasks", status_code=status.HTTP_201_CREATED)
def create_task(
    payload: ClinicalTaskCreateRequest,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
):
    try:
        gateway = _gateway(db, actor)
        permissions = _workflow_permissions(gateway)
        access = ClinicalAccessContext.from_gateway(gateway, purpose="workflow.task.create", permissions=permissions)
        task = ClinicalWorkflowService(db).create_task(
            access=access,
            patient_id=payload.patient_id,
            task_type=payload.task_type,
            description=payload.description,
            priority=payload.priority,
            encounter_id=payload.encounter_id,
            due_time=payload.due_time,
        )
        db.commit()
        return ClinicalWorkflowService.to_safe_dict(task)
    except ClinicalGatewayBlocked as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Task creation is not authorized") from exc


@router.post("/workflow/tasks/{task_id}/complete")
def complete_task(
    task_id: str,
    payload: ClinicalTaskCompleteRequest,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
):
    try:
        gateway = _gateway(db, actor)
        permissions = _workflow_permissions(gateway)
        access = ClinicalAccessContext.from_gateway(gateway, purpose="workflow.task.complete", permissions=permissions)
        task = ClinicalWorkflowService(db).complete_task(access=access, task_id=task_id, notes=payload.notes)
        db.commit()
        return ClinicalWorkflowService.to_safe_dict(task)
    except ClinicalGatewayBlocked as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Task completion is not authorized") from exc
