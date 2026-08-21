from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.clinical_gateway.access_context import ClinicalAccessContext
from app.clinical_gateway.context import ClinicalGatewayBlocked, ClinicalGatewayContextResolver
from app.clinical_gateway.order_service import ClinicalOrderService
from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync

router = APIRouter(prefix="/api/v1/clinical", tags=["Canonical Clinical Order Commands"])


class ClinicalOrderCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: int = Field(gt=0)
    encounter_id: str | None = Field(default=None, max_length=80)
    service: str = Field(min_length=1, max_length=120)
    priority: str = Field(default="routine", min_length=1, max_length=20)
    clinical_indication: str | None = Field(default=None, max_length=2000)
    prescriber_id: str | None = Field(default=None, max_length=80)


class ClinicalOrderTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_version: int = Field(ge=1)
    new_status: str = Field(min_length=1, max_length=24)
    reason: str | None = Field(default=None, max_length=500)


def _access(db: Session, actor: NiamActor, *, purpose: str, permissions: frozenset[str]) -> ClinicalAccessContext:
    gateway = ClinicalGatewayContextResolver(db).resolve(actor)
    return ClinicalAccessContext.from_gateway(gateway, purpose=purpose, permissions=permissions)


@router.post("/orders", status_code=status.HTTP_201_CREATED)
def create_clinical_order(
    payload: ClinicalOrderCreateRequest,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        access = _access(db, actor, purpose="clinical_order.create", permissions=frozenset({"create"}))
        order = ClinicalOrderService(db).create(
            access=access,
            patient_id=payload.patient_id,
            encounter_id=payload.encounter_id,
            service=payload.service,
            priority=payload.priority,
            clinical_indication=payload.clinical_indication,
            client_prescriber_id=payload.prescriber_id,
        )
        db.commit()
        return cast(dict[str, Any], ClinicalOrderService.to_safe_dict(order))
    except ClinicalGatewayBlocked as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clinical order creation is not authorized") from exc


@router.post("/orders/{order_id}/transition")
def transition_clinical_order(
    order_id: int,
    payload: ClinicalOrderTransitionRequest,
    actor: NiamActor = Depends(get_current_niam_actor_sync),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        access = _access(db, actor, purpose="clinical_order.transition", permissions=frozenset({"update"}))
        order = ClinicalOrderService(db).transition(
            access=access,
            order_id=order_id,
            expected_version=payload.expected_version,
            new_status=payload.new_status,
            reason=payload.reason,
        )
        db.commit()
        return cast(dict[str, Any], ClinicalOrderService.to_safe_dict(order))
    except ClinicalGatewayBlocked as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clinical order transition is not authorized") from exc
