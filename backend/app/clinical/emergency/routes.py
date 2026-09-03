from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, Header, Request, status
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
    BreakGlassActionRequest,
    BreakGlassRequest,
    DispatchCreateRequest,
    EPCRActionRequest,
    EPCRAmendRequest,
    EPCRCreateRequest,
    HandoverAmendRequest,
    HandoverCreateRequest,
    IncidentCreateRequest,
    PrealertCreateRequest,
    TemporarySubjectCreateRequest,
    TemporarySubjectReconciliationRequest,
    TreatmentCreateRequest,
    TriageCreateRequest,
    WorkflowActionRequest,
)
from .service import CanonicalEmergencyService

router = APIRouter(tags=["Core Emergency"])


def _run(request: Request, actor: NiamActor, db: Session, operation: str, target_type: str, target_id: str | None, workspace_id: str, callback: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    _actor_rate_limit(request, actor)
    try:
        result = callback()
        db.commit()
        return result
    except Exception as exc:
        _handle_error(exc, db=db, actor=actor, request=request, operation=operation, target_type=target_type, target_id=target_id, workspace_id=workspace_id)
        raise AssertionError("unreachable") from exc


@router.post("/api/v1/emergency/break-glass", status_code=status.HTTP_201_CREATED)
def request_break_glass(body: BreakGlassRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "emergency.break_glass.request", "emergency_break_glass", None, body.workspace_id, lambda: CanonicalEmergencyService(db).request_break_glass(actor, request_id=body.request_id, workspace_id=body.workspace_id, patient_person_id=body.patient_person_id, reason=body.reason, purpose=body.purpose, resource_scope=body.resource_scope, duration_minutes=body.duration_minutes, idempotency_key=key, correlation_id=_correlation_id(request), request_id_header=getattr(request.state, "request_id", None)))


@router.post("/api/v1/emergency/break-glass/{break_glass_id}/activate")
def activate_break_glass(break_glass_id: str, body: BreakGlassActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "emergency.break_glass.activate", "emergency_break_glass", break_glass_id, body.workspace_id, lambda: CanonicalEmergencyService(db).activate_break_glass(actor, break_glass_id=break_glass_id, workspace_id=body.workspace_id, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/emergency/break-glass/{break_glass_id}/revoke")
def revoke_break_glass(break_glass_id: str, body: BreakGlassActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "emergency.break_glass.revoke", "emergency_break_glass", break_glass_id, body.workspace_id, lambda: CanonicalEmergencyService(db).revoke_break_glass(actor, break_glass_id=break_glass_id, workspace_id=body.workspace_id, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/emergency/temporary-subjects", status_code=status.HTTP_201_CREATED)
def create_temporary_subject(body: TemporarySubjectCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "emergency.subject.create", "emergency_temporary_subject", None, body.workspace_id, lambda: CanonicalEmergencyService(db).create_temporary_subject(actor, workspace_id=body.workspace_id, synthetic_label=body.synthetic_label, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/emergency/temporary-subjects/{temporary_subject_id}/reconcile")
def reconcile_temporary_subject(temporary_subject_id: str, body: TemporarySubjectReconciliationRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "emergency.subject.reconcile", "emergency_temporary_subject", temporary_subject_id, body.workspace_id, lambda: CanonicalEmergencyService(db).reconcile_temporary_subject(actor, temporary_subject_id=temporary_subject_id, workspace_id=body.workspace_id, resolution=body.resolution, person_id=body.person_id, reason=body.reason, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/emergency/incidents", status_code=status.HTTP_201_CREATED)
def create_incident(body: IncidentCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "emergency.incident.create", "emergency_incident", None, body.workspace_id, lambda: CanonicalEmergencyService(db).create_incident(actor, incident_id=body.incident_id, workspace_id=body.workspace_id, chief_complaint=body.chief_complaint, priority=body.priority, patient_person_id=body.patient_person_id, temporary_subject_id=body.temporary_subject_id, location_summary=body.location_summary, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/emergency/incidents/{incident_id}/transition")
def transition_incident(incident_id: str, body: WorkflowActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "emergency.incident.transition", "emergency_incident", incident_id, body.workspace_id, lambda: CanonicalEmergencyService(db).transition_incident(actor, incident_id=incident_id, workspace_id=body.workspace_id, target_status=body.target_status, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/emergency/triage", status_code=status.HTTP_201_CREATED)
def create_triage(body: TriageCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "emergency.triage.create", "emergency_triage", None, body.workspace_id, lambda: CanonicalEmergencyService(db).create_triage(actor, incident_id=body.incident_id, workspace_id=body.workspace_id, triage_id=body.triage_id, category=body.category, clinician_summary=body.clinician_summary, vital_snapshot=body.vital_snapshot, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/emergency/dispatches", status_code=status.HTTP_201_CREATED)
def create_dispatch(body: DispatchCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "emergency.dispatch.create", "emergency_dispatch", None, body.workspace_id, lambda: CanonicalEmergencyService(db).create_dispatch(actor, dispatch_request_id=body.dispatch_request_id, incident_id=body.incident_id, workspace_id=body.workspace_id, ambulance_reference=body.ambulance_reference, crew_references=body.crew_references, dispatch_notes=body.dispatch_notes, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/emergency/dispatches/{dispatch_id}/transition")
def transition_dispatch(dispatch_id: str, body: WorkflowActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "emergency.dispatch.transition", "emergency_dispatch", dispatch_id, body.workspace_id, lambda: CanonicalEmergencyService(db).transition_dispatch(actor, dispatch_id=dispatch_id, workspace_id=body.workspace_id, target_status=body.target_status, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/emergency/treatments", status_code=status.HTTP_201_CREATED)
def create_treatment(body: TreatmentCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "emergency.treatment.create", "emergency_treatment", None, body.workspace_id, lambda: CanonicalEmergencyService(db).create_treatment(actor, treatment_request_id=body.treatment_request_id, incident_id=body.incident_id, workspace_id=body.workspace_id, treatment_type=body.treatment_type, treatment_details=body.treatment_details, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/emergency/prealerts", status_code=status.HTTP_201_CREATED)
def create_prealert(body: PrealertCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "emergency.prealert.create", "emergency_prealert", None, body.workspace_id, lambda: CanonicalEmergencyService(db).create_prealert(actor, prealert_request_id=body.prealert_request_id, incident_id=body.incident_id, workspace_id=body.workspace_id, destination_facility_reference=body.destination_facility_reference, acuity=body.acuity, estimated_arrival_minutes=body.estimated_arrival_minutes, minimal_payload=body.minimal_payload, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/emergency/prealerts/{prealert_id}/ack")
def acknowledge_prealert(prealert_id: str, body: WorkflowActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "emergency.prealert.ack", "emergency_prealert", prealert_id, body.workspace_id, lambda: CanonicalEmergencyService(db).acknowledge_prealert(actor, prealert_id=prealert_id, workspace_id=body.workspace_id, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/emergency/handovers", status_code=status.HTTP_201_CREATED)
def create_handover(body: HandoverCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "emergency.handover.create", "emergency_handover", None, body.workspace_id, lambda: CanonicalEmergencyService(db).create_handover(actor, handover_request_id=body.handover_request_id, incident_id=body.incident_id, workspace_id=body.workspace_id, receiving_facility_reference=body.receiving_facility_reference, minimal_summary=body.minimal_summary, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/emergency/handovers/{handover_id}/ack")
def acknowledge_handover(handover_id: str, body: WorkflowActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "emergency.handover.ack", "emergency_handover", handover_id, body.workspace_id, lambda: CanonicalEmergencyService(db).acknowledge_handover(actor, handover_id=handover_id, workspace_id=body.workspace_id, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/emergency/handovers/{handover_id}/amend", status_code=status.HTTP_201_CREATED)
def amend_handover(handover_id: str, body: HandoverAmendRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "emergency.handover.amend", "emergency_handover", handover_id, body.workspace_id, lambda: CanonicalEmergencyService(db).amend_handover(actor, handover_id=handover_id, workspace_id=body.workspace_id, handover_request_id=body.handover_request_id, receiving_facility_reference=body.receiving_facility_reference, minimal_summary=body.minimal_summary, amendment_reason=body.amendment_reason, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/emergency/epcr", status_code=status.HTTP_201_CREATED)
def create_epcr(body: EPCRCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "emergency.epcr.create", "emergency_epcr", None, body.workspace_id, lambda: CanonicalEmergencyService(db).create_epcr(actor, epcr_id=body.epcr_id, incident_id=body.incident_id, workspace_id=body.workspace_id, chief_complaint=body.chief_complaint, narrative=body.narrative, interventions=body.interventions, destination_facility_reference=body.destination_facility_reference, signature_evidence=body.signature_evidence, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/emergency/epcr/{epcr_id}/amend", status_code=status.HTTP_201_CREATED)
def amend_epcr(epcr_id: str, body: EPCRAmendRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "emergency.epcr.amend", "emergency_epcr", epcr_id, body.workspace_id, lambda: CanonicalEmergencyService(db).amend_epcr(actor, epcr_id=epcr_id, workspace_id=body.workspace_id, chief_complaint=body.chief_complaint, narrative=body.narrative, interventions=body.interventions, destination_facility_reference=body.destination_facility_reference, amendment_reason=body.amendment_reason, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/emergency/epcr/{epcr_id}/sign")
def sign_epcr(epcr_id: str, body: EPCRActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "emergency.epcr.sign", "emergency_epcr", epcr_id, body.workspace_id, lambda: CanonicalEmergencyService(db).sign_epcr(actor, epcr_id=epcr_id, workspace_id=body.workspace_id, expected_version=expected, signature_evidence=body.signature_evidence, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))
