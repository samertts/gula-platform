from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class AppointmentStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


@dataclass
class Appointment:
    id: str = ""
    patient_id: int = 0
    lab_id: int = 0
    doctor_name: str = ""
    test_types: list[str] = field(default_factory=list)
    scheduled_at: str = ""
    status: AppointmentStatus = AppointmentStatus.PENDING
    notes: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid4())
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "patient_id": self.patient_id, "lab_id": self.lab_id,
            "doctor_name": self.doctor_name, "test_types": self.test_types,
            "scheduled_at": self.scheduled_at, "status": self.status.value, "notes": self.notes,
        }


__all__ = ["Appointment", "AppointmentStatus"]
