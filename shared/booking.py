from __future__ import annotations

import logging
from datetime import datetime, timedelta
from uuid import uuid4

from .domain.booking import Appointment, AppointmentStatus

logger = logging.getLogger("gula.booking")

# Alias for backward compatibility
BookingStatus = AppointmentStatus


class BookingEngine:
    """Manages appointment bookings with slot management."""

    def __init__(self) -> None:
        self._appointments: dict[str, Appointment] = {}

    def book(
        self,
        patient_id: str,
        lab_id: int,
        slot_time: datetime,
        test_types: list[str] | None = None,
        patient_name: str = "",
        doctor_name: str = "",
    ) -> Appointment:
        apt = Appointment(
            id=str(uuid4()),
            patient_id=patient_id,
            lab_id=lab_id,
            patient_name=patient_name,
            doctor_name=doctor_name,
            test_types=test_types or [],
            slot_time=slot_time.isoformat(),
            scheduled_at=slot_time.isoformat(),
            status=AppointmentStatus.PENDING,
        )
        self._appointments[apt.id] = apt
        logger.info("[BOOKING] Appointment created successfully")
        return apt

    def get(self, appointment_id: str) -> Appointment | None:
        return self._appointments.get(appointment_id)

    def confirm(self, appointment_id: str) -> Appointment:
        apt = self._get_or_raise(appointment_id)
        apt.transition_to(AppointmentStatus.CONFIRMED)
        return apt

    def check_in(self, appointment_id: str) -> Appointment:
        apt = self._get_or_raise(appointment_id)
        apt.transition_to(AppointmentStatus.CHECKED_IN)
        return apt

    def start(self, appointment_id: str) -> Appointment:
        apt = self._get_or_raise(appointment_id)
        apt.transition_to(AppointmentStatus.IN_PROGRESS)
        return apt

    def complete(self, appointment_id: str) -> Appointment:
        apt = self._get_or_raise(appointment_id)
        apt.transition_to(AppointmentStatus.COMPLETED)
        return apt

    def cancel(self, appointment_id: str, reason: str = "") -> Appointment:
        apt = self._get_or_raise(appointment_id)
        apt.transition_to(AppointmentStatus.CANCELLED)
        apt.notes = reason
        return apt

    def mark_no_show(self, appointment_id: str) -> Appointment:
        apt = self._get_or_raise(appointment_id)
        apt.transition_to(AppointmentStatus.NO_SHOW)
        return apt

    def list_by_patient(self, patient_id: str) -> list[Appointment]:
        return [a for a in self._appointments.values() if a.patient_id == patient_id]

    def list_by_lab(self, lab_id: int) -> list[Appointment]:
        return [a for a in self._appointments.values() if a.lab_id == lab_id]

    def list_by_date(self, lab_id: int, date: datetime) -> list[Appointment]:
        date_str = date.date().isoformat()
        return [
            a for a in self._appointments.values()
            if a.lab_id == lab_id and a.slot_time.startswith(date_str)
        ]

    def get_available_slots(
        self, lab_id: int, date: datetime,
        slot_duration_minutes: int = 30,
        start_hour: int = 8, end_hour: int = 17,
    ) -> list[str]:
        slots: list[str] = []
        existing = {a.slot_time for a in self.list_by_date(lab_id, date)
                    if a.status.is_active()}
        current = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        end = date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        while current < end:
            slot_str = current.isoformat()
            if slot_str not in existing:
                slots.append(slot_str)
            current += timedelta(minutes=slot_duration_minutes)
        return slots

    def _get_or_raise(self, appointment_id: str) -> Appointment:
        apt = self._appointments.get(appointment_id)
        if apt is None:
            raise KeyError(f"Appointment not found: {appointment_id}")
        return apt

    def count(self) -> int:
        return len(self._appointments)


# Global singleton
engine = BookingEngine()
