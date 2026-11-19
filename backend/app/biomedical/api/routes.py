from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.biomedical.application.service import BiomedicalService
from app.biomedical.exceptions import (
    DeviceNotFoundError,
    WorkOrderAlreadyClosedError,
    WorkOrderNotFoundError,
)
from app.database import get_db
from app.models.lab_user import LabUser
from app.security.dependencies import get_current_user, require_permission

router = APIRouter(
    prefix="/biomedical",
    tags=["National Medical Device Platform"],
    dependencies=[Depends(require_permission("system:admin"))],
)


def _get_service(db: Session = Depends(get_db)) -> BiomedicalService:
    try:
        from app.kernel import Kernel
        kernel = Kernel.get_instance()
        event_bus = kernel.event_bus if hasattr(kernel, "event_bus") else None
    except Exception:
        event_bus = None
    return BiomedicalService(db=db, event_bus=event_bus)


# ---- Device Registry ----

@router.post("/devices", status_code=status.HTTP_201_CREATED)
async def register_device(
    body: dict[str, Any],
    service: BiomedicalService = Depends(_get_service),
) -> dict[str, Any]:
    return _device_to_dict(service.register_device(body))


@router.get("/devices")
async def list_devices(
    category: str | None = Query(None),
    status: str | None = Query(None),
    facility_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: BiomedicalService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_device_to_dict(d) for d in service.list_devices(category, status, facility_id, skip, limit)]


@router.get("/devices/{device_id}")
async def get_device(
    device_id: str,
    service: BiomedicalService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _device_to_dict(service.get_device(device_id))
    except DeviceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e


@router.put("/devices/{device_id}/status")
async def update_device_status(
    device_id: str,
    body: dict[str, Any],
    service: BiomedicalService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _device_to_dict(service.update_device_status(device_id, body.get("status", ""), body.get("reason", "")))
    except DeviceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e


@router.get("/devices/due/pm")
async def devices_due_for_pm(
    days_ahead: int = Query(30, ge=1, le=365),
    service: BiomedicalService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return service.devices_due_for_pm(days_ahead)


@router.get("/devices/due/calibration")
async def devices_due_for_calibration(
    days_ahead: int = Query(30, ge=1, le=365),
    service: BiomedicalService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return service.devices_due_for_calibration(days_ahead)


# ---- Work Orders ----

@router.post("/work-orders", status_code=status.HTTP_201_CREATED)
async def create_work_order(
    body: dict[str, Any],
    service: BiomedicalService = Depends(_get_service),
) -> dict[str, Any]:
    return _work_order_to_dict(service.create_work_order(body))


@router.get("/work-orders")
async def list_work_orders(
    device_id: str | None = Query(None),
    status: str | None = Query(None),
    maintenance_type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: BiomedicalService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_work_order_to_dict(w) for w in service.list_work_orders(device_id, status, maintenance_type, skip, limit)]


@router.get("/work-orders/{wo_id}")
async def get_work_order(
    wo_id: str,
    service: BiomedicalService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _work_order_to_dict(service.get_work_order(wo_id))
    except WorkOrderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e


@router.post("/work-orders/{wo_id}/complete")
async def complete_work_order(
    wo_id: str,
    body: dict[str, Any],
    service: BiomedicalService = Depends(_get_service),
    current_user: LabUser = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        return _work_order_to_dict(
            service.complete_work_order(wo_id, body, actor_lab_id=current_user.lab_id),
        )
    except WorkOrderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e
    except WorkOrderAlreadyClosedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Work order is already closed",
        ) from e


# ---- Calibrations ----

@router.post("/calibrations", status_code=status.HTTP_201_CREATED)
async def record_calibration(
    body: dict[str, Any],
    service: BiomedicalService = Depends(_get_service),
) -> dict[str, Any]:
    return _calibration_to_dict(service.record_calibration(body))


# ---- Safety Inspections ----

@router.post("/safety-inspections", status_code=status.HTTP_201_CREATED)
async def record_safety_inspection(
    body: dict[str, Any],
    service: BiomedicalService = Depends(_get_service),
) -> dict[str, Any]:
    return _safety_to_dict(service.record_safety_inspection(body))


# ---- Incidents ----

@router.post("/incidents", status_code=status.HTTP_201_CREATED)
async def report_incident(
    body: dict[str, Any],
    service: BiomedicalService = Depends(_get_service),
) -> dict[str, Any]:
    return _incident_to_dict(service.report_incident(body))


@router.get("/incidents")
async def list_incidents(
    device_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: BiomedicalService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_incident_to_dict(i) for i in service.list_incidents(device_id, skip, limit)]


# ---- Recalls ----

@router.post("/recalls", status_code=status.HTTP_201_CREATED)
async def issue_recall(
    body: dict[str, Any],
    service: BiomedicalService = Depends(_get_service),
) -> dict[str, Any]:
    return _recall_to_dict(service.issue_recall(body))


# ---- Technicians ----

@router.post("/technicians", status_code=status.HTTP_201_CREATED)
async def register_technician(
    body: dict[str, Any],
    service: BiomedicalService = Depends(_get_service),
) -> dict[str, Any]:
    return _technician_to_dict(service.register_technician(body))


@router.get("/technicians")
async def list_technicians(
    available: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: BiomedicalService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_technician_to_dict(t) for t in service.list_technicians(available, skip, limit)]


# ---- Vendors ----

@router.post("/vendors", status_code=status.HTTP_201_CREATED)
async def register_vendor(
    body: dict[str, Any],
    service: BiomedicalService = Depends(_get_service),
) -> dict[str, Any]:
    return _vendor_to_dict(service.register_vendor(body))


# ---- Maintenance Schedule ----

@router.post("/maintenance-schedules", status_code=status.HTTP_201_CREATED)
async def create_maintenance_schedule(
    body: dict[str, Any],
    service: BiomedicalService = Depends(_get_service),
) -> dict[str, Any]:
    return _schedule_to_dict(service.create_maintenance_schedule(body))


# ---- Dashboard ----

@router.get("/dashboard")
async def get_dashboard(
    service: BiomedicalService = Depends(_get_service),
) -> dict[str, Any]:
    return service.get_dashboard_stats()


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "module": "national_medical_device_platform", "version": "1.0.0"}


# ---- Serializers ----

def _device_to_dict(d: Any) -> dict[str, Any]:
    return {
        "id": d.id, "device_name": d.device_name, "model": d.model, "manufacturer": d.manufacturer,
        "serial_number": d.serial_number, "udi_di": d.udi_di, "udi_full": d.udi_full,
        "asset_tag": d.asset_tag, "category": d.category, "risk_class": d.risk_class,
        "status": d.status, "location_facility_id": d.location_facility_id,
        "location_department": d.location_department, "location_room": d.location_room,
        "warranty_status": d.warranty_status, "lifecycle_stage": d.lifecycle_stage,
        "requires_calibration": d.requires_calibration, "next_calibration_due": d.next_calibration_due.isoformat() if d.next_calibration_due else None,
        "requires_pm": d.requires_pm, "next_pm_due": d.next_pm_due.isoformat() if d.next_pm_due else None,
        "vendor_name": d.vendor_name, "software_version": d.software_version,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


def _work_order_to_dict(w: Any) -> dict[str, Any]:
    return {
        "id": w.id, "device_id": w.device_id, "device_name": w.device_name,
        "work_order_number": w.work_order_number, "maintenance_type": w.maintenance_type,
        "priority": w.priority, "status": w.status, "title": w.title,
        "description": w.description, "reported_by": w.reported_by,
        "assigned_to": w.assigned_to, "problem_found": w.problem_found,
        "action_taken": w.action_taken, "result": w.result,
        "created_at": w.created_at.isoformat() if w.created_at else None,
    }


def _calibration_to_dict(c: Any) -> dict[str, Any]:
    return {
        "id": c.id, "device_id": c.device_id, "calibration_number": c.calibration_number,
        "status": c.status, "passed": c.passed,
        "calibration_date": c.calibration_date.isoformat() if c.calibration_date else None,
    }


def _safety_to_dict(s: Any) -> dict[str, Any]:
    return {
        "id": s.id, "device_id": s.device_id, "overall_result": s.overall_result,
        "inspection_date": s.inspection_date.isoformat() if s.inspection_date else None,
    }


def _incident_to_dict(i: Any) -> dict[str, Any]:
    return {
        "id": i.id, "device_id": i.device_id, "incident_type": i.incident_type,
        "severity": i.severity, "description": i.description, "status": i.status,
    }


def _recall_to_dict(r: Any) -> dict[str, Any]:
    return {
        "id": r.id, "device_id": r.device_id, "recall_class": r.recall_class,
        "recall_reason": r.recall_reason, "status": r.status,
    }


def _technician_to_dict(t: Any) -> dict[str, Any]:
    return {
        "id": t.id, "full_name": t.full_name, "specialization": t.specialization,
        "is_available": t.is_available,
    }


def _vendor_to_dict(v: Any) -> dict[str, Any]:
    return {"id": v.id, "vendor_name": v.vendor_name, "vendor_type": v.vendor_type}


def _schedule_to_dict(s: Any) -> dict[str, Any]:
    return {
        "id": s.id, "device_id": s.device_id, "maintenance_type": s.maintenance_type,
        "frequency_days": s.frequency_days,
        "next_due_date": s.next_due_date.isoformat() if s.next_due_date else None,
    }
