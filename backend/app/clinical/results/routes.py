from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, Query, Request
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
    AmendResultRequest,
    CreateResultRequest,
    CriticalAcknowledgeRequest,
    ResultActionRequest,
)
from .service import ResultService

router = APIRouter(tags=["Core Laboratory Results"])


def _run(request: Request, actor: NiamActor, db: Session, operation: str, target_type: str, target_id: str | None, workspace_id: str, callback):
    _actor_rate_limit(request, actor)
    try:
        result = callback()
        db.commit()
        return result
    except Exception as exc:
        _handle_error(exc, db=db, actor=actor, request=request, operation=operation, target_type=target_type, target_id=target_id, workspace_id=workspace_id)


@router.post("/api/v1/clinical/results", status_code=201)
def create_result(body: CreateResultRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "result.create", "lab_result", None, body.workspace_id, lambda: ResultService(db).create_result(actor, specimen_id=body.specimen_id, workspace_id=body.workspace_id, value_numeric=body.value_numeric, value_text=body.value_text, unit=body.unit, reference_low=body.reference_low, reference_high=body.reference_high, source_message_id=body.source_message_id, provenance_type=body.provenance_type, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.get("/api/v1/clinical/results/{result_id}")
def get_result(result_id: str, request: Request, workspace_id: str = Query(..., min_length=1, max_length=26), actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, "result.read", "lab_result", result_id, workspace_id, lambda: ResultService(db).get_result(actor, result_id=result_id, workspace_id=workspace_id, correlation_id=_correlation_id(request)))


def _transition_route(target: str, operation: str):
    def handler(result_id: str, body: ResultActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
        key = _require_idempotency_key(idempotency_key)
        expected = _require_if_match(if_match)
        return _run(request, actor, db, operation, "lab_result", result_id, body.workspace_id, lambda: getattr(ResultService(db), target)(actor, result_id=result_id, workspace_id=body.workspace_id, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))
    return handler


router.add_api_route("/api/v1/clinical/results/{result_id}/validate-technical", _transition_route("technical_validate", "result.validate_technical"), methods=["POST"])
router.add_api_route("/api/v1/clinical/results/{result_id}/validate-clinical", _transition_route("clinical_validate", "result.validate_clinical"), methods=["POST"])
router.add_api_route("/api/v1/clinical/results/{result_id}/release", _transition_route("release", "result.release"), methods=["POST"])


@router.post("/api/v1/clinical/results/{result_id}/critical/acknowledge")
def acknowledge_critical(result_id: str, body: CriticalAcknowledgeRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "critical.acknowledge", "critical_result", result_id, body.workspace_id, lambda: ResultService(db).acknowledge_critical(actor, result_id=result_id, workspace_id=body.workspace_id, expected_version=expected, reason=body.reason, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/clinical/results/{result_id}/amend")
def amend_result(result_id: str, body: AmendResultRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "result.amend", "lab_result", result_id, body.workspace_id, lambda: ResultService(db).amend(actor, result_id=result_id, workspace_id=body.workspace_id, expected_version=expected, reason=body.reason, value_numeric=body.value_numeric, value_text=body.value_text, unit=body.unit, reference_low=body.reference_low, reference_high=body.reference_high, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))
