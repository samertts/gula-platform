from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.orm import Session

from app.clinical.appointments.routes import (
    _actor_rate_limit,
    _correlation_id,
    _handle_error,
    _require_idempotency_key,
    _require_if_match,
)
from app.database import get_db
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync

from .schemas import (
    CreateLabOrderRequest,
    CreateSpecimenRequest,
    LabOrderActionRequest,
    RejectSpecimenRequest,
)
from .service import LaboratoryService

router = APIRouter(tags=["Core Laboratory"])


def _run(request: Request, actor: NiamActor, db: Session, operation: str, target_type: str, target_id: str | None, workspace_id: str, callback):
    _actor_rate_limit(request, actor)
    try:
        result = callback()
        db.commit()
        return result
    except Exception as exc:
        _handle_error(exc, db=db, actor=actor, request=request, operation=operation, target_type=target_type, target_id=target_id, workspace_id=workspace_id)


@router.post("/api/v1/clinical/lab-orders", status_code=status.HTTP_201_CREATED)
def create_lab_order(body: CreateLabOrderRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "lab.order.create", "lab_order", None, body.workspace_id, lambda: LaboratoryService(db).create_order(actor, encounter_id=body.encounter_id, workspace_id=body.workspace_id, priority=body.priority, clinical_indication=body.clinical_indication, items=[item.model_dump() for item in body.items], idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.get("/api/v1/clinical/lab-orders/{order_id}")
def get_lab_order(order_id: str, request: Request, workspace_id: str = Query(..., min_length=1, max_length=26), actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, "lab.order.read", "lab_order", order_id, workspace_id, lambda: LaboratoryService(db).get_order(actor, order_id=order_id, workspace_id=workspace_id, correlation_id=_correlation_id(request)))


@router.post("/api/v1/clinical/lab-orders/{order_id}/verify")
def verify_lab_order(order_id: str, body: LabOrderActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "lab.order.verify", "lab_order", order_id, body.workspace_id, lambda: LaboratoryService(db).verify_order(actor, order_id=order_id, workspace_id=body.workspace_id, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/clinical/specimens", status_code=status.HTTP_201_CREATED)
def create_specimen(body: CreateSpecimenRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "specimen.create", "specimen", None, body.workspace_id, lambda: LaboratoryService(db).create_specimen(actor, order_item_id=body.order_item_id, workspace_id=body.workspace_id, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.get("/api/v1/clinical/specimens/worklist")
def specimen_worklist(request: Request, workspace_id: str = Query(..., min_length=1, max_length=26), status_filter: str | None = Query(default=None, alias="status", max_length=24), priority: str | None = Query(default=None, pattern="^(ROUTINE|URGENT|STAT)$"), limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0, le=1_000_000), actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, "specimen.worklist", "specimen", None, workspace_id, lambda: LaboratoryService(db).list_worklist(actor, workspace_id=workspace_id, status=status_filter, priority=priority, limit=limit, offset=offset, correlation_id=_correlation_id(request)))


def _transition_route(target: str):
    def handler(specimen_id: str, body: LabOrderActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
        key = _require_idempotency_key(idempotency_key)
        expected = _require_if_match(if_match)
        operation = f"specimen.{target.lower()}"
        return _run(request, actor, db, operation, "specimen", specimen_id, body.workspace_id, lambda: LaboratoryService(db).transition_specimen(actor, specimen_id=specimen_id, workspace_id=body.workspace_id, target=target, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))
    return handler


for _target, _path in (("COLLECTED", "collect"), ("RECEIVED", "receive"), ("PROCESSING", "process"), ("ANALYZING", "analyze"), ("VALIDATED", "validate")):
    router.add_api_route(f"/api/v1/clinical/specimens/{{specimen_id}}/{_path}", _transition_route(_target), methods=["POST"])


@router.post("/api/v1/clinical/specimens/{specimen_id}/reject")
def reject_specimen(specimen_id: str, body: RejectSpecimenRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "specimen.reject", "specimen", specimen_id, body.workspace_id, lambda: LaboratoryService(db).transition_specimen(actor, specimen_id=specimen_id, workspace_id=body.workspace_id, target="REJECTED", expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None), reason=body.reason))
