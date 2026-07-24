from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Any

from app._compat import UTC
from app.national.scheduling_platform import (
    Appointment,
    AppointmentReminder,
    SchedulingPlatformService,
)
from app.national.scheduling_platform import WaitingList as NationalWaitingList

logger = logging.getLogger("gula.citizen.appointments")


@dataclass
class CitizenAppointment:
    id: str = ""
    citizen_id: str = ""
    provider_id: str = ""
    provider_name: str = ""
    facility_id: str = ""
    facility_name: str = ""
    appointment_type: str = ""
    start_at: str = ""
    end_at: str = ""
    status: str = ""
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class AppointmentService:
    def __init__(self, scheduling_service: SchedulingPlatformService) -> None:
        self._scheduling = scheduling_service

    async def book_appointment(
        self,
        citizen_id: str,
        practitioner_id: str = "",
        facility_id: str = "",
        resource_id: str = "",
        title: str = "",
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        appointment_type: str = "",
        notes: str = "",
    ) -> CitizenAppointment:
        appointment = await self._scheduling.create_appointment(
            patient_id=citizen_id,
            practitioner_id=practitioner_id,
            facility_id=facility_id,
            resource_id=resource_id,
            title=title,
            start_at=start_at,
            end_at=end_at,
            appointment_type=appointment_type,
            notes=notes,
        )
        return self._to_citizen_appointment(appointment)

    async def get_appointment(self, appointment_id: str) -> CitizenAppointment:
        appointment = await self._scheduling.get_appointment(appointment_id)
        return self._to_citizen_appointment(appointment)

    async def list_appointments(
        self,
        citizen_id: str,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[CitizenAppointment]:
        appointments = await self._scheduling.list_appointments(
            patient_id=citizen_id,
            status=status,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit,
        )
        return [self._to_citizen_appointment(a) for a in appointments]

    async def reschedule_appointment(
        self, appointment_id: str, new_start: datetime, new_end: datetime, reason: str = "",
    ) -> CitizenAppointment:
        appointment = await self._scheduling.reschedule_appointment(
            appointment_id, new_start, new_end, reason,
        )
        return self._to_citizen_appointment(appointment)

    async def cancel_appointment(self, appointment_id: str, reason: str = "") -> CitizenAppointment:
        appointment = await self._scheduling.cancel_appointment(appointment_id, reason)
        return self._to_citizen_appointment(appointment)

    def _to_citizen_appointment(self, apt: Appointment) -> CitizenAppointment:
        return CitizenAppointment(
            id=apt.id,
            citizen_id=apt.patient_id,
            provider_id=apt.practitioner_id,
            facility_id=apt.facility_id,
            appointment_type=apt.appointment_type,
            start_at=apt.start_at.isoformat() if apt.start_at else "",
            end_at=apt.end_at.isoformat() if apt.end_at else "",
            status=apt.status.value if hasattr(apt.status, "value") else str(apt.status),
            notes=apt.notes,
            metadata=apt.metadata,
        )


class QueueManager:
    def __init__(self) -> None:
        self._queues: dict[str, list[dict[str, Any]]] = {}

    def add_to_queue(self, facility_id: str, citizen_id: str, priority: int = 0) -> dict[str, Any]:
        entry = {
            "citizen_id": citizen_id,
            "facility_id": facility_id,
            "position": len(self._queues.get(facility_id, [])) + 1,
            "priority": priority,
            "status": "waiting",
            "added_at": datetime.now(UTC).isoformat(),
        }
        if facility_id not in self._queues:
            self._queues[facility_id] = []
        self._queues[facility_id].append(entry)
        return entry

    def remove_from_queue(self, facility_id: str, citizen_id: str) -> bool:
        queue = self._queues.get(facility_id, [])
        before = len(queue)
        self._queues[facility_id] = [e for e in queue if e["citizen_id"] != citizen_id]
        return len(self._queues[facility_id]) < before

    def get_queue_position(self, facility_id: str, citizen_id: str) -> int | None:
        queue = self._queues.get(facility_id, [])
        for i, entry in enumerate(queue):
            if entry["citizen_id"] == citizen_id:
                return i + 1
        return None

    def get_queue_status(self, facility_id: str) -> dict[str, Any]:
        queue = self._queues.get(facility_id, [])
        return {
            "facility_id": facility_id,
            "total_waiting": len(queue),
            "estimated_wait_minutes": len(queue) * 10,
            "queue": queue,
        }


class WaitingListManager:
    def __init__(self, scheduling_service: SchedulingPlatformService) -> None:
        self._scheduling = scheduling_service

    async def join_waiting_list(
        self,
        citizen_id: str,
        resource_id: str = "",
        preferred_date_from: date | None = None,
        preferred_date_to: date | None = None,
        preferred_time_from: time | None = None,
        preferred_time_to: time | None = None,
        notes: str = "",
    ) -> NationalWaitingList:
        return await self._scheduling.add_to_waiting_list(
            patient_id=citizen_id,
            resource_id=resource_id,
            preferred_date_from=preferred_date_from,
            preferred_date_to=preferred_date_to,
            preferred_time_from=preferred_time_from,
            preferred_time_to=preferred_time_to,
            notes=notes,
        )

    async def leave_waiting_list(self, entry_id: str) -> None:
        await self._scheduling.remove_from_waiting_list(entry_id)

    async def get_waiting_list_status(
        self, resource_id: str | None = None, skip: int = 0, limit: int = 100,
    ) -> list[NationalWaitingList]:
        return await self._scheduling.list_waiting_list(
            resource_id=resource_id, skip=skip, limit=limit,
        )


class AppointmentReminderService:
    def __init__(self, scheduling_service: SchedulingPlatformService) -> None:
        self._scheduling = scheduling_service

    async def send_reminders(self) -> list[AppointmentReminder]:
        return await self._scheduling.send_reminders()

    async def schedule_reminder(
        self, appointment_id: str, channel: str = "sms", minutes_before: int = 60,
    ) -> None:
        await self._scheduling.reschedule_appointment(
            appointment_id,
            datetime.now(UTC),
            datetime.now(UTC),
            reason="reminder_update",
        )
