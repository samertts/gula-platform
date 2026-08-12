from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.national.services.citizen_service import CitizenService as NationalCitizenService

logger = logging.getLogger("gula.citizen.portal")


@dataclass
class TimelineEvent:
    event_id: str = ""
    event_type: str = ""
    event_date: str = ""
    title: str = ""
    description: str = ""
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MedicalHistoryRecord:
    record_id: str = ""
    record_type: str = ""
    date: str = ""
    provider: str = ""
    facility: str = ""
    diagnosis: str = ""
    notes: str = ""
    attachments: list[str] = field(default_factory=list)


class CitizenDashboard:
    def __init__(self, citizen_service: NationalCitizenService) -> None:
        self._citizen_service = citizen_service

    async def get_dashboard(self, citizen_id: str) -> dict[str, Any]:
        citizen = await self._citizen_service.get_citizen(citizen_id)
        return {
            "citizen_id": citizen.id,
            "health_number": citizen.health_number,
            "full_name": citizen.full_name,
            "date_of_birth": citizen.date_of_birth.isoformat() if citizen.date_of_birth else None,
            "blood_group": citizen.blood_group,
            "has_health_card": citizen.has_health_card,
            "upcoming_appointments": [],
            "pending_lab_results": 0,
            "active_medications": 0,
            "unread_notifications": 0,
        }


class HealthTimeline:
    def __init__(self) -> None:
        self._events: list[TimelineEvent] = []

    def add_event(self, event: TimelineEvent) -> None:
        self._events.append(event)

    def get_timeline(
        self,
        citizen_id: str,
        from_date: str | None = None,
        to_date: str | None = None,
        event_type: str | None = None,
        limit: int = 50,
    ) -> list[TimelineEvent]:
        results = list(self._events)
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if from_date:
            results = [e for e in results if e.event_date >= from_date]
        if to_date:
            results = [e for e in results if e.event_date <= to_date]
        results.sort(key=lambda e: e.event_date, reverse=True)
        return results[:limit]


class MedicalHistoryService:
    def __init__(self, citizen_service: NationalCitizenService) -> None:
        self._citizen_service = citizen_service
        self._records: dict[str, list[MedicalHistoryRecord]] = {}

    async def get_medical_history(
        self,
        citizen_id: str,
        record_type: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list[MedicalHistoryRecord]:
        await self._citizen_service.get_citizen(citizen_id)
        records = self._records.get(citizen_id, [])
        if record_type:
            records = [r for r in records if r.record_type == record_type]
        if from_date:
            records = [r for r in records if r.date >= from_date]
        if to_date:
            records = [r for r in records if r.date <= to_date]
        records.sort(key=lambda r: r.date, reverse=True)
        return records

    def add_record(self, citizen_id: str, record: MedicalHistoryRecord) -> None:
        if citizen_id not in self._records:
            self._records[citizen_id] = []
        self._records[citizen_id].append(record)
