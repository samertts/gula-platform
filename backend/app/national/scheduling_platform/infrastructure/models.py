from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy import Enum as SAEnum

from app.national.base import BaseEntity, _ulid
from app.national.scheduling_platform.domain.enums import (
    AppointmentStatus,
    RecurrencePattern,
    ResourceType,
    SlotStatus,
)


class NationalAppointment(BaseEntity):
    __tablename__ = "national_scheduling_appointments"

    id = Column(String(26), primary_key=True, default=_ulid)
    patient_id = Column(String(26), nullable=False, index=True)
    practitioner_id = Column(String(26), nullable=True, index=True)
    facility_id = Column(String(26), nullable=True, index=True)
    resource_id = Column(String(26), nullable=True, index=True)
    title = Column(String(255), nullable=True, default="")
    description = Column(Text, nullable=True, default="")
    start_at = Column(DateTime(timezone=True), nullable=True, index=True)
    end_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        SAEnum(AppointmentStatus), nullable=False, default=AppointmentStatus.PROPOSED, index=True,
    )
    appointment_type = Column(String(100), nullable=True, default="")
    recurrence_pattern = Column(
        SAEnum(RecurrencePattern), nullable=False, default=RecurrencePattern.NONE,
    )
    recurrence_end = Column(DateTime(timezone=True), nullable=True)
    reminder_enabled = Column(Boolean, nullable=False, default=True)
    reminder_minutes_before = Column(Integer, nullable=False, default=60)
    notes = Column(Text, nullable=True, default="")
    metadata_ = Column("metadata", JSON, nullable=True, default=dict)
    created_by = Column(String(100), nullable=True)
    version = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        Index("ix_nat_sched_appt_patient_status", "patient_id", "status"),
        Index("ix_nat_sched_appt_practitioner_status", "practitioner_id", "status"),
        Index("ix_nat_sched_appt_resource_time", "resource_id", "start_at"),
        Index("ix_nat_sched_appt_practitioner_time", "practitioner_id", "start_at"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.scheduling_platform.domain.entities import Appointment

        return Appointment(
            id=self.id,
            patient_id=self.patient_id,
            practitioner_id=self.practitioner_id or "",
            facility_id=self.facility_id or "",
            resource_id=self.resource_id or "",
            title=self.title or "",
            description=self.description or "",
            start_at=self.start_at,
            end_at=self.end_at,
            status=self.status or AppointmentStatus.PROPOSED,
            appointment_type=self.appointment_type or "",
            recurrence_pattern=self.recurrence_pattern or RecurrencePattern.NONE,
            recurrence_end=self.recurrence_end,
            reminder_enabled=self.reminder_enabled if self.reminder_enabled is not None else True,
            reminder_minutes_before=self.reminder_minutes_before or 60,
            notes=self.notes or "",
            metadata=self.metadata_ or {},
            created_by=self.created_by or "",
            created_at=self.created_at,
            updated_at=self.updated_at,
            version=self.version,
        )


class NationalResource(BaseEntity):
    __tablename__ = "national_scheduling_resources"

    id = Column(String(26), primary_key=True, default=_ulid)
    name = Column(String(255), nullable=False, index=True)
    type = Column(SAEnum(ResourceType), nullable=False, default=ResourceType.ROOM, index=True)
    description = Column(Text, nullable=True, default="")
    capacity = Column(Integer, nullable=False, default=1)
    location = Column(String(255), nullable=True, default="")
    is_active = Column(Boolean, nullable=False, default=True)
    calendar_id = Column(String(26), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True, default=dict)

    __table_args__ = (
        Index("ix_nat_sched_res_type_active", "type", "is_active"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.scheduling_platform.domain.entities import Resource

        return Resource(
            id=self.id,
            name=self.name,
            type=self.type or ResourceType.ROOM,
            description=self.description or "",
            capacity=self.capacity,
            location=self.location or "",
            is_active=self.is_active if self.is_active is not None else True,
            calendar_id=self.calendar_id or "",
            metadata=self.metadata_ or {},
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class NationalSchedule(BaseEntity):
    __tablename__ = "national_scheduling_schedules"

    id = Column(String(26), primary_key=True, default=_ulid)
    resource_id = Column(
        String(26),
        ForeignKey("national_scheduling_resources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date = Column(Date, nullable=True, index=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    is_available = Column(Boolean, nullable=False, default=True)
    slot_duration_minutes = Column(Integer, nullable=False, default=30)

    __table_args__ = (
        Index("ix_nat_sched_sched_resource_date", "resource_id", "date", unique=True),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.scheduling_platform.domain.entities import Schedule

        return Schedule(
            id=self.id,
            resource_id=self.resource_id,
            date=self.date,
            start_time=self.start_time,
            end_time=self.end_time,
            is_available=self.is_available if self.is_available is not None else True,
            slot_duration_minutes=self.slot_duration_minutes,
            created_at=self.created_at,
        )


class NationalTimeSlot(BaseEntity):
    __tablename__ = "national_scheduling_time_slots"

    id = Column(String(26), primary_key=True, default=_ulid)
    schedule_id = Column(
        String(26),
        ForeignKey("national_scheduling_schedules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_at = Column(DateTime(timezone=True), nullable=True)
    end_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(SAEnum(SlotStatus), nullable=False, default=SlotStatus.AVAILABLE, index=True)
    booked_by = Column(String(100), nullable=True, default="")
    purpose = Column(String(255), nullable=True, default="")

    __table_args__ = (
        Index("ix_nat_sched_slot_schedule_status", "schedule_id", "status"),
        Index("ix_nat_sched_slot_start_status", "start_at", "status"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.scheduling_platform.domain.entities import TimeSlot

        return TimeSlot(
            id=self.id,
            schedule_id=self.schedule_id,
            start_at=self.start_at,
            end_at=self.end_at,
            status=self.status or SlotStatus.AVAILABLE,
            booked_by=self.booked_by or "",
            purpose=self.purpose or "",
        )


class NationalWaitingList(BaseEntity):
    __tablename__ = "national_scheduling_waiting_list"

    id = Column(String(26), primary_key=True, default=_ulid)
    patient_id = Column(String(26), nullable=False, index=True)
    resource_id = Column(String(26), nullable=True, index=True)
    preferred_date_from = Column(Date, nullable=True)
    preferred_date_to = Column(Date, nullable=True)
    preferred_time_from = Column(Time, nullable=True)
    preferred_time_to = Column(Time, nullable=True)
    priority = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="active", index=True)
    notes = Column(Text, nullable=True, default="")

    __table_args__ = (
        Index("ix_nat_sched_wl_patient_status", "patient_id", "status"),
        Index("ix_nat_sched_wl_resource_status", "resource_id", "status"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.scheduling_platform.domain.entities import WaitingList

        return WaitingList(
            id=self.id,
            patient_id=self.patient_id,
            resource_id=self.resource_id or "",
            preferred_date_from=self.preferred_date_from,
            preferred_date_to=self.preferred_date_to,
            preferred_time_from=self.preferred_time_from,
            preferred_time_to=self.preferred_time_to,
            priority=self.priority,
            status=self.status,
            notes=self.notes or "",
            created_at=self.created_at,
        )


class NationalCalendar(BaseEntity):
    __tablename__ = "national_scheduling_calendars"

    id = Column(String(26), primary_key=True, default=_ulid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True, default="")
    timezone = Column(String(50), nullable=False, default="UTC")
    business_hours = Column(JSON, nullable=True, default=dict)
    holidays = Column(JSON, nullable=True, default=list)

    __table_args__ = {"extend_existing": True}

    def to_domain(self):
        from app.national.scheduling_platform.domain.entities import Calendar

        return Calendar(
            id=self.id,
            name=self.name,
            description=self.description or "",
            timezone=self.timezone,
            business_hours=self.business_hours or {},
            holidays=self.holidays or [],
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class NationalAppointmentReminder(BaseEntity):
    __tablename__ = "national_scheduling_appointment_reminders"

    id = Column(String(26), primary_key=True, default=_ulid)
    appointment_id = Column(
        String(26),
        ForeignKey("national_scheduling_appointments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel = Column(String(50), nullable=False, default="email")
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    error = Column(Text, nullable=True, default="")

    __table_args__ = (
        Index("ix_nat_sched_reminder_status", "status", "sent_at"),
        {"extend_existing": True},
    )

    def to_domain(self):
        from app.national.scheduling_platform.domain.entities import AppointmentReminder

        return AppointmentReminder(
            id=self.id,
            appointment_id=self.appointment_id,
            channel=self.channel,
            sent_at=self.sent_at,
            status=self.status,
            error=self.error or "",
        )
