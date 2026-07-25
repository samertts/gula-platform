from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.critical_care.application.service import CriticalCareService
from app.critical_care.exceptions import (
    BedNotAvailableError,
    ICUAdmissionNotFoundError,
    InfusionNotFoundError,
    MonitoringRecordNotFoundError,
)
from app.database import get_db

router = APIRouter(prefix="/critical-care", tags=["National Critical Care Platform"])


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
    service: CriticalCareService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        admission = service.admit_patient(body)
        return _admission_to_dict(admission)
    except BedNotAvailableError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resource conflict") from e


@router.get("/admissions")
async def list_admissions(
    icu_type: str | None = Query(None),
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: CriticalCareService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_admission_to_dict(a) for a in service.list_admissions(icu_type, status, skip, limit)]


@router.get("/admissions/{admission_id}")
async def get_admission(
    admission_id: str,
    service: CriticalCareService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _admission_to_dict(service.get_admission(admission_id))
    except ICUAdmissionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


@router.post("/admissions/{admission_id}/discharge")
async def discharge_patient(
    admission_id: str,
    body: dict[str, Any],
    service: CriticalCareService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _admission_to_dict(service.discharge_patient(admission_id, body))
    except ICUAdmissionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


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
    service: CriticalCareService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return service.get_bed_availability(icu_type)


# ---- Vital Signs ----


@router.post("/vitals", status_code=status.HTTP_201_CREATED)
async def record_vitals(
    body: dict[str, Any],
    service: CriticalCareService = Depends(_get_service),
) -> dict[str, Any]:
    return _vitals_to_dict(service.record_vitals(body))


@router.get("/vitals/{patient_id}")
async def get_vitals(
    patient_id: str,
    limit: int = Query(100, ge=1, le=1000),
    service: CriticalCareService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_vitals_to_dict(v) for v in service.get_vitals(patient_id, limit)]


# ---- Ventilator ----


@router.post("/ventilator", status_code=status.HTTP_201_CREATED)
async def set_ventilator(
    body: dict[str, Any],
    service: CriticalCareService = Depends(_get_service),
) -> dict[str, Any]:
    return _ventilator_to_dict(service.set_ventilator(body))


@router.get("/ventilator/{patient_id}")
async def get_ventilator_settings(
    patient_id: str,
    limit: int = Query(50, ge=1, le=500),
    service: CriticalCareService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_ventilator_to_dict(v) for v in service.get_ventilator_settings(patient_id, limit)]


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


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
    service: CriticalCareService = Depends(_get_service),
) -> dict[str, Any]:
    return _infusion_to_dict(service.start_infusion(body))


@router.post("/infusions/{infusion_id}/stop")
async def stop_infusion(
    infusion_id: str,
    service: CriticalCareService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _infusion_to_dict(service.stop_infusion(infusion_id))
    except InfusionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found",
        ) from e


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
    service: CriticalCareService = Depends(_get_service),
) -> dict[str, Any]:
    return _alert_to_dict(service.acknowledge_alert(alert_id, body.get("acknowledged_by", "")))


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
    service: CriticalCareService = Depends(_get_service),
) -> dict[str, Any]:
    return service.get_dashboard_stats()


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "module": "national_critical_care_platform", "version": "1.0.0"}


# ---- Serializers ----


def _admission_to_dict(a: Any) -> dict[str, Any]:
    return {
        "id": a.id,
        "patient_id": a.patient_id,
        "patient_name": getattr(a, "patient_name", ""),
        "icu_type": a.icu_type if not hasattr(a.icu_type, "value") else a.icu_type.value,
        "admission_type": getattr(a, "admission_type", ""),
        "admission_diagnosis": getattr(a, "admission_diagnosis", ""),
        "status": a.status if not hasattr(a.status, "value") else a.status.value,
        "bed_id": getattr(a, "bed_id", ""),
        "facility_id": getattr(a, "facility_id", ""),
        "created_at": getattr(a, "created_at", None),
        "discharged_at": getattr(a, "discharged_at", None),
    }


def _bed_to_dict(b: Any) -> dict[str, Any]:
    return {
        "id": b.id,
        "bed_label": b.bed_label,
        "icu_type": b.icu_type if not hasattr(b.icu_type, "value") else b.icu_type.value,
    }


def _vitals_to_dict(v: Any) -> dict[str, Any]:
    return {
        "id": v.id,
        "patient_id": v.patient_id,
        "heart_rate": v.heart_rate,
        "respiratory_rate": v.respiratory_rate,
        "systolic_bp": v.systolic_bp,
        "diastolic_bp": v.diastolic_bp,
        "temperature": v.temperature,
        "oxygen_saturation": v.oxygen_saturation,
        "gcs_total": v.gcs_total,
        "recorded_at": v.recorded_at.isoformat() if v.recorded_at else None,
    }


def _ventilator_to_dict(v: Any) -> dict[str, Any]:
    return {
        "id": v.id,
        "patient_id": v.patient_id,
        "mode": v.mode if not hasattr(v.mode, "value") else v.mode.value,
        "tidal_volume_ml": getattr(v, "tidal_volume_ml", None),
        "peep_cmh2o": getattr(v, "peep_cmh2o", None),
        "fi_o2": getattr(v, "fi_o2", None),
        "respiratory_rate_set": getattr(v, "respiratory_rate_set", None),
    }


def _ews_to_dict(e: Any) -> dict[str, Any]:
    return {
        "id": e.id,
        "patient_id": e.patient_id,
        "score_system": e.score_system,
        "score_value": e.score_value,
        "risk_category": e.risk_category,
        "recommended_frequency": e.recommended_frequency,
        "triggers_escalation": e.triggers_escalation,
    }


def _score_to_dict(s: Any) -> dict[str, Any]:
    return {
        "id": s.id,
        "patient_id": s.patient_id,
        "score_type": s.score_type,
        "score_value": s.score_value,
        "mortality_prediction": s.mortality_prediction,
    }


def _infusion_to_dict(i: Any) -> dict[str, Any]:
    return {
        "id": i.id,
        "patient_id": i.patient_id,
        "medication": i.medication,
        "rate": getattr(i, "rate", ""),
        "status": i.status,
    }


def _fluid_to_dict(f: Any) -> dict[str, Any]:
    return {
        "id": f.id,
        "patient_id": f.patient_id,
        "total_intake_ml": f.total_intake_ml,
        "total_output_ml": f.total_output_ml,
        "net_balance_ml": f.net_balance_ml,
    }


def _alert_to_dict(a: Any) -> dict[str, Any]:
    return {
        "id": a.id,
        "patient_id": a.patient_id,
        "alert_type": a.alert_type,
        "severity": a.severity if not hasattr(a.severity, "value") else a.severity.value,
        "alert_message": getattr(a, "alert_message", ""),
        "is_active": a.is_active if hasattr(a, "is_active") else True,
    }


def _round_to_dict(r: Any) -> dict[str, Any]:
    return {
        "id": r.id,
        "patient_id": r.patient_id,
        "attending_physician": getattr(r, "attending_physician", ""),
    }
