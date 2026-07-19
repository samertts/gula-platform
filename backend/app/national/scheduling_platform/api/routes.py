from __future__ import annotations

from datetime import date, datetime, time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.national.scheduling_platform.application.service import SchedulingPlatformService
from app.national.scheduling_platform.domain.enums import (
    AppointmentStatus,
    RecurrencePattern,
    ResourceType,
)
from app.national.scheduling_platform.exceptions import (
    AppointmentNotFoundError,
    CalendarNotFoundError,
    ConflictDetectionError,
    ResourceNotFoundError,
    ScheduleNotFoundError,
    WaitingListNotFoundError,
)
from app.national.scheduling_platform.infrastructure.repository import (
    SQLAlchemyAppointmentReminderRepository,
    SQLAlchemyAppointmentRepository,
    SQLAlchemyCalendarRepository,
    SQLAlchemyResourceRepository,
    SQLAlchemyScheduleRepository,
    SQLAlchemyTimeSlotRepository,
    SQLAlchemyWaitingListRepository,
)

router = APIRouter(prefix="/national/scheduling", tags=["National Scheduling Platform"])


def _get_service(db: Session = Depends(get_db)) -> SchedulingPlatformService:
    from app.kernel import Kernel
    from app.kernel.event_bus.bus import EventBus

    kernel = Kernel.get_instance()
    event_bus = kernel.event_bus if hasattr(kernel, "event_bus") else EventBus(kernel)
    return SchedulingPlatformService(
        appointment_repository=SQLAlchemyAppointmentRepository(db),
        resource_repository=SQLAlchemyResourceRepository(db),
        schedule_repository=SQLAlchemyScheduleRepository(db),
        time_slot_repository=SQLAlchemyTimeSlotRepository(db),
        waiting_list_repository=SQLAlchemyWaitingListRepository(db),
        calendar_repository=SQLAlchemyCalendarRepository(db),
        reminder_repository=SQLAlchemyAppointmentReminderRepository(db),
        event_bus=event_bus,
    )


@router.post("/appointments", status_code=status.HTTP_201_CREATED)
async def create_appointment(
    body: dict[str, Any],
    service: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        appointment = await service.create_appointment(
            patient_id=body.get("patient_id", ""),
            practitioner_id=body.get("practitioner_id", ""),
            facility_id=body.get("facility_id", ""),
            resource_id=body.get("resource_id", ""),
            title=body.get("title", ""),
            description=body.get("description", ""),
            start_at=datetime.fromisoformat(body["start_at"]) if body.get("start_at") else None,
            end_at=datetime.fromisoformat(body["end_at"]) if body.get("end_at") else None,
            appointment_type=body.get("appointment_type", ""),
            recurrence_pattern=RecurrencePattern(body.get("recurrence_pattern", "none")),
            recurrence_end=datetime.fromisoformat(body["recurrence_end"]) if body.get("recurrence_end") else None,
            reminder_enabled=body.get("reminder_enabled", True),
            reminder_minutes_before=body.get("reminder_minutes_before", 60),
            notes=body.get("notes", ""),
            metadata=body.get("metadata"),
            created_by=body.get("created_by", ""),
        )
        return _appointment_to_dict(appointment)
    except ConflictDetectionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get("/appointments")
async def list_appointments(
    patient_id: str | None = Query(None),
    practitioner_id: str | None = Query(None),
    status: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: SchedulingPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    appointments = await service.list_appointments(
        patient_id=patient_id,
        practitioner_id=practitioner_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )
    return [_appointment_to_dict(a) for a in appointments]


@router.get("/appointments/{appointment_id}")
async def get_appointment(
    appointment_id: str,
    service: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        appointment = await service.get_appointment(appointment_id)
        return _appointment_to_dict(appointment)
    except AppointmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.put("/appointments/{appointment_id}")
async def update_appointment(
    appointment_id: str,
    body: dict[str, Any],
    service: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        if body.get("start_at") and body.get("end_at"):
            appointment = await service.reschedule_appointment(
                appointment_id=appointment_id,
                new_start=datetime.fromisoformat(body["start_at"]),
                new_end=datetime.fromisoformat(body["end_at"]),
                reason=body.get("reason", ""),
            )
        elif body.get("status"):
            appointment = await service.update_appointment_status(
                appointment_id=appointment_id,
                new_status=AppointmentStatus(body["status"]),
            )
        else:
            appointment = await service.get_appointment(appointment_id)
        return _appointment_to_dict(appointment)
    except AppointmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ConflictDetectionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete("/appointments/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_appointment(
    appointment_id: str,
    body: dict[str, Any] | None = None,
    service: SchedulingPlatformService = Depends(_get_service),
) -> None:
    if body is None:
        body = {}
    try:
        await service.cancel_appointment(appointment_id, reason=body.get("reason", ""))
    except AppointmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ConflictDetectionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.post("/appointments/{appointment_id}/complete")
async def complete_appointment(
    appointment_id: str,
    service: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        appointment = await service.complete_appointment(appointment_id)
        return _appointment_to_dict(appointment)
    except AppointmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ConflictDetectionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.post("/appointments/{appointment_id}/no-show")
async def mark_no_show(
    appointment_id: str,
    service: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        appointment = await service.mark_no_show(appointment_id)
        return _appointment_to_dict(appointment)
    except AppointmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ConflictDetectionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.post("/appointments/{appointment_id}/reschedule")
async def reschedule_appointment(
    appointment_id: str,
    body: dict[str, Any],
    service: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        appointment = await service.reschedule_appointment(
            appointment_id=appointment_id,
            new_start=datetime.fromisoformat(body["start_at"]),
            new_end=datetime.fromisoformat(body["end_at"]),
            reason=body.get("reason", ""),
        )
        return _appointment_to_dict(appointment)
    except AppointmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ConflictDetectionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.post("/availability/check")
async def check_availability(
    body: dict[str, Any],
    service: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return await service.check_availability(
            resource_id=body.get("resource_id", ""),
            start_at=datetime.fromisoformat(body["start_at"]),
            end_at=datetime.fromisoformat(body["end_at"]),
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/availability/slots")
async def find_available_slots(
    resource_id: str = Query(...),
    date_from: str = Query(...),
    date_to: str = Query(...),
    service: SchedulingPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    return await service.find_available_slots(
        resource_id=resource_id,
        date_from=datetime.fromisoformat(date_from),
        date_to=datetime.fromisoformat(date_to),
    )


@router.post("/resources", status_code=status.HTTP_201_CREATED)
async def create_resource(
    body: dict[str, Any],
    service: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    resource = await service.create_resource(
        name=body.get("name", ""),
        type=ResourceType(body.get("type", "room")),
        description=body.get("description", ""),
        capacity=body.get("capacity", 1),
        location=body.get("location", ""),
        calendar_id=body.get("calendar_id", ""),
        metadata=body.get("metadata"),
    )
    return _resource_to_dict(resource)


@router.get("/resources")
async def list_resources(
    type: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: SchedulingPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    resources = await service.list_resources(type=type, skip=skip, limit=limit)
    return [_resource_to_dict(r) for r in resources]


@router.get("/resources/{resource_id}")
async def get_resource(
    resource_id: str,
    service: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        resource = await service.get_resource(resource_id)
        return _resource_to_dict(resource)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.put("/resources/{resource_id}")
async def update_resource(
    resource_id: str,
    body: dict[str, Any],
    service: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        resource = await service.update_resource(resource_id, body)
        return _resource_to_dict(resource)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/resources/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_resource(
    resource_id: str,
    service: SchedulingPlatformService = Depends(_get_service),
) -> None:
    try:
        await service.deactivate_resource(resource_id)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/schedules")
async def set_availability(
    body: dict[str, Any],
    service: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        schedule = await service.set_availability(
            resource_id=body.get("resource_id", ""),
            date=date.fromisoformat(body["date"]),
            start_time=time.fromisoformat(body["start_time"]),
            end_time=time.fromisoformat(body["end_time"]),
            slot_duration_minutes=body.get("slot_duration_minutes", 30),
            is_available=body.get("is_available", True),
        )
        return _schedule_to_dict(schedule)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/schedules/block")
async def block_time(
    body: dict[str, Any],
    service: SchedulingPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    try:
        slots = await service.block_time(
            resource_id=body.get("resource_id", ""),
            start_at=datetime.fromisoformat(body["start_at"]),
            end_at=datetime.fromisoformat(body["end_at"]),
            purpose=body.get("purpose", ""),
        )
        return [_slot_to_dict(s) for s in slots]
    except ScheduleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/schedules/{resource_id}/{date}")
async def get_schedule(
    resource_id: str,
    date: str,
    service: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        return await service.get_schedule(
            resource_id=resource_id,
            date=date.fromisoformat(date),
        )
    except ScheduleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/waiting-list", status_code=status.HTTP_201_CREATED)
async def add_to_waiting_list(
    body: dict[str, Any],
    service: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    entry = await service.add_to_waiting_list(
        patient_id=body.get("patient_id", ""),
        resource_id=body.get("resource_id", ""),
        preferred_date_from=date.fromisoformat(body["preferred_date_from"]) if body.get("preferred_date_from") else None,
        preferred_date_to=date.fromisoformat(body["preferred_date_to"]) if body.get("preferred_date_to") else None,
        preferred_time_from=time.fromisoformat(body["preferred_time_from"]) if body.get("preferred_time_from") else None,
        preferred_time_to=time.fromisoformat(body["preferred_time_to"]) if body.get("preferred_time_to") else None,
        priority=body.get("priority", 0),
        notes=body.get("notes", ""),
    )
    return _waiting_list_to_dict(entry)


@router.get("/waiting-list")
async def list_waiting_list(
    resource_id: str | None = Query(None),
    status: str = Query("active"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: SchedulingPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    entries = await service.list_waiting_list(
        resource_id=resource_id,
        status=status,
        skip=skip,
        limit=limit,
    )
    return [_waiting_list_to_dict(e) for e in entries]


@router.delete("/waiting-list/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_waiting_list(
    entry_id: str,
    service: SchedulingPlatformService = Depends(_get_service),
) -> None:
    try:
        await service.remove_from_waiting_list(entry_id)
    except WaitingListNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/waiting-list/{entry_id}/fulfill")
async def fulfill_waiting_list(
    entry_id: str,
    body: dict[str, Any],
    service: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        entry = await service.fulfill_waiting_list(
            entry_id=entry_id,
            appointment_id=body.get("appointment_id", ""),
        )
        return _waiting_list_to_dict(entry)
    except (WaitingListNotFoundError, AppointmentNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/reminders/send")
async def send_reminders(
    service: SchedulingPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    reminders = await service.send_reminders()
    return [_reminder_to_dict(r) for r in reminders]


@router.post("/calendars", status_code=status.HTTP_201_CREATED)
async def create_calendar(
    body: dict[str, Any],
    service: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    calendar = await service.create_calendar(
        name=body.get("name", ""),
        description=body.get("description", ""),
        timezone=body.get("timezone", "UTC"),
        business_hours=body.get("business_hours"),
        holidays=body.get("holidays"),
    )
    return _calendar_to_dict(calendar)


@router.get("/calendars")
async def list_calendars(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: SchedulingPlatformService = Depends(_get_service),
) -> list[dict[str, Any]]:
    calendars = await service.list_calendars(skip=skip, limit=limit)
    return [_calendar_to_dict(c) for c in calendars]


@router.get("/calendars/{calendar_id}")
async def get_calendar(
    calendar_id: str,
    service: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    try:
        calendar = await service.get_calendar(calendar_id)
        return _calendar_to_dict(calendar)
    except CalendarNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/stats")
async def get_dashboard_stats(
    service: SchedulingPlatformService = Depends(_get_service),
) -> dict[str, Any]:
    return await service.get_dashboard_stats()


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "module": "national_scheduling_platform", "version": "1.0.0"}


def _appointment_to_dict(a: Any) -> dict[str, Any]:
    return {
        "id": a.id,
        "patient_id": a.patient_id,
        "practitioner_id": a.practitioner_id,
        "facility_id": a.facility_id,
        "resource_id": a.resource_id,
        "title": a.title,
        "description": a.description,
        "start_at": a.start_at.isoformat() if a.start_at else None,
        "end_at": a.end_at.isoformat() if a.end_at else None,
        "status": a.status.value,
        "appointment_type": a.appointment_type,
        "recurrence_pattern": a.recurrence_pattern.value,
        "reminder_enabled": a.reminder_enabled,
        "reminder_minutes_before": a.reminder_minutes_before,
        "notes": a.notes,
        "metadata": a.metadata,
        "created_by": a.created_by,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        "version": a.version,
    }


def _resource_to_dict(r: Any) -> dict[str, Any]:
    return {
        "id": r.id,
        "name": r.name,
        "type": r.type.value,
        "description": r.description,
        "capacity": r.capacity,
        "location": r.location,
        "is_active": r.is_active,
        "calendar_id": r.calendar_id,
        "metadata": r.metadata,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


def _schedule_to_dict(s: Any) -> dict[str, Any]:
    return {
        "id": s.id,
        "resource_id": s.resource_id,
        "date": s.date.isoformat() if s.date else None,
        "start_time": s.start_time.isoformat() if s.start_time else None,
        "end_time": s.end_time.isoformat() if s.end_time else None,
        "is_available": s.is_available,
        "slot_duration_minutes": s.slot_duration_minutes,
    }


def _slot_to_dict(s: Any) -> dict[str, Any]:
    return {
        "id": s.id,
        "schedule_id": s.schedule_id,
        "start_at": s.start_at.isoformat() if s.start_at else None,
        "end_at": s.end_at.isoformat() if s.end_at else None,
        "status": s.status.value,
        "booked_by": s.booked_by,
        "purpose": s.purpose,
    }


def _waiting_list_to_dict(e: Any) -> dict[str, Any]:
    return {
        "id": e.id,
        "patient_id": e.patient_id,
        "resource_id": e.resource_id,
        "preferred_date_from": e.preferred_date_from.isoformat() if e.preferred_date_from else None,
        "preferred_date_to": e.preferred_date_to.isoformat() if e.preferred_date_to else None,
        "preferred_time_from": e.preferred_time_from.isoformat() if e.preferred_time_from else None,
        "preferred_time_to": e.preferred_time_to.isoformat() if e.preferred_time_to else None,
        "priority": e.priority,
        "status": e.status,
        "notes": e.notes,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


def _reminder_to_dict(r: Any) -> dict[str, Any]:
    return {
        "id": r.id,
        "appointment_id": r.appointment_id,
        "channel": r.channel,
        "sent_at": r.sent_at.isoformat() if r.sent_at else None,
        "status": r.status,
        "error": r.error,
    }


def _calendar_to_dict(c: Any) -> dict[str, Any]:
    return {
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "timezone": c.timezone,
        "business_hours": c.business_hours,
        "holidays": c.holidays,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }
