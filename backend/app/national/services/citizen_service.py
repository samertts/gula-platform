from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.national.domain.citizen import Citizen
from app.national.domain.health_number import HealthNumberSequence
from app.national.events.citizen_events import CitizenCreated, CitizenUpdated, HealthNumberAssigned
from app.national.exceptions import CitizenNotFoundError, DuplicateHealthNumberError
from app.national.repositories.citizen_repository import CitizenRepository
from shared.events import events


class CitizenService:
    def __init__(self, repo: CitizenRepository, db: Session | None = None) -> None:
        self.repo = repo
        self._db = db

    async def register_citizen(self, data: dict[str, Any]) -> Citizen:
        health_number = await self._generate_health_number()
        existing = await self.repo.get_by_health_number(health_number)
        if existing:
            raise DuplicateHealthNumberError(health_number)
        citizen = Citizen(**{k: v for k, v in data.items() if hasattr(Citizen, k)})
        citizen.health_number = health_number
        result = await self.repo.create(citizen)
        events.emit(CitizenCreated.event_type, {"citizen_id": result.id, **data})
        events.emit(
            HealthNumberAssigned.event_type,
            {"citizen_id": result.id, "health_number": health_number},
        )
        return result

    async def get_citizen(self, citizen_id: str) -> Citizen:
        citizen = await self.repo.get(citizen_id)
        if not citizen:
            raise CitizenNotFoundError(citizen_id)
        return citizen

    async def update_citizen(self, citizen_id: str, data: dict[str, Any]) -> Citizen:
        citizen = await self.get_citizen(citizen_id)
        for key, value in data.items():
            if hasattr(citizen, key) and value is not None:
                setattr(citizen, key, value)
        result = await self.repo.update(citizen)
        events.emit(CitizenUpdated.event_type, {"citizen_id": result.id, **data})
        return result

    async def search_citizens(self, query: str, skip: int = 0, limit: int = 20) -> list[Citizen]:
        if not query:
            return await self.repo.list(skip=skip, limit=limit)
        pattern = f"%{query}%"
        db = self._db if self._db is not None else self.repo.db
        return (
            db.query(Citizen)
            .filter(
                ~Citizen.is_deleted,
                or_(
                    Citizen.first_name.ilike(pattern),
                    Citizen.father_name.ilike(pattern),
                    Citizen.grandfather_name.ilike(pattern),
                    Citizen.last_name.ilike(pattern),
                    Citizen.health_number.ilike(pattern),
                ),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    async def _generate_health_number(self, prefix: str = "IQ") -> str:
        now = datetime.now(UTC)
        year = now.year
        seq = await self._next_sequence(prefix, year)
        return f"{prefix}{year}{seq:06d}"

    async def _next_sequence(self, prefix: str, year: int) -> int:
        db = self._db
        if db is None:
            db = self.repo.db
        entry = (
            db.query(HealthNumberSequence)
            .filter(
                HealthNumberSequence.prefix == prefix,
                HealthNumberSequence.year == year,
                ~HealthNumberSequence.is_depleted,
            )
            .with_for_update()
            .first()
        )
        if entry is None:
            entry = HealthNumberSequence(
                prefix=prefix,
                sequence_number=0,
                year=year,
            )
            db.add(entry)
        entry.sequence_number += 1
        db.flush()
        return entry.sequence_number
