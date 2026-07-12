from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger("gula.booking")


class BookingStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class Appointment:
    def __init__(
        self, patient_id: str, lab_id: int, slot_time: datetime,
        test_types: list[str] | None = None, appointment_id: str | None = None,
    ) -> None:
        self.id = appointment_id or str(uuid4())
        self.patient_id = patient_id
        self.lab_id = lab_id
        self.slot_time = slot_time
        self.test_types = test_types or []
        self.status = BookingStatus.PENDING
        self.created_at = datetime.now(UTC)
        self.notes: str = ""

    def confirm(self) -> None:
        self.status = BookingStatus.CONFIRMED

    def cancel(self, reason: str = "") -> None:
        self.status = BookingStatus.CANCELLED
        self.notes = reason

    def complete(self) -> None:
        self.status = BookingStatus.COMPLETED

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "patient_id": self.patient_id, "lab_id": self.lab_id,
            "slot_time": self.slot_time.isoformat(), "test_types": self.test_types,
            "status": self.status.value, "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }


class BookingEngine:
    def __init__(self) -> None:
        self._appointments: dict[str, Appointment] = {}

    def book(self, appointment: Appointment) -> Appointment:
        self._appointments[appointment.id] = appointment
        return appointment

    def get(self, appointment_id: str) -> Appointment | None:
        return self._appointments.get(appointment_id)

    def list_by_patient(self, patient_id: str) -> list[Appointment]:
        return [a for a in self._appointments.values() if a.patient_id == patient_id]

    def list_by_lab(self, lab_id: int, date: datetime | None = None) -> list[Appointment]:
        results = [a for a in self._appointments.values() if a.lab_id == lab_id]
        if date:
            results = [a for a in results if a.slot_time.date() == date.date()]
        return results

    def get_available_slots(
        self, lab_id: int, date: datetime, duration_minutes: int = 15,
        start_hour: int = 8, end_hour: int = 17,
    ) -> list[datetime]:
        slots: list[datetime] = []
        current = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        end = date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        existing = {a.slot_time for a in self._appointments.values() if a.lab_id == lab_id}
        while current < end:
            if current not in existing:
                slots.append(current)
            current += timedelta(minutes=duration_minutes)
        return slots


__all__ = ["BookingStatus", "Appointment", "BookingEngine"]
