from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any

from app.national.scheduling_platform.domain.entities import (
    Appointment,
    AppointmentReminder,
    Calendar,
    Resource,
    Schedule,
    TimeSlot,
    WaitingList,
)
from app.national.scheduling_platform.domain.enums import AppointmentStatus


class AppointmentRepository(ABC):
    @abstractmethod
    async def save(self, appointment: Appointment) -> Appointment: ...

    @abstractmethod
    async def get(self, appointment_id: str) -> Appointment | None: ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[Appointment]: ...

    @abstractmethod
    async def delete(self, appointment_id: str, soft: bool = True) -> None: ...

    @abstractmethod
    async def find_by_patient(
        self,
        patient_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Appointment]: ...

    @abstractmethod
    async def find_by_practitioner(
        self,
        practitioner_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Appointment]: ...

    @abstractmethod
    async def find_by_status(
        self,
        status: AppointmentStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Appointment]: ...

    @abstractmethod
    async def find_overlapping(
        self,
        start_at: datetime,
        end_at: datetime,
        resource_id: str | None = None,
        practitioner_id: str | None = None,
        exclude_id: str | None = None,
    ) -> list[Appointment]: ...

    @abstractmethod
    async def count_by_status(self, status: AppointmentStatus) -> int: ...


class ResourceRepository(ABC):
    @abstractmethod
    async def save(self, resource: Resource) -> Resource: ...

    @abstractmethod
    async def get(self, resource_id: str) -> Resource | None: ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[Resource]: ...

    @abstractmethod
    async def delete(self, resource_id: str, soft: bool = True) -> None: ...

    @abstractmethod
    async def find_by_type(
        self,
        type: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Resource]: ...


class ScheduleRepository(ABC):
    @abstractmethod
    async def save(self, schedule: Schedule) -> Schedule: ...

    @abstractmethod
    async def get(self, schedule_id: str) -> Schedule | None: ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[Schedule]: ...

    @abstractmethod
    async def delete(self, schedule_id: str) -> None: ...

    @abstractmethod
    async def find_by_resource(
        self,
        resource_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Schedule]: ...

    @abstractmethod
    async def find_by_date(
        self,
        resource_id: str,
        date: date,
    ) -> Schedule | None: ...


class TimeSlotRepository(ABC):
    @abstractmethod
    async def save(self, slot: TimeSlot) -> TimeSlot: ...

    @abstractmethod
    async def save_many(self, slots: list[TimeSlot]) -> list[TimeSlot]: ...

    @abstractmethod
    async def get(self, slot_id: str) -> TimeSlot | None: ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[TimeSlot]: ...

    @abstractmethod
    async def delete(self, slot_id: str) -> None: ...

    @abstractmethod
    async def find_by_schedule(
        self,
        schedule_id: str,
    ) -> list[TimeSlot]: ...

    @abstractmethod
    async def find_available(
        self,
        resource_id: str,
        date_from: datetime,
        date_to: datetime,
    ) -> list[TimeSlot]: ...


class WaitingListRepository(ABC):
    @abstractmethod
    async def save(self, entry: WaitingList) -> WaitingList: ...

    @abstractmethod
    async def get(self, entry_id: str) -> WaitingList | None: ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[WaitingList]: ...

    @abstractmethod
    async def delete(self, entry_id: str) -> None: ...

    @abstractmethod
    async def find_by_patient(
        self,
        patient_id: str,
    ) -> list[WaitingList]: ...

    @abstractmethod
    async def find_by_resource(
        self,
        resource_id: str,
        status: str = "active",
    ) -> list[WaitingList]: ...


class CalendarRepository(ABC):
    @abstractmethod
    async def save(self, calendar: Calendar) -> Calendar: ...

    @abstractmethod
    async def get(self, calendar_id: str) -> Calendar | None: ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Calendar]: ...

    @abstractmethod
    async def delete(self, calendar_id: str) -> None: ...


class AppointmentReminderRepository(ABC):
    @abstractmethod
    async def save(self, reminder: AppointmentReminder) -> AppointmentReminder: ...

    @abstractmethod
    async def get(self, reminder_id: str) -> AppointmentReminder | None: ...

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> list[AppointmentReminder]: ...

    @abstractmethod
    async def find_by_appointment(
        self,
        appointment_id: str,
    ) -> list[AppointmentReminder]: ...

    @abstractmethod
    async def find_due_reminders(
        self,
        before: datetime | None = None,
    ) -> list[AppointmentReminder]: ...
