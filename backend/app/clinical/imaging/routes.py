from __future__ import annotations

from collections.abc import Callable
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
    CriticalAcknowledgeRequest,
    ImagingInstanceIngestRequest,
    ImagingOrderActionRequest,
    ImagingOrderCreateRequest,
    ImagingReportActionRequest,
    ImagingReportAmendRequest,
    ImagingReportCreateRequest,
    ImagingStudyIngestRequest,
)
from .service import CanonicalImagingService

router = APIRouter(tags=["Core Imaging"])


def _run(request: Request, actor: NiamActor, db: Session, operation: str, target_type: str, target_id: str | None, workspace_id: str, callback: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    _actor_rate_limit(request, actor)
    try:
        result = callback()
        db.commit()
        return result
    except Exception as exc:
        _handle_error(exc, db=db, actor=actor, request=request, operation=operation, target_type=target_type, target_id=target_id, workspace_id=workspace_id)
        raise AssertionError("unreachable") from exc


@router.post("/api/v1/clinical/imaging-orders", status_code=status.HTTP_201_CREATED)
def create_imaging_order(body: ImagingOrderCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "imaging.order.create", "imaging_order", None, body.workspace_id, lambda: CanonicalImagingService(db).create_order(actor, encounter_id=body.encounter_id, workspace_id=body.workspace_id, modality=body.modality, body_part=body.body_part, clinical_indication=body.clinical_indication, priority=body.priority, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


for _target, _path in (("PLACED", "place"), ("SCHEDULED", "schedule"), ("IN_PROGRESS", "start"), ("COMPLETED", "complete")):
    def _order_transition(order_id: str, body: ImagingOrderActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match"), _target: str = _target) -> dict[str, Any]:
        key = _require_idempotency_key(idempotency_key)
        expected = _require_if_match(if_match)
        return _run(request, actor, db, f"imaging.order.{_target.lower()}", "imaging_order", order_id, body.workspace_id, lambda: CanonicalImagingService(db).transition_order(actor, order_id=order_id, workspace_id=body.workspace_id, target=_target, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))
    router.add_api_route(f"/api/v1/clinical/imaging-orders/{{order_id}}/{_path}", _order_transition, methods=["POST"])


@router.post("/api/v1/clinical/imaging-studies", status_code=status.HTTP_201_CREATED)
def ingest_study(body: ImagingStudyIngestRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "imaging.study.ingest", "imaging_study", None, body.workspace_id, lambda: CanonicalImagingService(db).ingest_study(actor, order_id=body.order_id, workspace_id=body.workspace_id, study_instance_uid=body.study_instance_uid, accession_number=body.accession_number, modality=body.modality, source_message_id=body.source_message_id, provenance_type=body.provenance_type, study_description=body.study_description, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


for _target, _path in (("MATCHED", "match"), ("ACQUIRED", "acquire"), ("COMPLETED", "complete")):
    def _study_transition(study_id: str, body: ImagingOrderActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match"), _target: str = _target) -> dict[str, Any]:
        key = _require_idempotency_key(idempotency_key)
        expected = _require_if_match(if_match)
        return _run(request, actor, db, f"imaging.study.{_target.lower()}", "imaging_study", study_id, body.workspace_id, lambda: CanonicalImagingService(db).transition_study(actor, study_id=study_id, workspace_id=body.workspace_id, target=_target, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))
    router.add_api_route(f"/api/v1/clinical/imaging-studies/{{study_id}}/{_path}", _study_transition, methods=["POST"])


@router.post("/api/v1/clinical/imaging-instances", status_code=status.HTTP_201_CREATED)
def ingest_instance(body: ImagingInstanceIngestRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "imaging.instance.ingest", "imaging_instance", None, body.workspace_id, lambda: CanonicalImagingService(db).ingest_instance(actor, study_id=body.study_id, workspace_id=body.workspace_id, series_instance_uid=body.series_instance_uid, sop_instance_uid=body.sop_instance_uid, source_message_id=body.source_message_id, object_reference=body.object_reference, checksum=body.checksum, file_size_bytes=body.file_size_bytes, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.get("/api/v1/clinical/imaging-orders/{order_id}/fhir")
def get_order_fhir(order_id: str, request: Request, workspace_id: str = Query(..., min_length=1, max_length=26), actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, "imaging.order.fhir", "imaging_order", order_id, workspace_id, lambda: CanonicalImagingService(db).fhir_order(actor, order_id=order_id, workspace_id=workspace_id, correlation_id=_correlation_id(request)))


@router.get("/api/v1/clinical/imaging-studies/{study_id}")
def get_study(study_id: str, request: Request, workspace_id: str = Query(..., min_length=1, max_length=26), actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, "imaging.study.read", "imaging_study", study_id, workspace_id, lambda: CanonicalImagingService(db).get_study(actor, study_id=study_id, workspace_id=workspace_id, correlation_id=_correlation_id(request)))


@router.get("/api/v1/clinical/imaging-studies/{study_id}/fhir")
def get_study_fhir(study_id: str, request: Request, workspace_id: str = Query(..., min_length=1, max_length=26), actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, "imaging.study.fhir", "imaging_study", study_id, workspace_id, lambda: CanonicalImagingService(db).fhir_study(actor, study_id=study_id, workspace_id=workspace_id, correlation_id=_correlation_id(request)))


@router.post("/api/v1/clinical/imaging-reports", status_code=status.HTTP_201_CREATED)
def create_report(body: ImagingReportCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "imaging.report.create", "imaging_report", None, body.workspace_id, lambda: CanonicalImagingService(db).create_report(actor, study_id=body.study_id, workspace_id=body.workspace_id, findings=body.findings, impression=body.impression, critical=body.critical, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.get("/api/v1/clinical/imaging-reports/{report_id}")
def get_report(report_id: str, request: Request, workspace_id: str = Query(..., min_length=1, max_length=26), actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, "imaging.report.read", "imaging_report", report_id, workspace_id, lambda: CanonicalImagingService(db).get_report(actor, report_id=report_id, workspace_id=workspace_id, correlation_id=_correlation_id(request)))


@router.get("/api/v1/clinical/imaging-reports/{report_id}/fhir")
def get_report_fhir(report_id: str, request: Request, workspace_id: str = Query(..., min_length=1, max_length=26), actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db)) -> dict[str, Any]:
    return _run(request, actor, db, "imaging.report.fhir", "imaging_report", report_id, workspace_id, lambda: CanonicalImagingService(db).fhir_report(actor, report_id=report_id, workspace_id=workspace_id, correlation_id=_correlation_id(request)))


@router.post("/api/v1/clinical/imaging-reports/{report_id}/sign")
def sign_report(report_id: str, body: ImagingReportActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "imaging.report.sign", "imaging_report", report_id, body.workspace_id, lambda: CanonicalImagingService(db).sign_report(actor, report_id=report_id, workspace_id=body.workspace_id, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/clinical/imaging-reports/{report_id}/release")
def release_report(report_id: str, body: ImagingReportActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "imaging.report.release", "imaging_report", report_id, body.workspace_id, lambda: CanonicalImagingService(db).release_report(actor, report_id=report_id, workspace_id=body.workspace_id, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/clinical/imaging-reports/{report_id}/amend")
def amend_report(report_id: str, body: ImagingReportAmendRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "imaging.report.amend", "imaging_report", report_id, body.workspace_id, lambda: CanonicalImagingService(db).amend_report(actor, report_id=report_id, workspace_id=body.workspace_id, expected_version=expected, reason=body.reason, findings=body.findings, impression=body.impression, critical=body.critical, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/clinical/imaging-critical/{report_id}/acknowledge")
def acknowledge_critical(report_id: str, body: CriticalAcknowledgeRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "imaging.critical.acknowledge", "imaging_critical_event", report_id, body.workspace_id, lambda: CanonicalImagingService(db).acknowledge_critical(actor, report_id=report_id, workspace_id=body.workspace_id, expected_version=expected, reason=body.reason, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))
