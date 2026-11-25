from __future__ import annotations

import re
import secrets
from collections.abc import Callable
from datetime import datetime
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.national.domain.citizen import Citizen
from app.national.domain.health_number import HealthNumberSequence
from app.national.events.citizen_events import CitizenCreated, CitizenUpdated, HealthNumberAssigned
from app.national.exceptions import (
    CitizenNotFoundError,
    DuplicateHealthNumberError,
    GulaCitizenIdentifierCollisionError,
    GulaCitizenIdentifierExhaustedError,
    InvalidGulaCitizenIdentifierError,
)
from app.national.repositories.citizen_repository import CitizenRepository
from shared.events import events

GULA_CITIZEN_IDENTIFIER_PATTERN = re.compile(r"^\d{12}$")
_GULA_IDENTIFIER_RANDOM_SPACE = 100_000_000

# The reservation callback must atomically persist the candidate under a
# database UNIQUE constraint. A pre-check SELECT followed by INSERT is not an
# acceptable uniqueness guarantee in a multi-server concurrent environment.
IdentifierReservation = Callable[[str], bool]


def assert_gula_citizen_identifier_format(identifier: str) -> None:
    """Validate the internal 12-digit GULA Citizen Identifier shape.

    This identifier is not the Iraqi national ID. It must never be renamed or
    used as a substitute for the government-issued national number.
    """
    if not isinstance(identifier, str) or not GULA_CITIZEN_IDENTIFIER_PATTERN.fullmatch(identifier):
        raise InvalidGulaCitizenIdentifierError(identifier, "must be exactly 12 ASCII digits")


def generate_gula_citizen_identifier(
    *,
    birth_year: int,
    reserve: IdentifierReservation,
    max_attempts: int = 10,
    random_source: Callable[[], int] | None = None,
) -> str:
    """Generate and atomically reserve an immutable internal citizen identifier.

    The first four digits are the birth year at creation. The remaining eight
    digits come from a cryptographically secure source. ``reserve`` is the
    atomic database adapter: it must rely on a UNIQUE constraint and raise
    :class:`GulaCitizenIdentifierCollisionError` or return ``False`` when the
    candidate is already used. No pre-check-only uniqueness is assumed.
    """
    if not isinstance(birth_year, int) or isinstance(birth_year, bool):
        raise InvalidGulaCitizenIdentifierError("", "birth_year must be an integer")
    if not 1000 <= birth_year <= 9999:
        raise InvalidGulaCitizenIdentifierError("", "birth_year must be four digits")
    if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or max_attempts < 1:
        raise InvalidGulaCitizenIdentifierError("", "max_attempts must be a positive integer")

    random_int = random_source or (lambda: secrets.randbelow(_GULA_IDENTIFIER_RANDOM_SPACE))
    for _ in range(max_attempts):
        suffix = random_int()
        if not isinstance(suffix, int) or isinstance(suffix, bool) or not 0 <= suffix < _GULA_IDENTIFIER_RANDOM_SPACE:
            raise InvalidGulaCitizenIdentifierError("", "random source returned an out-of-range suffix")
        candidate = f"{birth_year:04d}{suffix:08d}"
        assert_gula_citizen_identifier_format(candidate)
        try:
            if reserve(candidate):
                return candidate
        except GulaCitizenIdentifierCollisionError:
            continue
    raise GulaCitizenIdentifierExhaustedError(max_attempts)


def assert_gula_citizen_identifier_immutable(original: str, candidate: str) -> None:
    """Reject regeneration after demographic correction."""
    assert_gula_citizen_identifier_format(original)
    assert_gula_citizen_identifier_format(candidate)
    if original != candidate:
        raise InvalidGulaCitizenIdentifierError(candidate, "identifier is immutable after creation")


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
        now = datetime.utcnow()
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
