from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.public_health.application.service import PublicHealthService
from app.public_health.domain.entities import (
    DiseaseCase,
    ImmunizationAdverseEvent,
    ImmunizationFollowUpTask,
    ImmunizationRecord,
    ImmunizationSchedule,
    ColdChainReading,
    VaccineCatalog,
    VaccineLot,
    OutbreakAlert,
    PublicHealthReport,
    SurveillanceSignal,
)
from app.public_health.exceptions import (
    DiseaseCaseNotFoundError,
    ImmunizationScheduleConfigurationError,
    ImmunizationScheduleNotFoundError,
    ImmunizationStateError,
    OutbreakNotFoundError,
)
from app.security.dependencies import require_permission

router = APIRouter(
    prefix="/public-health",
    tags=["National Public Health Surveillance"],
)

ADMIN_ONLY = [Depends(require_permission("system:admin"))]


class ImmunizationScheduleDefinitionRequest(BaseModel):
    schedule_version: str = Field(min_length=1, max_length=40)
    vaccine: str = Field(min_length=1, max_length=200)
    vaccine_code: str = Field(min_length=1, max_length=40)
    dose_number: int = Field(ge=1, le=20)
    total_doses: int = Field(ge=1, le=20)
    minimum_age_days: int = Field(default=0, ge=0, le=10000)
    recommended_age_days: int = Field(ge=0, le=10000)
    grace_period_days: int = Field(default=0, ge=0, le=3650)
    route: str | None = Field(default=None, max_length=50)
    site: str | None = Field(default=None, max_length=50)
    source_reference: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class PatientScheduleRequest(BaseModel):
    patient_id: str = Field(min_length=1, max_length=100)
    health_number: str = Field(min_length=1, max_length=20)
    date_of_birth: date
    schedule_version: str = Field(min_length=1, max_length=40)
    newborn_id: str | None = Field(default=None, max_length=26)
    facility_id: str | None = Field(default=None, max_length=100)


class ScheduleAppointmentRequest(BaseModel):
    scheduled_date: datetime
    appointment_id: str | None = Field(default=None, max_length=100)
    facility_id: str | None = Field(default=None, max_length=100)


class AdministrationRequest(BaseModel):
    administration_date: datetime | None = None
    patient_name: str | None = Field(default=None, max_length=200)
    lot_number: str | None = Field(default=None, max_length=100)
    expiry_date: datetime | None = None
    route: str | None = Field(default=None, max_length=50)
    site: str | None = Field(default=None, max_length=50)
    batch_number: str | None = Field(default=None, max_length=100)
    manufacturer: str | None = Field(default=None, max_length=200)
    adverse_event: str | None = Field(default=None, max_length=2000)
    consent_obtained: bool = True
    notes: str | None = Field(default=None, max_length=2000)


class NonAdministrationRequest(BaseModel):
    reason: str = Field(pattern="^(refused|contraindicated|stockout|absent|transferred|other)$")
    notes: str | None = Field(default=None, max_length=2000)
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    next_follow_up_date: datetime | None = None


class AEFIRequest(BaseModel):
    onset_at: datetime | None = None
    severity: str = Field(default="unknown", pattern="^(unknown|mild|moderate|severe|critical)$")
    symptoms: list[str] = Field(default_factory=list, max_length=50)
    treatment: str | None = Field(default=None, max_length=4000)
    outcome: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=4000)


class FollowUpCompletionRequest(BaseModel):
    status: str = Field(pattern="^(completed|suppressed)$")


class VaccineCatalogRequest(BaseModel):
    vaccine_code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=200)
    name_ar: str | None = Field(default=None, max_length=200)
    unit: str = Field(default="dose", max_length=24)
    manufacturer: str | None = Field(default=None, max_length=200)
    storage_min_c: float | None = None
    storage_max_c: float | None = None
    source_reference: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class VaccineLotRequest(BaseModel):
    lot_number: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0, le=10_000_000)
    expiry_date: datetime
    storage_equipment_id: str | None = Field(default=None, max_length=100)
    reference_id: str | None = Field(default=None, max_length=100)
    reason: str | None = Field(default=None, max_length=200)


class ColdChainReadingRequest(BaseModel):
    equipment_id: str = Field(min_length=1, max_length=100)
    reading_at: datetime | None = None
    temperature_c: float = Field(ge=-100, le=100)
    minimum_allowed_c: float | None = Field(default=None, ge=-100, le=100)
    maximum_allowed_c: float | None = Field(default=None, ge=-100, le=100)
    source: str = Field(default="manual", max_length=24)
    notes: str | None = Field(default=None, max_length=2000)


class InventoryConsumptionRequest(BaseModel):
    lot_id: str = Field(min_length=1, max_length=26)
    quantity: int = Field(default=1, ge=1, le=1)
    idempotency_key: str = Field(min_length=8, max_length=160)


class InventoryWastageRequest(BaseModel):
    quantity: int = Field(gt=0, le=10_000_000)
    reason: str = Field(min_length=1, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=160)
    reference_id: str | None = Field(default=None, max_length=100)


class InventoryAdjustmentRequest(BaseModel):
    delta: int = Field(ge=-10_000_000, le=10_000_000)
    reason: str = Field(min_length=1, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=160)
    reference_id: str | None = Field(default=None, max_length=100)


def _tenant_id(current_user: Any) -> int:
    lab_id = getattr(current_user, "lab_id", None)
    if not isinstance(lab_id, int) or lab_id <= 0:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Facility context is required")
    return lab_id


def _get_service(db: Session = Depends(get_db)) -> PublicHealthService:
    try:
        from app.kernel import Kernel
        kernel = Kernel.get_instance()
        event_bus = kernel.event_bus if hasattr(kernel, "event_bus") else None
    except Exception:
        event_bus = None
    return PublicHealthService(db=db, event_bus=event_bus)


# ── Disease Cases ──

@router.post("/disease-cases", status_code=status.HTTP_201_CREATED, dependencies=ADMIN_ONLY)
async def report_case(
    body: dict[str, Any],
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    return _case_to_dict(service.report_case(body))


@router.get("/disease-cases", dependencies=ADMIN_ONLY)
async def list_cases(
    disease_code: str | None = Query(None),
    region: str | None = Query(None),
    confirmed: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: PublicHealthService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_case_to_dict(c) for c in service.list_cases(disease_code, region, confirmed, skip, limit)]


@router.get("/disease-cases/{case_id}", dependencies=ADMIN_ONLY)
async def get_case(
    case_id: str,
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _case_to_dict(service.get_case(case_id))
    except DiseaseCaseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e


@router.get("/disease-cases/stats", dependencies=ADMIN_ONLY)
async def get_case_stats(
    region: str | None = Query(None),
    days: int = Query(30, ge=1, le=365),
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    return service.get_case_stats(region, days)


# ── Outbreak Alerts ──

@router.post("/outbreak-alerts", status_code=status.HTTP_201_CREATED, dependencies=ADMIN_ONLY)
async def raise_alert(
    body: dict[str, Any],
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    return _alert_to_dict(service.raise_alert(body))


@router.get("/outbreak-alerts", dependencies=ADMIN_ONLY)
async def list_alerts(
    status: str | None = Query(None),
    alert_level: str | None = Query(None),
    region: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: PublicHealthService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_alert_to_dict(a) for a in service.list_alerts(status, alert_level, region, skip, limit)]


@router.get("/outbreak-alerts/{alert_id}", dependencies=ADMIN_ONLY)
async def get_alert(
    alert_id: str,
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _alert_to_dict(service.get_alert(alert_id))
    except OutbreakNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e


@router.put("/outbreak-alerts/{alert_id}/status", dependencies=ADMIN_ONLY)
async def update_alert_status(
    alert_id: str,
    body: dict[str, Any],
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return _alert_to_dict(service.update_alert_status(alert_id, body.get("status", ""), body.get("notes", "")))
    except OutbreakNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found") from e


# ── Surveillance Signals ──

@router.post("/surveillance-signals", status_code=status.HTTP_201_CREATED, dependencies=ADMIN_ONLY)
async def record_signal(
    body: dict[str, Any],
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    return _signal_to_dict(service.record_signal(body))


@router.get("/surveillance-signals", dependencies=ADMIN_ONLY)
async def list_signals(
    alert_level: str | None = Query(None),
    region: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: PublicHealthService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_signal_to_dict(s) for s in service.list_signals(alert_level, region, skip, limit)]


# ── AI Fabric Integration ──

@router.post("/analyze", dependencies=ADMIN_ONLY)
async def analyze_surveillance(
    body: dict[str, Any],
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    return service.analyze_surveillance(
        body.get("disease", ""),
        body.get("region", ""),
        body.get("case_count", 0),
        body.get("expected_daily", 0),
    )


@router.post("/detect-outbreak", dependencies=ADMIN_ONLY)
async def detect_outbreak_cluster(
    body: dict[str, Any],
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    return service.detect_outbreak_cluster(
        body.get("disease", ""),
        body.get("region", ""),
        body.get("cases", []),
    )


# ── Immunization ──

@router.post("/vaccinations", status_code=status.HTTP_201_CREATED)
async def record_vaccination(
    body: dict[str, Any],
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("immunization:administer")),
) -> dict[str, Any]:
    return _immunization_to_dict(service.record_vaccination(body, _tenant_id(current_user)))


@router.get("/vaccinations")
async def list_vaccinations(
    patient_id: str | None = Query(None),
    vaccine: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("immunization:read")),
) -> list[dict[str, Any]]:
    return [_immunization_to_dict(v) for v in service.list_vaccinations(
        patient_id, vaccine, skip, limit, _tenant_id(current_user)
    )]


@router.get("/vaccinations/coverage")
async def vaccination_coverage(
    vaccine: str | None = Query(None),
    region: str | None = Query(None),
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("immunization:report")),
) -> dict[str, Any]:
    return service.get_vaccination_coverage(vaccine, region, _tenant_id(current_user))


@router.post("/vaccinations/schedule-definitions", status_code=status.HTTP_201_CREATED)
async def configure_immunization_schedule(
    body: ImmunizationScheduleDefinitionRequest,
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("system:admin")),
) -> dict[str, Any]:
    try:
        return service.configure_immunization_schedule(
            body.model_dump(), _tenant_id(current_user), str(getattr(current_user, "id", ""))
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid schedule definition") from e


@router.post("/vaccinations/schedule", status_code=status.HTTP_201_CREATED)
async def generate_patient_schedule(
    body: PatientScheduleRequest,
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("immunization:schedule")),
) -> list[dict[str, Any]]:
    try:
        schedules = service.generate_patient_immunization_schedule(
            patient_id=body.patient_id,
            health_number=body.health_number,
            date_of_birth=body.date_of_birth,
            lab_id=_tenant_id(current_user),
            schedule_version=body.schedule_version,
            newborn_id=body.newborn_id,
            facility_id=body.facility_id,
        )
        return [_schedule_to_dict(item) for item in schedules]
    except ImmunizationScheduleConfigurationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No approved schedule version is available") from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid schedule request") from e


@router.get("/vaccinations/{patient_id}/schedule")
async def get_patient_schedule(
    patient_id: str,
    include_closed: bool = Query(True),
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("immunization:read")),
) -> list[dict[str, Any]]:
    schedules = service.get_patient_immunization_schedule(
        patient_id, _tenant_id(current_user), include_closed
    )
    return [_schedule_to_dict(item) for item in schedules]


@router.get("/vaccinations/overdue")
async def get_overdue_vaccinations(
    patient_id: str | None = Query(None),
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("immunization:read")),
) -> list[dict[str, Any]]:
    schedules = service.get_overdue_vaccinations(_tenant_id(current_user), patient_id)
    return [_schedule_to_dict(item) for item in schedules]


@router.post("/vaccinations/schedule/{schedule_id}/appointment")
async def schedule_appointment(
    schedule_id: str,
    body: ScheduleAppointmentRequest,
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("immunization:schedule")),
) -> dict[str, Any]:
    try:
        schedule = service.schedule_immunization(
            schedule_id, _tenant_id(current_user), body.scheduled_date, body.appointment_id, body.facility_id
        )
        return _schedule_to_dict(schedule)
    except ImmunizationScheduleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule entry not found") from e
    except (ImmunizationStateError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Schedule entry cannot be updated") from e


@router.post("/vaccinations/schedule/{schedule_id}/administer", status_code=status.HTTP_201_CREATED)
async def administer_scheduled_vaccine(
    schedule_id: str,
    body: AdministrationRequest,
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("immunization:administer")),
) -> dict[str, Any]:
    try:
        record = service.mark_administered(
            schedule_id,
            body.model_dump(),
            _tenant_id(current_user),
            str(getattr(current_user, "id", "")),
        )
        return _immunization_to_dict(record)
    except ImmunizationScheduleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule entry not found") from e
    except (ImmunizationStateError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vaccine administration cannot be recorded") from e


@router.post("/vaccinations/schedule/{schedule_id}/reminder")
async def queue_immunization_reminder(
    schedule_id: str,
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("immunization:schedule")),
) -> dict[str, Any]:
    try:
        return _schedule_to_dict(service.send_reminder(schedule_id, _tenant_id(current_user)))
    except ImmunizationScheduleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule entry not found") from e
    except ImmunizationStateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Reminder cannot be queued") from e


@router.post("/vaccinations/schedule/{schedule_id}/not-administered")
async def record_non_administration(
    schedule_id: str,
    body: NonAdministrationRequest,
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("immunization:administer")),
) -> dict[str, Any]:
    try:
        schedule = service.record_non_administration(
            schedule_id, body.model_dump(), _tenant_id(current_user), str(getattr(current_user, "id", ""))
        )
        return _schedule_to_dict(schedule)
    except ImmunizationScheduleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule entry not found") from e
    except (ImmunizationStateError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Non-administration cannot be recorded") from e


@router.get("/vaccinations/follow-up/tasks")
async def list_immunization_follow_up_tasks(
    task_status: str | None = Query(None, alias="status", pattern="^(pending|queued|completed|suppressed)$"),
    limit: int = Query(100, ge=1, le=500),
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("immunization:read")),
) -> list[dict[str, Any]]:
    return [_follow_up_to_dict(task) for task in service.list_follow_up_tasks(_tenant_id(current_user), task_status, limit)]


@router.patch("/vaccinations/follow-up/tasks/{task_id}")
async def complete_immunization_follow_up_task(
    task_id: str,
    body: FollowUpCompletionRequest,
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("immunization:write")),
) -> dict[str, Any]:
    try:
        task = service.complete_follow_up_task(task_id, _tenant_id(current_user), str(getattr(current_user, "id", "")), body.status)
        return _follow_up_to_dict(task)
    except ImmunizationScheduleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up task not found") from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid follow-up state") from e


@router.post("/vaccinations/records/{record_id}/aefi", status_code=status.HTTP_201_CREATED)
async def report_immunization_aefi(
    record_id: str,
    body: AEFIRequest,
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("immunization:report")),
) -> dict[str, Any]:
    try:
        event = service.report_adverse_event(record_id, body.model_dump(), _tenant_id(current_user), str(getattr(current_user, "id", "")))
        return _aefi_to_dict(event)
    except ImmunizationScheduleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vaccination record not found") from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid adverse event") from e


@router.post("/vaccinations/inventory/catalog", status_code=status.HTTP_201_CREATED)
async def register_vaccine_catalog(
    body: VaccineCatalogRequest,
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("vaccine_inventory:manage")),
) -> dict[str, Any]:
    try:
        return _vaccine_catalog_to_dict(service.register_vaccine_catalog(body.model_dump(), _tenant_id(current_user)))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vaccine catalog entry cannot be created") from e


@router.post("/vaccinations/inventory/catalog/{catalog_id}/lots", status_code=status.HTTP_201_CREATED)
async def receive_vaccine_lot(
    catalog_id: str,
    body: VaccineLotRequest,
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("vaccine_inventory:manage")),
) -> dict[str, Any]:
    try:
        lot = service.receive_vaccine_lot(catalog_id, body.model_dump(), _tenant_id(current_user), str(getattr(current_user, "id", "")))
        return _vaccine_lot_to_dict(lot)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vaccine lot cannot be received") from e


@router.get("/vaccinations/inventory")
async def list_vaccine_inventory(
    vaccine_code: str | None = Query(None, max_length=40),
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("vaccine_inventory:read")),
) -> list[dict[str, Any]]:
    return [_vaccine_lot_to_dict(lot) for lot in service.list_vaccine_inventory(_tenant_id(current_user), vaccine_code)]


@router.post("/vaccinations/inventory/cold-chain/readings", status_code=status.HTTP_201_CREATED)
async def record_cold_chain_reading(
    body: ColdChainReadingRequest,
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("vaccine_inventory:manage")),
) -> dict[str, Any]:
    try:
        return _cold_chain_to_dict(service.record_cold_chain_reading(body.model_dump(), _tenant_id(current_user), str(getattr(current_user, "id", ""))))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cold-chain reading") from e


@router.post("/vaccinations/records/{record_id}/inventory-consumption")
async def consume_inventory_for_vaccination(
    record_id: str,
    body: InventoryConsumptionRequest,
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("vaccine_inventory:dispense")),
) -> dict[str, Any]:
    try:
        return service.consume_vaccine_for_administration(
            record_id, body.lot_id, body.quantity, _tenant_id(current_user),
            str(getattr(current_user, "id", "")), body.idempotency_key,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vaccine inventory cannot be consumed") from e


@router.post("/vaccinations/inventory/lots/{lot_id}/wastage")
async def record_vaccine_wastage(
    lot_id: str,
    body: InventoryWastageRequest,
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("vaccine_inventory:manage")),
) -> dict[str, Any]:
    try:
        return service.record_vaccine_wastage(lot_id, body.model_dump(), _tenant_id(current_user), str(getattr(current_user, "id", "")))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vaccine wastage cannot be recorded") from e


@router.post("/vaccinations/inventory/lots/{lot_id}/adjustment")
async def adjust_vaccine_lot(
    lot_id: str,
    body: InventoryAdjustmentRequest,
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("vaccine_inventory:manage")),
) -> dict[str, Any]:
    try:
        return service.adjust_vaccine_lot(lot_id, body.model_dump(), _tenant_id(current_user), str(getattr(current_user, "id", "")))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vaccine stock adjustment cannot be recorded") from e


@router.get("/vaccinations/inventory/report")
async def vaccine_inventory_report(
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("vaccine_inventory:report")),
) -> dict[str, Any]:
    return service.get_vaccine_inventory_report(_tenant_id(current_user))


@router.get("/vaccinations/statistics/monthly")
async def monthly_immunization_statistics(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    service: PublicHealthService = Depends(_get_service),
    current_user: Any = Depends(require_permission("immunization:report")),
) -> dict[str, Any]:
    return service.get_monthly_immunization_statistics(_tenant_id(current_user), year, month)


# ── Reports ──

@router.post("/reports", status_code=status.HTTP_201_CREATED, dependencies=ADMIN_ONLY)
async def publish_report(
    body: dict[str, Any],
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    return _report_to_dict(service.publish_report(body))


@router.get("/reports", dependencies=ADMIN_ONLY)
async def list_reports(
    report_type: str | None = Query(None),
    region: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: PublicHealthService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return [_report_to_dict(r) for r in service.list_reports(report_type, region, skip, limit)]


# ── Dashboard ──

@router.get("/dashboard", dependencies=ADMIN_ONLY)
async def get_dashboard(
    region: str | None = Query(None),
    service: PublicHealthService = Depends(_get_service),
) -> dict[str, Any]:
    return service.get_dashboard(region)


@router.get("/health", dependencies=ADMIN_ONLY)
async def health() -> dict[str, Any]:
    return {"status": "ok", "module": "national_public_health_surveillance", "version": "1.0.0"}


# ── Serializers ──

def _case_to_dict(c: DiseaseCase) -> dict[str, Any]:
    return {"id": c.id, "disease_code": c.disease_code, "disease_name": c.disease_name,
            "region": c.region, "is_confirmed": c.is_confirmed, "source": c.source,
            "reported_by": c.reported_by, "reported_at": c.reported_at}


def _alert_to_dict(a: OutbreakAlert) -> dict[str, Any]:
    return {"id": a.id, "disease": a.disease, "region": a.region,
            "confirmed_cases": a.confirmed_cases, "alert_level": a.alert_level,
            "status": a.status, "recommendations": a.recommendations}


def _signal_to_dict(s: SurveillanceSignal) -> dict[str, Any]:
    return {"id": s.id, "disease": s.disease, "region": s.region,
            "case_count": s.case_count, "z_score": s.z_score,
            "alert_level": s.alert_level, "recommendation": s.recommendation}


def _immunization_to_dict(v: ImmunizationRecord) -> dict[str, Any]:
    return {"id": v.id, "patient_id": v.patient_id, "patient_name": v.patient_name,
            "health_number": v.health_number, "newborn_id": v.newborn_id,
            "schedule_id": v.schedule_id, "vaccine": v.vaccine,
            "vaccine_code": v.vaccine_code, "dose_number": v.dose_number,
            "total_doses": v.total_doses, "due_date": v.due_date,
            "scheduled_date": v.scheduled_date, "status": v.status,
            "appointment_id": v.appointment_id, "administration_date": v.administration_date,
            "administered_by": v.administered_by, "facility_id": v.facility_id,
            "lot_number": v.lot_number, "batch_number": v.batch_number,
            "manufacturer": v.manufacturer, "adverse_event": v.adverse_event}


def _schedule_to_dict(schedule: ImmunizationSchedule) -> dict[str, Any]:
    return {
        "id": schedule.id,
        "patient_id": schedule.patient_id,
        "health_number": schedule.health_number,
        "newborn_id": schedule.newborn_id,
        "schedule_definition_id": schedule.schedule_definition_id,
        "schedule_version": schedule.schedule_version,
        "vaccine": schedule.vaccine,
        "vaccine_code": schedule.vaccine_code,
        "dose_number": schedule.dose_number,
        "total_doses": schedule.total_doses,
        "due_date": schedule.due_date,
        "scheduled_date": schedule.scheduled_date,
        "status": schedule.status,
        "facility_id": schedule.facility_id,
        "appointment_id": schedule.appointment_id,
        "reminder_sent": schedule.reminder_sent,
        "reminder_sent_at": schedule.reminder_sent_at,
        "reminder_count": schedule.reminder_count,
        "contraindication_reason": schedule.contraindication_reason,
        "refusal_reason": schedule.refusal_reason,
                "notes": schedule.notes,
        "follow_up_status": schedule.follow_up_status,
        "follow_up_priority": schedule.follow_up_priority,
        "next_follow_up_date": schedule.next_follow_up_date,
        "non_administration_reason": schedule.non_administration_reason,
        "non_administration_notes": schedule.non_administration_notes,
    }


def _follow_up_to_dict(task: ImmunizationFollowUpTask) -> dict[str, Any]:
    return {
        "id": task.id, "schedule_id": task.schedule_id, "patient_id": task.patient_id,
        "health_number": task.health_number, "vaccine": task.vaccine, "due_date": task.due_date,
        "status": task.status, "priority": task.priority, "reason": task.reason,
        "next_action_at": task.next_action_at, "consent_verified": task.consent_verified,
        "preferred_channel": task.preferred_channel, "last_attempt_at": task.last_attempt_at,
        "completed_at": task.completed_at, "completed_by": task.completed_by, "notes": task.notes,
    }


def _aefi_to_dict(event: ImmunizationAdverseEvent) -> dict[str, Any]:
    return {
        "id": event.id, "record_id": event.record_id, "schedule_id": event.schedule_id,
        "patient_id": event.patient_id, "health_number": event.health_number, "vaccine": event.vaccine,
        "onset_at": event.onset_at, "severity": event.severity, "symptoms": event.symptoms,
        "treatment": event.treatment, "outcome": event.outcome, "investigation_status": event.investigation_status,
        "reported_by": event.reported_by, "reported_at": event.reported_at, "notes": event.notes,
    }


def _vaccine_catalog_to_dict(catalog: VaccineCatalog) -> dict[str, Any]:
    return {
        "id": catalog.id, "vaccine_code": catalog.vaccine_code, "name": catalog.name,
        "name_ar": catalog.name_ar, "unit": catalog.unit, "manufacturer": catalog.manufacturer,
        "storage_min_c": catalog.storage_min_c, "storage_max_c": catalog.storage_max_c,
        "source_reference": catalog.source_reference, "is_active": catalog.is_active,
    }


def _vaccine_lot_to_dict(lot: VaccineLot) -> dict[str, Any]:
    return {
        "id": lot.id, "catalog_id": lot.catalog_id, "lot_number": lot.lot_number,
        "expiry_date": lot.expiry_date, "received_at": lot.received_at,
        "received_quantity": lot.received_quantity, "available_quantity": lot.available_quantity,
        "quarantined": lot.quarantined, "quarantine_reason": lot.quarantine_reason,
        "storage_equipment_id": lot.storage_equipment_id,
    }


def _cold_chain_to_dict(reading: ColdChainReading) -> dict[str, Any]:
    return {
        "id": reading.id, "equipment_id": reading.equipment_id, "reading_at": reading.reading_at,
        "temperature_c": reading.temperature_c, "minimum_allowed_c": reading.minimum_allowed_c,
        "maximum_allowed_c": reading.maximum_allowed_c, "status": reading.status,
        "source": reading.source, "recorded_by": reading.recorded_by,
        "alert_acknowledged": reading.alert_acknowledged, "notes": reading.notes,
    }


def _report_to_dict(r: PublicHealthReport) -> dict[str, Any]:
    return {"id": r.id, "report_type": r.report_type, "region": r.region,
            "total_cases": r.total_cases, "total_deaths": r.total_deaths,
            "key_findings": r.key_findings, "published_by": r.published_by}
