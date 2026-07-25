from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app._compat import UTC

logger = logging.getLogger("gula.citizen.radiology")


@dataclass
class RadiologyStudy:
    study_id: str = ""
    citizen_id: str = ""
    order_id: str = ""
    modality: str = ""
    body_part: str = ""
    study_description: str = ""
    study_description_ar: str = ""
    status: str = "ordered"
    requested_at: str = ""
    scheduled_at: str = ""
    performed_at: str = ""
    reported_at: str = ""
    facility_id: str = ""
    facility_name: str = ""
    radiologist_name: str = ""
    findings: str = ""
    impression: str = ""
    report_url: str = ""
    image_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AppointmentSlot:
    slot_id: str = ""
    facility_id: str = ""
    facility_name: str = ""
    modality: str = ""
    start_at: str = ""
    end_at: str = ""
    available: bool = True


class CitizenRadiologyService:
    def __init__(self) -> None:
        self._studies: dict[str, list[RadiologyStudy]] = {}
        self._appointments: dict[str, list[dict[str, Any]]] = {}

    def get_studies(
        self,
        citizen_id: str,
        status: str | None = None,
        modality: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[RadiologyStudy]:
        studies = self._studies.get(citizen_id, [])
        if status:
            studies = [s for s in studies if s.status == status]
        if modality:
            studies = [s for s in studies if s.modality == modality]
        studies.sort(key=lambda s: s.requested_at, reverse=True)
        return studies[skip : skip + limit]

    def get_study_by_id(self, citizen_id: str, study_id: str) -> RadiologyStudy | None:
        studies = self._studies.get(citizen_id, [])
        for s in studies:
            if s.study_id == study_id:
                return s
        return None

    def add_study(self, citizen_id: str, study: RadiologyStudy) -> None:
        if citizen_id not in self._studies:
            self._studies[citizen_id] = []
        self._studies[citizen_id].append(study)

    def update_study_status(self, study_id: str, status: str) -> bool:
        for studies in self._studies.values():
            for s in studies:
                if s.study_id == study_id:
                    s.status = status
                    if status == "performed":
                        s.performed_at = datetime.now(UTC).isoformat()
                    elif status == "reported":
                        s.reported_at = datetime.now(UTC).isoformat()
                    return True
        return False


class AppointmentTracking:
    def __init__(self) -> None:
        self._appointments: dict[str, list[dict[str, Any]]] = {}

    def schedule_appointment(
        self,
        citizen_id: str,
        study_id: str,
        facility_id: str,
        slot: AppointmentSlot,
    ) -> dict[str, Any]:
        appointment = {
            "appointment_id": str(uuid.uuid4()),
            "citizen_id": citizen_id,
            "study_id": study_id,
            "facility_id": facility_id,
            "facility_name": slot.facility_name,
            "modality": slot.modality,
            "start_at": slot.start_at,
            "end_at": slot.end_at,
            "status": "scheduled",
            "created_at": datetime.now(UTC).isoformat(),
        }
        if citizen_id not in self._appointments:
            self._appointments[citizen_id] = []
        self._appointments[citizen_id].append(appointment)
        return appointment

    def cancel_appointment(self, appointment_id: str, citizen_id: str) -> bool:
        appointments = self._appointments.get(citizen_id, [])
        for apt in appointments:
            if apt["appointment_id"] == appointment_id:
                apt["status"] = "cancelled"
                return True
        return False

    def get_appointments(
        self,
        citizen_id: str,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        appointments = self._appointments.get(citizen_id, [])
        if status:
            appointments = [a for a in appointments if a["status"] == status]
        appointments.sort(key=lambda a: a["start_at"], reverse=True)
        return appointments
