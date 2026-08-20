from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.clinical.command_guard import ClinicalCommandGuard
from app.critical_care.application.service import CriticalCareService
from app.critical_care.exceptions import (
    BedNotAvailableError,
    ICUAdmissionNotFoundError,
    ICUValidationError,
    ICUWorkflowError,
    InfusionNotFoundError,
    MonitoringRecordNotFoundError,
)
from app.critical_care.infrastructure.models import (
    ContinuousInfusionModel,
    CriticalAlertModel,
    ICUAdmissionModel,
    ICUBedModel,
)
from app.database import get_db
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user, require_permission

router = APIRouter(
    prefix="/critical-care",
    tags=["National Critical Care Platform"],
    dependencies=[Depends(require_permission("system:admin"))],
)


def _lab_id(current_user: LabUser) -> int:
    lab_id = getattr(current_user, "lab_id", None)
    if not isinstance(lab_id, int) or lab_id <= 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Institutional laboratory context is required")
    return lab_id


def _guard(db: Session, current_user: LabUser) -> ClinicalCommandGuard:
    return ClinicalCommandGuard(
        db,
        actor_user_id=current_user.id,
        lab_id=_lab_id(current_user),
        actor_role=current_user.role,
    )


def _raise_icu_error(error: Exception) -> None:
    if isinstance(error, (ICUValidationError, ICUWorkflowError, BedNotAvailableError)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    if isinstance(error, (ICUAdmissionNotFoundError, InfusionNotFoundError, MonitoringRecordNotFoundError)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from error
    raise error


def _get_service(db: Session = Depends(get_db)) -> CriticalCareService:
    try:
        from app.kernel import Kernel
        kernel = Kernel.get_instance()
        event_bus = kernel.event_bus if hasattr(kernel, "event_bus") else None
    except Exception:
        event_bus = None
    return CriticalCareService(db=db, event_bus=event_bus)


# ---- Admissions ----

@router.post("/admissions", status_code=status.HTTP_201_CREATED)
async def admit_patient(
    body: dict[str, Any],
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    """Admit only into the current, compatible, unoccupied ICU bed."""
    lab_id = _lab_id(current_user)
    bed_id = body.get("bed_id")
    bed = (
        db.query(ICUBedModel)
        .filter(ICUBedModel.id == bed_id, ICUBedModel.lab_id == lab_id)
        .with_for_update()
        .first()
    )
    if not bed:
        raise HTTPException(status_code=404, detail="Resource not found")
    guard = _guard(db, current_user)
    version_before = bed.version
    state_before = "occupied" if bed.is_occupied else "available"
    guard.require_expected_version(if_match, current_version=version_before, resource_name="ICU bed")
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(
        operation="icu.admission.create", resource_type="icu_bed", resource_id=bed.id,
        idempotency_key=key, payload=body,
    )
    try:
        body = {**body, "lab_id": lab_id}
        admission = CriticalCareService(db).admit_patient_safely(body)
        guard.complete(
            receipt, resource_type="icu_admission", resource_id=admission.id,
            state_before=state_before, state_after=admission.status,
            version_before=version_before, version_after=bed.version,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        guard.reject(
            operation="icu.admission.create", resource_type="icu_bed", resource_id=bed.id,
            state_before=state_before, version_before=version_before, reason=str(exc),
        )
        db.commit()
        _raise_icu_error(exc)
    db.refresh(admission)
    return _admission_to_dict(admission)


@router.get("/admissions")
async def list_admissions(
    icu_type: str | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: LabUser = Depends(get_current_user),
    service: CriticalCareService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_admission_to_dict(a) for a in service.list_admissions(_lab_id(current_user), icu_type, status, skip, limit)]


@router.get("/admissions/{admission_id}")
async def get_admission(
    admission_id: str,
    current_user: LabUser = Depends(get_current_user),
    service: CriticalCareService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _admission_to_dict(service.get_admission(admission_id, _lab_id(current_user)))
    except ICUAdmissionNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e


@router.post("/admissions/{admission_id}/discharge")
async def discharge_patient(
    admission_id: str,
    body: dict[str, Any],
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    lab_id = _lab_id(current_user)
    admission = (
        db.query(ICUAdmissionModel)
        .filter(ICUAdmissionModel.id == admission_id, ICUAdmissionModel.lab_id == lab_id)
        .with_for_update()
        .first()
    )
    if not admission:
        raise HTTPException(status_code=404, detail="Resource not found")
    guard = _guard(db, current_user)
    version_before = admission.version
    state_before = admission.status
    guard.require_expected_version(if_match, current_version=version_before, resource_name="ICU admission")
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(
        operation="icu.admission.discharge", resource_type="icu_admission", resource_id=admission.id,
        idempotency_key=key, payload=body,
    )
    try:
        discharged = CriticalCareService(db).discharge_patient_safely(admission_id, body, lab_id)
        guard.complete(
            receipt, resource_type="icu_admission", resource_id=discharged.id,
            state_before=state_before, state_after=discharged.status,
            version_before=version_before, version_after=discharged.version,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        guard.reject(
            operation="icu.admission.discharge", resource_type="icu_admission", resource_id=admission_id,
            state_before=state_before, version_before=version_before, reason=str(exc),
        )
        db.commit()
        _raise_icu_error(exc)
    db.refresh(discharged)
    return _admission_to_dict(discharged)


# ---- Beds ----

@router.post("/beds", status_code=status.HTTP_201_CREATED)
async def register_bed(
    body: dict[str, Any],
    service: CriticalCareService = Depends(_get_service),
) -> dict[str, Any]:
    return _bed_to_dict(service.register_bed(body))


@router.get("/beds/availability")
async def get_bed_availability(
    icu_type: str | None = Query(None),
    current_user: LabUser = Depends(get_current_user),
    service: CriticalCareService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return service.get_bed_availability(_lab_id(current_user), icu_type)


# ---- Vital Signs ----

@router.post("/vitals", status_code=status.HTTP_201_CREATED)
async def record_vitals(
    body: dict[str, Any],
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    lab_id = _lab_id(current_user)
    admission = (
        db.query(ICUAdmissionModel)
        .filter(
            ICUAdmissionModel.id == body.get("admission_id"),
            ICUAdmissionModel.patient_id == body.get("patient_id"),
            ICUAdmissionModel.lab_id == lab_id,
        )
        .with_for_update()
        .first()
    )
    if not admission:
        raise HTTPException(status_code=404, detail="Resource not found")
    guard = _guard(db, current_user)
    version_before = admission.version
    guard.require_expected_version(if_match, current_version=version_before, resource_name="ICU admission")
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(
        operation="icu.vitals.record", resource_type="icu_admission", resource_id=admission.id,
        idempotency_key=key, payload=body,
    )
    try:
        vitals = CriticalCareService(db).record_vitals_safely({**body, "lab_id": lab_id})
        guard.complete(
            receipt, resource_type="icu_vitals", resource_id=vitals.id,
            state_before="active", state_after="recorded",
            version_before=version_before, version_after=admission.version,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        guard.reject(
            operation="icu.vitals.record", resource_type="icu_admission", resource_id=admission.id,
            state_before="active", version_before=version_before, reason=str(exc),
        )
        db.commit()
        _raise_icu_error(exc)
    db.refresh(vitals)
    return _vitals_to_dict(vitals)


@router.get("/vitals/{patient_id}")
async def get_vitals(
    patient_id: str,
    limit: int = Query(100, ge=1, le=1000),
    current_user: LabUser = Depends(get_current_user),
    service: CriticalCareService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_vitals_to_dict(v) for v in service.get_vitals(patient_id, _lab_id(current_user), limit)]


# ---- Ventilator ----

@router.post("/ventilator", status_code=status.HTTP_201_CREATED)
async def set_ventilator(
    body: dict[str, Any],
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    lab_id = _lab_id(current_user)
    admission = (
        db.query(ICUAdmissionModel)
        .filter(
            ICUAdmissionModel.id == body.get("admission_id"),
            ICUAdmissionModel.patient_id == body.get("patient_id"),
            ICUAdmissionModel.lab_id == lab_id,
        )
        .with_for_update()
        .first()
    )
    if not admission:
        raise HTTPException(status_code=404, detail="Resource not found")
    guard = _guard(db, current_user)
    version_before = admission.version
    guard.require_expected_version(if_match, current_version=version_before, resource_name="ICU admission")
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(
        operation="icu.ventilator.set", resource_type="icu_admission", resource_id=admission.id,
        idempotency_key=key, payload=body,
    )
    try:
        settings = CriticalCareService(db).set_ventilator_safely(
            {**body, "lab_id": lab_id, "set_by": str(current_user.id)},
        )
        guard.complete(
            receipt, resource_type="icu_ventilator_setting", resource_id=settings.id,
            state_before="active", state_after="recorded",
            version_before=version_before, version_after=admission.version,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        guard.reject(
            operation="icu.ventilator.set", resource_type="icu_admission", resource_id=admission.id,
            state_before="active", version_before=version_before, reason=str(exc),
        )
        db.commit()
        _raise_icu_error(exc)
    db.refresh(settings)
    return _ventilator_to_dict(settings)


@router.get("/ventilator/{patient_id}")
async def get_ventilator_settings(
    patient_id: str,
    limit: int = Query(50, ge=1, le=500),
    current_user: LabUser = Depends(get_current_user),
    service: CriticalCareService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_ventilator_to_dict(v) for v in service.get_ventilator_settings(patient_id, _lab_id(current_user), limit)]


# ---- Early Warning Scores ----

@router.post("/ews/{patient_id}")
async def calculate_ews(
    patient_id: str,
    body: dict[str, Any],
    service: CriticalCareService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        ews = service.calculate_ews(patient_id, body.get("admission_id", ""), body.get("vitals_id"))
        return _ews_to_dict(ews)
    except MonitoringRecordNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e


@router.post("/sofa/{patient_id}")
async def calculate_sofa(
    patient_id: str,
    body: dict[str, Any],
    service: CriticalCareService = Depends(_get_service),
) -> dict[str, Any]:
    score = service.calculate_sofa(patient_id, body.get("admission_id", ""), body)
    return _score_to_dict(score)


# ---- Infusions ----

@router.post("/infusions", status_code=status.HTTP_201_CREATED)
async def start_infusion(
    body: dict[str, Any],
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    lab_id = _lab_id(current_user)
    admission = (
        db.query(ICUAdmissionModel)
        .filter(
            ICUAdmissionModel.id == body.get("admission_id"),
            ICUAdmissionModel.patient_id == body.get("patient_id"),
            ICUAdmissionModel.lab_id == lab_id,
        )
        .with_for_update()
        .first()
    )
    if not admission:
        raise HTTPException(status_code=404, detail="Resource not found")
    guard = _guard(db, current_user)
    version_before = admission.version
    guard.require_expected_version(if_match, current_version=version_before, resource_name="ICU admission")
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(
        operation="icu.infusion.start", resource_type="icu_admission", resource_id=admission.id,
        idempotency_key=key, payload=body,
    )
    try:
        infusion = CriticalCareService(db).start_infusion_safely(
            {**body, "lab_id": lab_id, "initiated_by": str(current_user.id)},
        )
        guard.complete(
            receipt, resource_type="icu_infusion", resource_id=infusion.id,
            state_before="not_started", state_after=infusion.status,
            version_before=version_before, version_after=admission.version,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        guard.reject(
            operation="icu.infusion.start", resource_type="icu_admission", resource_id=admission.id,
            state_before="active", version_before=version_before, reason=str(exc),
        )
        db.commit()
        _raise_icu_error(exc)
    db.refresh(infusion)
    return _infusion_to_dict(infusion)


@router.post("/infusions/{infusion_id}/stop")
async def stop_infusion(
    infusion_id: str,
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    lab_id = _lab_id(current_user)
    infusion = (
        db.query(ContinuousInfusionModel)
        .filter(ContinuousInfusionModel.id == infusion_id, ContinuousInfusionModel.lab_id == lab_id)
        .with_for_update()
        .first()
    )
    if not infusion:
        raise HTTPException(status_code=404, detail="Resource not found")
    guard = _guard(db, current_user)
    version_before = infusion.version
    state_before = infusion.status
    guard.require_expected_version(if_match, current_version=version_before, resource_name="infusion")
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(
        operation="icu.infusion.stop", resource_type="icu_infusion", resource_id=infusion.id,
        idempotency_key=key, payload={"infusion_id": infusion_id},
    )
    try:
        stopped = CriticalCareService(db).stop_infusion_safely(infusion_id, lab_id)
        guard.complete(
            receipt, resource_type="icu_infusion", resource_id=stopped.id,
            state_before=state_before, state_after=stopped.status,
            version_before=version_before, version_after=stopped.version,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        guard.reject(
            operation="icu.infusion.stop", resource_type="icu_infusion", resource_id=infusion_id,
            state_before=state_before, version_before=version_before, reason=str(exc),
        )
        db.commit()
        _raise_icu_error(exc)
    db.refresh(stopped)
    return _infusion_to_dict(stopped)


# ---- Fluid Balance ----

@router.post("/fluid-balance", status_code=status.HTTP_201_CREATED)
async def record_fluid_balance(
    body: dict[str, Any],
    service: CriticalCareService = Depends(_get_service),
) -> dict[str, Any]:
    return _fluid_to_dict(service.record_fluid_balance(body))


# ---- Alerts ----

@router.post("/alerts", status_code=status.HTTP_201_CREATED)
async def raise_alert(
    body: dict[str, Any],
    service: CriticalCareService = Depends(_get_service),
) -> dict[str, Any]:
    return _alert_to_dict(service.raise_alert(body))


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    body: dict[str, Any],
    current_user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    if_match: str | None = Header(None, alias="If-Match"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> dict[str, Any]:
    lab_id = _lab_id(current_user)
    alert = (
        db.query(CriticalAlertModel)
        .filter(CriticalAlertModel.id == alert_id, CriticalAlertModel.lab_id == lab_id)
        .with_for_update()
        .first()
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Resource not found")
    guard = _guard(db, current_user)
    version_before = alert.version
    state_before = "active" if alert.is_active else "inactive"
    guard.require_expected_version(if_match, current_version=version_before, resource_name="critical alert")
    key = guard.require_idempotency_key(idempotency_key)
    receipt = guard.claim(
        operation="icu.alert.acknowledge", resource_type="icu_alert", resource_id=alert.id,
        idempotency_key=key, payload=body,
    )
    try:
        acknowledged = CriticalCareService(db).acknowledge_alert_safely(
            alert_id, str(current_user.id), lab_id,
        )
        guard.complete(
            receipt, resource_type="icu_alert", resource_id=acknowledged.id,
            state_before=state_before, state_after="acknowledged",
            version_before=version_before, version_after=acknowledged.version,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        guard.reject(
            operation="icu.alert.acknowledge", resource_type="icu_alert", resource_id=alert_id,
            state_before=state_before, version_before=version_before, reason=str(exc),
        )
        db.commit()
        _raise_icu_error(exc)
    db.refresh(acknowledged)
    return _alert_to_dict(acknowledged)


# ---- Rounds ----

@router.post("/rounds", status_code=status.HTTP_201_CREATED)
async def record_round(
    body: dict[str, Any],
    service: CriticalCareService = Depends(_get_service),
) -> dict[str, Any]:
    return _round_to_dict(service.record_round(body))


# ---- Dashboard ----

@router.get("/dashboard")
async def get_dashboard(
    current_user: LabUser = Depends(get_current_user),
    service: CriticalCareService = Depends(_get_service),
) -> dict[str, Any]:
    return service.get_dashboard_stats(_lab_id(current_user))


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "module": "national_critical_care_platform", "version": "1.0.0"}


# ---- Serializers ----

def _admission_to_dict(a: Any) -> dict[str, Any]:
    return {
        "id": a.id, "patient_id": a.patient_id, "patient_name": getattr(a, "patient_name", ""),
        "icu_type": a.icu_type if not hasattr(a.icu_type, "value") else a.icu_type.value,
        "admission_type": getattr(a, "admission_type", ""),
        "admission_diagnosis": getattr(a, "admission_diagnosis", ""),
        "status": a.status if not hasattr(a.status, "value") else a.status.value,
        "bed_id": getattr(a, "bed_id", ""), "facility_id": getattr(a, "facility_id", ""),
        "created_at": getattr(a, "created_at", None),
        "discharged_at": getattr(a, "discharged_at", None),
    }


def _bed_to_dict(b: Any) -> dict[str, Any]:
    return {"id": b.id, "bed_label": b.bed_label, "icu_type": b.icu_type if not hasattr(b.icu_type, "value") else b.icu_type.value}


def _vitals_to_dict(v: Any) -> dict[str, Any]:
    return {
        "id": v.id, "patient_id": v.patient_id, "heart_rate": v.heart_rate,
        "respiratory_rate": v.respiratory_rate, "systolic_bp": v.systolic_bp,
        "diastolic_bp": v.diastolic_bp, "temperature": v.temperature,
        "oxygen_saturation": v.oxygen_saturation, "gcs_total": v.gcs_total,
        "recorded_at": v.recorded_at.isoformat() if v.recorded_at else None,
    }


def _ventilator_to_dict(v: Any) -> dict[str, Any]:
    return {
        "id": v.id, "patient_id": v.patient_id,
        "mode": v.mode if not hasattr(v.mode, "value") else v.mode.value,
        "tidal_volume_ml": getattr(v, "tidal_volume_ml", None),
        "peep_cmh2o": getattr(v, "peep_cmh2o", None),
        "fi_o2": getattr(v, "fi_o2", None),
        "respiratory_rate_set": getattr(v, "respiratory_rate_set", None),
    }


def _ews_to_dict(e: Any) -> dict[str, Any]:
    return {
        "id": e.id, "patient_id": e.patient_id, "score_system": e.score_system,
        "score_value": e.score_value, "risk_category": e.risk_category,
        "recommended_frequency": e.recommended_frequency,
        "triggers_escalation": e.triggers_escalation,
    }


def _score_to_dict(s: Any) -> dict[str, Any]:
    return {
        "id": s.id, "patient_id": s.patient_id, "score_type": s.score_type,
        "score_value": s.score_value, "mortality_prediction": s.mortality_prediction,
    }


def _infusion_to_dict(i: Any) -> dict[str, Any]:
    return {
        "id": i.id, "patient_id": i.patient_id, "medication": i.medication,
        "rate": getattr(i, "rate", ""), "status": i.status,
    }


def _fluid_to_dict(f: Any) -> dict[str, Any]:
    return {
        "id": f.id, "patient_id": f.patient_id,
        "total_intake_ml": f.total_intake_ml, "total_output_ml": f.total_output_ml,
        "net_balance_ml": f.net_balance_ml,
    }


def _alert_to_dict(a: Any) -> dict[str, Any]:
    return {
        "id": a.id, "patient_id": a.patient_id, "alert_type": a.alert_type,
        "severity": a.severity if not hasattr(a.severity, "value") else a.severity.value,
        "alert_message": getattr(a, "alert_message", ""),
        "is_active": a.is_active if hasattr(a, "is_active") else True,
    }


def _round_to_dict(r: Any) -> dict[str, Any]:
    return {
        "id": r.id, "patient_id": r.patient_id,
        "attending_physician": getattr(r, "attending_physician", ""),
    }
