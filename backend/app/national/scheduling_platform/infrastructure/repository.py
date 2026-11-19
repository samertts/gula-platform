from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app._compat import UTC
from app.national.scheduling_platform.domain.entities import (
    Appointment,
    AppointmentReminder,
    Calendar,
    Resource,
    Schedule,
    TimeSlot,
    WaitingList,
)
from app.national.scheduling_platform.domain.enums import AppointmentStatus, SlotStatus
from app.national.scheduling_platform.domain.repository import (
    AppointmentReminderRepository,
    AppointmentRepository,
    CalendarRepository,
    ResourceRepository,
    ScheduleRepository,
    TimeSlotRepository,
    WaitingListRepository,
)
from app.national.scheduling_platform.infrastructure.models import (
    NationalAppointment,
    NationalAppointmentReminder,
    NationalCalendar,
    NationalResource,
    NationalSchedule,
    NationalTimeSlot,
    NationalWaitingList,
)


class SQLAlchemyAppointmentRepository(AppointmentRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, appointment: Appointment) -> Appointment:
        model = self.db.query(NationalAppointment).filter(NationalAppointment.id == appointment.id).first()
        if model:
            model.patient_id = appointment.patient_id
            model.practitioner_id = appointment.practitioner_id
            model.facility_id = appointment.facility_id
            model.resource_id = appointment.resource_id
            model.title = appointment.title
            model.description = appointment.description
            model.start_at = appointment.start_at
            model.end_at = appointment.end_at
            model.status = appointment.status
            model.appointment_type = appointment.appointment_type
            model.recurrence_pattern = appointment.recurrence_pattern
            model.recurrence_end = appointment.recurrence_end
            model.reminder_enabled = appointment.reminder_enabled
            model.reminder_minutes_before = appointment.reminder_minutes_before
            model.notes = appointment.notes
            model.metadata_ = appointment.metadata
            model.created_by = appointment.created_by
            model.version = appointment.version
        else:
            model = NationalAppointment(
                id=appointment.id,
                patient_id=appointment.patient_id,
                practitioner_id=appointment.practitioner_id or None,
                facility_id=appointment.facility_id or None,
                resource_id=appointment.resource_id or None,
                title=appointment.title,
                description=appointment.description,
                start_at=appointment.start_at,
                end_at=appointment.end_at,
                status=appointment.status,
                appointment_type=appointment.appointment_type,
                recurrence_pattern=appointment.recurrence_pattern,
                recurrence_end=appointment.recurrence_end,
                reminder_enabled=appointment.reminder_enabled,
                reminder_minutes_before=appointment.reminder_minutes_before,
                notes=appointment.notes,
                metadata_=appointment.metadata,
                created_by=appointment.created_by,
                version=appointment.version,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, appointment_id: str) -> Appointment | None:
        model = self.db.query(NationalAppointment).filter(
            NationalAppointment.id == appointment_id,
            ~NationalAppointment.is_deleted,
        ).first()
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[Appointment]:
        query = self.db.query(NationalAppointment).filter(~NationalAppointment.is_deleted)
        for key, value in filters.items():
            if hasattr(NationalAppointment, key) and value is not None:
                query = query.filter(getattr(NationalAppointment, key) == value)
        models = query.order_by(NationalAppointment.start_at.asc().nullsfirst()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def delete(self, appointment_id: str, soft: bool = True) -> None:
        model = self.db.query(NationalAppointment).filter(
            NationalAppointment.id == appointment_id,
            ~NationalAppointment.is_deleted,
        ).first()
        if model:
            if soft:
                model.is_deleted = True
                model.deleted_at = datetime.now(UTC)
            else:
                self.db.delete(model)
            self.db.commit()

    async def find_by_patient(
        self,
        patient_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Appointment]:
        models = self.db.query(NationalAppointment).filter(
            NationalAppointment.patient_id == patient_id,
            ~NationalAppointment.is_deleted,
        ).order_by(NationalAppointment.start_at.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def find_by_practitioner(
        self,
        practitioner_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Appointment]:
        models = self.db.query(NationalAppointment).filter(
            NationalAppointment.practitioner_id == practitioner_id,
            ~NationalAppointment.is_deleted,
        ).order_by(NationalAppointment.start_at.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def find_by_status(
        self,
        status: AppointmentStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Appointment]:
        models = self.db.query(NationalAppointment).filter(
            NationalAppointment.status == status,
            ~NationalAppointment.is_deleted,
        ).order_by(NationalAppointment.start_at.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def find_overlapping(
        self,
        start_at: datetime,
        end_at: datetime,
        resource_id: str | None = None,
        practitioner_id: str | None = None,
        exclude_id: str | None = None,
    ) -> list[Appointment]:
        query = self.db.query(NationalAppointment).filter(
            ~NationalAppointment.is_deleted,
            NationalAppointment.start_at < end_at,
            NationalAppointment.end_at > start_at,
            NationalAppointment.status.notin_([
                AppointmentStatus.CANCELLED,
                AppointmentStatus.NO_SHOW,
                AppointmentStatus.ENTERED_IN_ERROR,
            ]),
        )
        if resource_id:
            query = query.filter(NationalAppointment.resource_id == resource_id)
        if practitioner_id:
            query = query.filter(NationalAppointment.practitioner_id == practitioner_id)
        if exclude_id:
            query = query.filter(NationalAppointment.id != exclude_id)
        models = query.all()
        return [m.to_domain() for m in models]

    async def count_by_status(self, status: AppointmentStatus) -> int:
        return self.db.query(func.count(NationalAppointment.id)).filter(
            NationalAppointment.status == status,
            ~NationalAppointment.is_deleted,
        ).scalar() or 0


class SQLAlchemyResourceRepository(ResourceRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, resource: Resource) -> Resource:
        model = self.db.query(NationalResource).filter(NationalResource.id == resource.id).first()
        if model:
            model.name = resource.name
            model.type = resource.type
            model.description = resource.description
            model.capacity = resource.capacity
            model.location = resource.location
            model.is_active = resource.is_active
            model.calendar_id = resource.calendar_id
            model.metadata_ = resource.metadata
        else:
            model = NationalResource(
                id=resource.id,
                name=resource.name,
                type=resource.type,
                description=resource.description,
                capacity=resource.capacity,
                location=resource.location,
                is_active=resource.is_active,
                calendar_id=resource.calendar_id,
                metadata_=resource.metadata,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, resource_id: str) -> Resource | None:
        model = self.db.query(NationalResource).filter(
            NationalResource.id == resource_id,
            ~NationalResource.is_deleted,
        ).first()
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[Resource]:
        query = self.db.query(NationalResource).filter(~NationalResource.is_deleted)
        for key, value in filters.items():
            if hasattr(NationalResource, key) and value is not None:
                query = query.filter(getattr(NationalResource, key) == value)
        models = query.order_by(NationalResource.name.asc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def delete(self, resource_id: str, soft: bool = True) -> None:
        model = self.db.query(NationalResource).filter(
            NationalResource.id == resource_id,
            ~NationalResource.is_deleted,
        ).first()
        if model:
            if soft:
                model.is_deleted = True
                model.deleted_at = datetime.now(UTC)
            else:
                self.db.delete(model)
            self.db.commit()

    async def find_by_type(
        self,
        type: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Resource]:
        from app.national.scheduling_platform.domain.enums import ResourceType as RT
        models = self.db.query(NationalResource).filter(
            NationalResource.type == RT(type),
            ~NationalResource.is_deleted,
        ).order_by(NationalResource.name.asc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]


class SQLAlchemyScheduleRepository(ScheduleRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, schedule: Schedule) -> Schedule:
        model = self.db.query(NationalSchedule).filter(NationalSchedule.id == schedule.id).first()
        if model:
            model.resource_id = schedule.resource_id
            model.date = schedule.date
            model.start_time = schedule.start_time
            model.end_time = schedule.end_time
            model.is_available = schedule.is_available
            model.slot_duration_minutes = schedule.slot_duration_minutes
        else:
            model = NationalSchedule(
                id=schedule.id,
                resource_id=schedule.resource_id,
                date=schedule.date,
                start_time=schedule.start_time,
                end_time=schedule.end_time,
                is_available=schedule.is_available,
                slot_duration_minutes=schedule.slot_duration_minutes,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, schedule_id: str) -> Schedule | None:
        model = self.db.query(NationalSchedule).filter(
            NationalSchedule.id == schedule_id,
            ~NationalSchedule.is_deleted,
        ).first()
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[Schedule]:
        query = self.db.query(NationalSchedule).filter(~NationalSchedule.is_deleted)
        for key, value in filters.items():
            if hasattr(NationalSchedule, key) and value is not None:
                query = query.filter(getattr(NationalSchedule, key) == value)
        models = query.order_by(NationalSchedule.created_at.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def delete(self, schedule_id: str) -> None:
        model = self.db.query(NationalSchedule).filter(
            NationalSchedule.id == schedule_id,
            ~NationalSchedule.is_deleted,
        ).first()
        if model:
            model.is_deleted = True
            model.deleted_at = datetime.now(UTC)
            self.db.commit()

    async def find_by_resource(
        self,
        resource_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Schedule]:
        models = self.db.query(NationalSchedule).filter(
            NationalSchedule.resource_id == resource_id,
            ~NationalSchedule.is_deleted,
        ).order_by(NationalSchedule.date.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def find_by_date(
        self,
        resource_id: str,
        date: date,
    ) -> Schedule | None:
        model = self.db.query(NationalSchedule).filter(
            NationalSchedule.resource_id == resource_id,
            NationalSchedule.date == date,
            ~NationalSchedule.is_deleted,
        ).first()
        if not model:
            return None
        return model.to_domain()


class SQLAlchemyTimeSlotRepository(TimeSlotRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, slot: TimeSlot) -> TimeSlot:
        model = self.db.query(NationalTimeSlot).filter(NationalTimeSlot.id == slot.id).first()
        if model:
            model.schedule_id = slot.schedule_id
            model.start_at = slot.start_at
            model.end_at = slot.end_at
            model.status = slot.status
            model.booked_by = slot.booked_by
            model.purpose = slot.purpose
        else:
            model = NationalTimeSlot(
                id=slot.id,
                schedule_id=slot.schedule_id,
                start_at=slot.start_at,
                end_at=slot.end_at,
                status=slot.status,
                booked_by=slot.booked_by,
                purpose=slot.purpose,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def save_many(self, slots: list[TimeSlot]) -> list[TimeSlot]:
        schedule_ids = {s.schedule_id for s in slots}
        existing = self.db.query(NationalTimeSlot).filter(
            NationalTimeSlot.schedule_id.in_(schedule_ids),
        ).all()
        existing_map = {f"{e.schedule_id}_{e.start_at.isoformat() if e.start_at else ''}": e for e in existing}

        for slot in slots:
            key = f"{slot.schedule_id}_{slot.start_at.isoformat() if slot.start_at else ''}"
            if key in existing_map:
                model = existing_map[key]
                model.start_at = slot.start_at
                model.end_at = slot.end_at
                model.status = slot.status
                model.booked_by = slot.booked_by
                model.purpose = slot.purpose
            else:
                model = NationalTimeSlot(
                    id=slot.id,
                    schedule_id=slot.schedule_id,
                    start_at=slot.start_at,
                    end_at=slot.end_at,
                    status=slot.status,
                    booked_by=slot.booked_by,
                    purpose=slot.purpose,
                )
                self.db.add(model)
        self.db.commit()
        return slots

    async def get(self, slot_id: str) -> TimeSlot | None:
        model = self.db.query(NationalTimeSlot).filter(
            NationalTimeSlot.id == slot_id,
        ).first()
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[TimeSlot]:
        query = self.db.query(NationalTimeSlot)
        for key, value in filters.items():
            if hasattr(NationalTimeSlot, key) and value is not None:
                query = query.filter(getattr(NationalTimeSlot, key) == value)
        models = query.order_by(NationalTimeSlot.start_at.asc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def delete(self, slot_id: str) -> None:
        model = self.db.query(NationalTimeSlot).filter(NationalTimeSlot.id == slot_id).first()
        if model:
            self.db.delete(model)
            self.db.commit()

    async def find_by_schedule(
        self,
        schedule_id: str,
    ) -> list[TimeSlot]:
        models = self.db.query(NationalTimeSlot).filter(
            NationalTimeSlot.schedule_id == schedule_id,
        ).order_by(NationalTimeSlot.start_at.asc()).all()
        return [m.to_domain() for m in models]

    async def find_available(
        self,
        resource_id: str,
        date_from: datetime,
        date_to: datetime,
    ) -> list[TimeSlot]:
        models = self.db.query(NationalTimeSlot).join(
            NationalSchedule,
            NationalTimeSlot.schedule_id == NationalSchedule.id,
        ).filter(
            NationalSchedule.resource_id == resource_id,
            NationalTimeSlot.status == SlotStatus.AVAILABLE,
            NationalTimeSlot.start_at >= date_from,
            NationalTimeSlot.end_at <= date_to,
            ~NationalSchedule.is_deleted,
        ).order_by(NationalTimeSlot.start_at.asc()).all()
        return [m.to_domain() for m in models]


class SQLAlchemyWaitingListRepository(WaitingListRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, entry: WaitingList) -> WaitingList:
        model = self.db.query(NationalWaitingList).filter(NationalWaitingList.id == entry.id).first()
        if model:
            model.patient_id = entry.patient_id
            model.resource_id = entry.resource_id
            model.preferred_date_from = entry.preferred_date_from
            model.preferred_date_to = entry.preferred_date_to
            model.preferred_time_from = entry.preferred_time_from
            model.preferred_time_to = entry.preferred_time_to
            model.priority = entry.priority
            model.status = entry.status
            model.notes = entry.notes
        else:
            model = NationalWaitingList(
                id=entry.id,
                patient_id=entry.patient_id,
                resource_id=entry.resource_id or None,
                preferred_date_from=entry.preferred_date_from,
                preferred_date_to=entry.preferred_date_to,
                preferred_time_from=entry.preferred_time_from,
                preferred_time_to=entry.preferred_time_to,
                priority=entry.priority,
                status=entry.status,
                notes=entry.notes,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, entry_id: str) -> WaitingList | None:
        model = self.db.query(NationalWaitingList).filter(
            NationalWaitingList.id == entry_id,
            ~NationalWaitingList.is_deleted,
        ).first()
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[WaitingList]:
        query = self.db.query(NationalWaitingList).filter(~NationalWaitingList.is_deleted)
        for key, value in filters.items():
            if hasattr(NationalWaitingList, key) and value is not None:
                query = query.filter(getattr(NationalWaitingList, key) == value)
        models = query.order_by(NationalWaitingList.priority.desc(), NationalWaitingList.created_at.asc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def delete(self, entry_id: str) -> None:
        model = self.db.query(NationalWaitingList).filter(
            NationalWaitingList.id == entry_id,
            ~NationalWaitingList.is_deleted,
        ).first()
        if model:
            model.is_deleted = True
            model.deleted_at = datetime.now(UTC)
            self.db.commit()

    async def find_by_patient(
        self,
        patient_id: str,
    ) -> list[WaitingList]:
        models = self.db.query(NationalWaitingList).filter(
            NationalWaitingList.patient_id == patient_id,
            ~NationalWaitingList.is_deleted,
        ).order_by(NationalWaitingList.created_at.desc()).all()
        return [m.to_domain() for m in models]

    async def find_by_resource(
        self,
        resource_id: str,
        status: str = "active",
    ) -> list[WaitingList]:
        models = self.db.query(NationalWaitingList).filter(
            NationalWaitingList.resource_id == resource_id,
            NationalWaitingList.status == status,
            ~NationalWaitingList.is_deleted,
        ).order_by(NationalWaitingList.priority.desc(), NationalWaitingList.created_at.asc()).all()
        return [m.to_domain() for m in models]


class SQLAlchemyCalendarRepository(CalendarRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, calendar: Calendar) -> Calendar:
        model = self.db.query(NationalCalendar).filter(NationalCalendar.id == calendar.id).first()
        if model:
            model.name = calendar.name
            model.description = calendar.description
            model.timezone = calendar.timezone
            model.business_hours = calendar.business_hours
            model.holidays = calendar.holidays
        else:
            model = NationalCalendar(
                id=calendar.id,
                name=calendar.name,
                description=calendar.description,
                timezone=calendar.timezone,
                business_hours=calendar.business_hours,
                holidays=calendar.holidays,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, calendar_id: str) -> Calendar | None:
        model = self.db.query(NationalCalendar).filter(
            NationalCalendar.id == calendar_id,
            ~NationalCalendar.is_deleted,
        ).first()
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Calendar]:
        models = self.db.query(NationalCalendar).filter(
            ~NationalCalendar.is_deleted,
        ).order_by(NationalCalendar.name.asc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def delete(self, calendar_id: str) -> None:
        model = self.db.query(NationalCalendar).filter(
            NationalCalendar.id == calendar_id,
            ~NationalCalendar.is_deleted,
        ).first()
        if model:
            model.is_deleted = True
            model.deleted_at = datetime.now(UTC)
            self.db.commit()


class SQLAlchemyAppointmentReminderRepository(AppointmentReminderRepository):

    def __init__(self, db: Session) -> None:
        self.db = db

    async def save(self, reminder: AppointmentReminder) -> AppointmentReminder:
        model = self.db.query(NationalAppointmentReminder).filter(
            NationalAppointmentReminder.id == reminder.id,
        ).first()
        if model:
            model.appointment_id = reminder.appointment_id
            model.channel = reminder.channel
            model.sent_at = reminder.sent_at
            model.status = reminder.status
            model.error = reminder.error
        else:
            model = NationalAppointmentReminder(
                id=reminder.id,
                appointment_id=reminder.appointment_id,
                channel=reminder.channel,
                sent_at=reminder.sent_at,
                status=reminder.status,
                error=reminder.error,
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model.to_domain()

    async def get(self, reminder_id: str) -> AppointmentReminder | None:
        model = self.db.query(NationalAppointmentReminder).filter(
            NationalAppointmentReminder.id == reminder_id,
        ).first()
        if not model:
            return None
        return model.to_domain()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[AppointmentReminder]:
        query = self.db.query(NationalAppointmentReminder)
        for key, value in filters.items():
            if hasattr(NationalAppointmentReminder, key) and value is not None:
                query = query.filter(getattr(NationalAppointmentReminder, key) == value)
        models = query.order_by(NationalAppointmentReminder.created_at.desc()).offset(skip).limit(limit).all()
        return [m.to_domain() for m in models]

    async def find_by_appointment(
        self,
        appointment_id: str,
    ) -> list[AppointmentReminder]:
        models = self.db.query(NationalAppointmentReminder).filter(
            NationalAppointmentReminder.appointment_id == appointment_id,
        ).order_by(NationalAppointmentReminder.created_at.desc()).all()
        return [m.to_domain() for m in models]

    async def find_due_reminders(
        self,
        before: datetime | None = None,
    ) -> list[AppointmentReminder]:
        cutoff = before or datetime.now(UTC)
        models = self.db.query(NationalAppointmentReminder).join(
            NationalAppointment,
            NationalAppointmentReminder.appointment_id == NationalAppointment.id,
        ).filter(
            NationalAppointmentReminder.status == "scheduled",
            NationalAppointment.start_at <= cutoff,
            ~NationalAppointment.is_deleted,
        ).order_by(NationalAppointment.start_at.asc()).all()
        return [m.to_domain() for m in models]
