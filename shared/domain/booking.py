from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from datetime import UTC


class AppointmentStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

    def is_active(self) -> bool:
        return self in (
            AppointmentStatus.PENDING,
            AppointmentStatus.CONFIRMED,
            AppointmentStatus.CHECKED_IN,
            AppointmentStatus.IN_PROGRESS,
        )

    def is_terminal(self) -> bool:
        return self in (
            AppointmentStatus.COMPLETED,
            AppointmentStatus.CANCELLED,
            AppointmentStatus.NO_SHOW,
        )


_VALID_TRANSITIONS: dict[AppointmentStatus, set[AppointmentStatus]] = {
    AppointmentStatus.PENDING: {AppointmentStatus.CONFIRMED, AppointmentStatus.CANCELLED},
    AppointmentStatus.CONFIRMED: {AppointmentStatus.CHECKED_IN, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW},
    AppointmentStatus.CHECKED_IN: {AppointmentStatus.IN_PROGRESS, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW},
    AppointmentStatus.IN_PROGRESS: {AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED},
    AppointmentStatus.COMPLETED: set(),
    AppointmentStatus.CANCELLED: set(),
    AppointmentStatus.NO_SHOW: set(),
}


@dataclass
class Appointment:
    id: str = ""
    patient_id: str = ""
    lab_id: int = 0
    patient_name: str = ""
    doctor_name: str = ""
    test_types: list[str] = field(default_factory=list)
    scheduled_at: str = ""
    slot_time: str = ""
    status: AppointmentStatus = AppointmentStatus.PENDING
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def transition_to(self, new_status: AppointmentStatus) -> None:
        allowed = _VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from {self.status.value} to {new_status.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )
        self.status = new_status
        self.updated_at = datetime.now(UTC).isoformat()

    def can_check_in(self) -> bool:
        return self.status == AppointmentStatus.CONFIRMED

    def can_start(self) -> bool:
        return self.status == AppointmentStatus.CHECKED_IN

    def is_reschedulable(self) -> bool:
        return self.status in (AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "lab_id": self.lab_id,
            "patient_name": self.patient_name,
            "doctor_name": self.doctor_name,
            "test_types": self.test_types,
            "scheduled_at": self.scheduled_at,
            "slot_time": self.slot_time,
            "status": self.status.value,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


__all__ = ["Appointment", "AppointmentStatus"]
