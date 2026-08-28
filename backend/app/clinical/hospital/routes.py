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
    AdmissionCreateRequest,
    BedAllocationRequest,
    BedCreateRequest,
    CareTeamMemberCreateRequest,
    DischargeCreateRequest,
    DischargeReadinessRequest,
    DischargeSummaryRequest,
    HandoverAcknowledgeRequest,
    HandoverCreateRequest,
    MedicationAdministrationActionRequest,
    MedicationAdministrationCreateRequest,
    NursingTaskCreateRequest,
    ResourceActionRequest,
    RoomCreateRequest,
    SafetyEventCreateRequest,
    TransferCreateRequest,
    VitalCreateRequest,
    WardCreateRequest,
    WorkflowActionRequest,
)
from .service import CanonicalHospitalService

router = APIRouter(tags=["Core Hospital"])


def _run(request: Request, actor: NiamActor, db: Session, operation: str, target_type: str, target_id: str | None, workspace_id: str, callback: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    _actor_rate_limit(request, actor)
    try:
        result = callback()
        db.commit()
        return result
    except Exception as exc:
        _handle_error(exc, db=db, actor=actor, request=request, operation=operation, target_type=target_type, target_id=target_id, workspace_id=workspace_id)
        raise AssertionError("unreachable") from exc


@router.post("/api/v1/hospital/wards", status_code=status.HTTP_201_CREATED)
def create_ward(body: WardCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "hospital.ward.create", "hospital_ward", None, body.workspace_id, lambda: CanonicalHospitalService(db).create_ward(actor, workspace_id=body.workspace_id, code=body.code, name=body.name, capacity=body.capacity, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/rooms", status_code=status.HTTP_201_CREATED)
def create_room(body: RoomCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "hospital.room.create", "hospital_room", None, body.workspace_id, lambda: CanonicalHospitalService(db).create_room(actor, workspace_id=body.workspace_id, ward_id=body.ward_id, code=body.code, name=body.name, capacity=body.capacity, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/beds", status_code=status.HTTP_201_CREATED)
def create_bed(body: BedCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "hospital.bed.create", "hospital_bed", None, body.workspace_id, lambda: CanonicalHospitalService(db).create_bed(actor, workspace_id=body.workspace_id, room_id=body.room_id, code=body.code, bed_type=body.bed_type, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/care-team", status_code=status.HTTP_201_CREATED)
def add_care_team_member(body: CareTeamMemberCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "hospital.care_team.create", "hospital_care_team_member", None, body.workspace_id, lambda: CanonicalHospitalService(db).add_care_team_member(actor, admission_id=body.admission_id, workspace_id=body.workspace_id, account_id=body.account_id, role=body.role, member_scope=body.scope, purpose=body.purpose, starts_at=body.starts_at, ends_at=body.ends_at, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/admissions", status_code=status.HTTP_201_CREATED)
def create_admission(body: AdmissionCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "hospital.admission.create", "hospital_admission", None, body.workspace_id, lambda: CanonicalHospitalService(db).create_admission(actor, admission_request_id=body.admission_request_id, encounter_id=body.encounter_id, workspace_id=body.workspace_id, ward_id=body.ward_id, admission_reason=body.admission_reason, admission_type=body.admission_type, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/admissions/{admission_id}/transition")
def transition_admission(admission_id: str, body: WorkflowActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "hospital.admission.transition", "hospital_admission", admission_id, body.workspace_id, lambda: CanonicalHospitalService(db).transition_admission(actor, admission_id=admission_id, workspace_id=body.workspace_id, target_status=body.target_status, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/beds/allocate", status_code=status.HTTP_201_CREATED)
def allocate_bed(body: BedAllocationRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "hospital.bed.allocate", "hospital_bed", body.bed_id, body.workspace_id, lambda: CanonicalHospitalService(db).allocate_bed(actor, admission_id=body.admission_id, bed_id=body.bed_id, workspace_id=body.workspace_id, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/tasks", status_code=status.HTTP_201_CREATED)
def create_task(body: NursingTaskCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "hospital.task.create", "hospital_nursing_task", None, body.workspace_id, lambda: CanonicalHospitalService(db).create_task(actor, admission_id=body.admission_id, workspace_id=body.workspace_id, task_type=body.task_type, instructions=body.instructions, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/tasks/{task_id}/transition")
def transition_task(task_id: str, body: WorkflowActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "hospital.task.transition", "hospital_nursing_task", task_id, body.workspace_id, lambda: CanonicalHospitalService(db).transition_task(actor, task_id=task_id, workspace_id=body.workspace_id, target_status=body.target_status, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/vitals", status_code=status.HTTP_201_CREATED)
def record_vital(body: VitalCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "hospital.vital.create", "hospital_vital_observation", None, body.workspace_id, lambda: CanonicalHospitalService(db).record_vital(actor, admission_id=body.admission_id, encounter_id=body.encounter_id, workspace_id=body.workspace_id, vital_type=body.vital_type, value_numeric=body.value_numeric, unit=body.unit, method=body.method, source=body.source, observed_at=body.observed_at, device_reference=body.device_reference, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/medications", status_code=status.HTTP_201_CREATED)
def create_emar(body: MedicationAdministrationCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "hospital.emar.create", "hospital_emar", None, body.workspace_id, lambda: CanonicalHospitalService(db).create_emar(actor, admission_id=body.admission_id, prescription_id=body.prescription_id, prescription_item_id=body.prescription_item_id, workspace_id=body.workspace_id, administration_key=body.administration_key, dose_value=body.dose_value, dose_unit=body.dose_unit, route=body.route, scheduled_at=body.scheduled_at, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/medications/{administration_id}/transition")
def transition_emar(administration_id: str, body: MedicationAdministrationActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "hospital.emar.transition", "hospital_emar", administration_id, body.workspace_id, lambda: CanonicalHospitalService(db).transition_emar(actor, administration_id=administration_id, workspace_id=body.workspace_id, target_status=body.target_status, reason=body.reason, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/medications/{administration_id}/safety-events", status_code=status.HTTP_201_CREATED)
def create_safety_event(administration_id: str, body: SafetyEventCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "hospital.emar.safety_event", "hospital_medication_safety_event", administration_id, body.workspace_id, lambda: CanonicalHospitalService(db).create_safety_event(actor, administration_id=administration_id, workspace_id=body.workspace_id, event_type=body.event_type, severity=body.severity, description=body.description, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/transfers", status_code=status.HTTP_201_CREATED)
def create_transfer(body: TransferCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "hospital.transfer.create", "hospital_transfer", None, body.workspace_id, lambda: CanonicalHospitalService(db).create_transfer(actor, transfer_request_id=body.transfer_request_id, admission_id=body.admission_id, from_bed_id=body.from_bed_id, to_bed_id=body.to_bed_id, workspace_id=body.workspace_id, reason=body.reason, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/transfers/{transfer_id}/transition")
def transition_transfer(transfer_id: str, body: WorkflowActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "hospital.transfer.transition", "hospital_transfer", transfer_id, body.workspace_id, lambda: CanonicalHospitalService(db).transition_transfer(actor, transfer_id=transfer_id, workspace_id=body.workspace_id, target_status=body.target_status, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/handovers", status_code=status.HTTP_201_CREATED)
def create_handover(body: HandoverCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "hospital.handover.create", "hospital_handover", None, body.workspace_id, lambda: CanonicalHospitalService(db).create_handover(actor, handover_request_id=body.handover_request_id, admission_id=body.admission_id, workspace_id=body.workspace_id, minimal_summary=body.minimal_summary, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/handovers/{handover_id}/ack")
def acknowledge_handover(handover_id: str, body: HandoverAcknowledgeRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "hospital.handover.ack", "hospital_handover", handover_id, body.workspace_id, lambda: CanonicalHospitalService(db).acknowledge_handover(actor, handover_id=handover_id, workspace_id=body.workspace_id, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/discharge", status_code=status.HTTP_201_CREATED)
def create_discharge(body: DischargeCreateRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "hospital.discharge.create", "hospital_discharge", None, body.workspace_id, lambda: CanonicalHospitalService(db).create_discharge(actor, discharge_request_id=body.discharge_request_id, admission_id=body.admission_id, workspace_id=body.workspace_id, disposition=body.disposition, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/discharge/{discharge_id}/readiness")
def update_discharge_readiness(discharge_id: str, body: DischargeReadinessRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "hospital.discharge.readiness", "hospital_discharge", discharge_id, body.workspace_id, lambda: CanonicalHospitalService(db).update_discharge_readiness(actor, discharge_id=discharge_id, workspace_id=body.workspace_id, medication_reconciliation_complete=body.medication_reconciliation_complete, pending_results_reviewed=body.pending_results_reviewed, follow_up_plan=body.follow_up_plan, instructions=body.instructions, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/discharge/{discharge_id}/summary", status_code=status.HTTP_201_CREATED)
def create_discharge_summary(discharge_id: str, body: DischargeSummaryRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    return _run(request, actor, db, "hospital.discharge.summary.create", "hospital_discharge_summary", discharge_id, body.workspace_id, lambda: CanonicalHospitalService(db).create_discharge_summary(actor, discharge_id=discharge_id, workspace_id=body.workspace_id, data=body.model_dump(exclude={"workspace_id"}), idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/discharge-summaries/{summary_id}/sign")
def sign_discharge_summary(summary_id: str, body: ResourceActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "hospital.discharge.summary.sign", "hospital_discharge_summary", summary_id, body.workspace_id, lambda: CanonicalHospitalService(db).sign_discharge_summary(actor, summary_id=summary_id, workspace_id=body.workspace_id, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))


@router.post("/api/v1/hospital/discharge/{discharge_id}/complete")
def complete_discharge(discharge_id: str, body: ResourceActionRequest, request: Request, actor: NiamActor = Depends(get_current_niam_actor_sync), db: Session = Depends(get_db), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"), if_match: str | None = Header(default=None, alias="If-Match")) -> dict[str, Any]:
    key = _require_idempotency_key(idempotency_key)
    expected = _require_if_match(if_match)
    return _run(request, actor, db, "hospital.discharge.complete", "hospital_discharge", discharge_id, body.workspace_id, lambda: CanonicalHospitalService(db).complete_discharge(actor, discharge_id=discharge_id, workspace_id=body.workspace_id, expected_version=expected, idempotency_key=key, correlation_id=_correlation_id(request), request_id=getattr(request.state, "request_id", None)))
