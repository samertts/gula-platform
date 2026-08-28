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

from .advanced_schemas import (
    AnalyzerActionRequest,
    AnalyzerCreateRequest,
    AnalyzerMessageRequest,
    QCCreateRequest,
    TestCatalogCreateRequest,
)
from .advanced_service import LISAdvancedService

router = APIRouter(tags=["LIS Advanced"])


def _run(request: Request, actor: NiamActor, db: Session, operation: str, target_type: str, target_id: str | None, workspace_id: str, callback):
    _actor_rate_limit(request, actor)
    try:
        result = callback()
        db.commit()
        return result
    except Exception as exc:
        _handle_error(exc, db=db, actor=actor, request=request, operation=operation, target_type=target_type, target_id=target_id, workspace_id=workspace_id)


@router.post("/api/v1/clinical/lab/test-catalog", status_code=201)
def create_test_catalog(body: TestCatalogCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "lab.test_catalog.create", "lab_test_catalog", None, body.workspace_id, lambda: LISAdvancedService(db).create_test_catalog(actor, workspace_id=body.workspace_id, canonical_code=body.canonical_code, local_code=body.local_code, name=body.name, system=body.system, specimen_type=body.specimen_type, unit_ucum=body.unit_ucum, method=body.method, reference_range=body.reference_range, critical_range=body.critical_range, key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.get("/api/v1/clinical/lab/test-catalog")
def list_test_catalog(request: Request, workspace_id: str = Query(min_length=1, max_length=80), canonical_code: str | None = Query(default=None, max_length=120), limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0, le=100000), actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, "lab.test_catalog.read", "lab_test_catalog", None, workspace_id, lambda: LISAdvancedService(db).list_test_catalog(actor, workspace_id=workspace_id, canonical_code=canonical_code, limit=limit, offset=offset, correlation_id=_correlation_id(request)))


@router.post("/api/v1/clinical/lab/analyzers", status_code=201)
def register_analyzer(body: AnalyzerCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "lab.analyzer.create", "lab_analyzer", None, body.workspace_id, lambda: LISAdvancedService(db).register_analyzer(actor, workspace_id=body.workspace_id, section=body.section, manufacturer=body.manufacturer, model=body.model, serial_fingerprint=body.serial_fingerprint, protocol=body.protocol, key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/clinical/lab/analyzers/{analyzer_id}/transition")
def transition_analyzer(analyzer_id: str, body: AnalyzerActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "lab.analyzer.transition", "lab_analyzer", analyzer_id, body.workspace_id, lambda: LISAdvancedService(db).transition_analyzer(actor, analyzer_id=analyzer_id, workspace_id=body.workspace_id, target_status=body.target_status, expected_version=expected, key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/clinical/lab/analyzer-messages", status_code=201)
def receive_analyzer_message(body: AnalyzerMessageRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "lab.analyzer_message.receive", "lab_analyzer_message", None, body.workspace_id, lambda: LISAdvancedService(db).receive_analyzer_message(actor, workspace_id=body.workspace_id, message_id=body.message_id, analyzer_id=body.analyzer_id, specimen_id=body.specimen_id, test_code=body.test_code, payload_hash=body.payload_hash, quality_flags=body.quality_flags, source=body.source, occurred_at=body.occurred_at, key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/clinical/lab/qc", status_code=201)
def create_qc(body: QCCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "lab.qc.create", "lab_quality_control", None, body.workspace_id, lambda: LISAdvancedService(db).create_qc(actor, workspace_id=body.workspace_id, result_id=body.result_id, analyzer_id=body.analyzer_id, status=body.status, reason=body.reason, override_reason=body.override_reason, expected_version=expected, key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))
