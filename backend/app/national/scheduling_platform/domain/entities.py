from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Any

from app._compat import UTC
from app.national.scheduling_platform.domain.enums import (
    AppointmentStatus,
    ConflictLevel,
    RecurrencePattern,
    ResourceType,
    SlotStatus,
)


@dataclass
class Appointment:
    id: str
    patient_id: str
    practitioner_id: str = ""
    facility_id: str = ""
    resource_id: str = ""
    title: str = ""
    description: str = ""
    start_at: datetime | None = None
    end_at: datetime | None = None
    status: AppointmentStatus = AppointmentStatus.PROPOSED
    appointment_type: str = ""
    recurrence_pattern: RecurrencePattern = RecurrencePattern.NONE
    recurrence_end: datetime | None = None
    reminder_enabled: bool = True
    reminder_minutes_before: int = 60
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    version: int = 1

    @property
    def is_booked(self) -> bool:
        return self.status == AppointmentStatus.BOOKED

    @property
    def is_active(self) -> bool:
        return self.status in (
            AppointmentStatus.PROPOSED,
            AppointmentStatus.PENDING,
            AppointmentStatus.BOOKED,
            AppointmentStatus.ARRIVED,
            AppointmentStatus.IN_PROGRESS,
        )

    @property
    def is_cancellable(self) -> bool:
        return self.status in (
            AppointmentStatus.PROPOSED,
            AppointmentStatus.PENDING,
            AppointmentStatus.BOOKED,
            AppointmentStatus.ARRIVED,
        )


@dataclass
class Resource:
    id: str
    name: str
    type: ResourceType = ResourceType.ROOM
    description: str = ""
    capacity: int = 1
    location: str = ""
    is_active: bool = True
    calendar_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Schedule:
    id: str
    resource_id: str
    date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    is_available: bool = True
    slot_duration_minutes: int = 30
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TimeSlot:
    id: str
    schedule_id: str
    start_at: datetime | None = None
    end_at: datetime | None = None
    status: SlotStatus = SlotStatus.AVAILABLE
    booked_by: str = ""
    purpose: str = ""

    @property
    def is_available(self) -> bool:
        return self.status == SlotStatus.AVAILABLE

    @property
    def is_booked(self) -> bool:
        return self.status == SlotStatus.BOOKED


@dataclass
class WaitingList:
    id: str
    patient_id: str
    resource_id: str = ""
    preferred_date_from: date | None = None
    preferred_date_to: date | None = None
    preferred_time_from: time | None = None
    preferred_time_to: time | None = None
    priority: int = 0
    status: str = "active"
    notes: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Calendar:
    id: str
    name: str
    description: str = ""
    timezone: str = "UTC"
    business_hours: dict[str, Any] = field(default_factory=dict)
    holidays: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class AppointmentReminder:
    id: str
    appointment_id: str
    channel: str = "email"
    sent_at: datetime | None = None
    status: str = "pending"
    error: str = ""


@dataclass
class ConflictResult:
    level: ConflictLevel = ConflictLevel.NONE
    conflicts: list[dict[str, Any]] = field(default_factory=list)

    def add_conflict(self, conflict_type: str, details: dict[str, Any]) -> None:
        self.conflicts.append({"type": conflict_type, **details})
        if conflict_type in ("time_overlap", "resource_double_booked", "personnel_double_booked"):
            self.level = ConflictLevel.HARD
        elif self.level == ConflictLevel.NONE:
            self.level = ConflictLevel.SOFT
