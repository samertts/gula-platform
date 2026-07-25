from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.national.domain.encounter import Encounter
from app.national.enums import EncounterStatus
from app.national.exceptions import EncounterNotFoundError


def get_encounter(db: Session, encounter_id: str) -> Encounter | None:
    return (
        db.query(Encounter)
        .filter(
            Encounter.id == encounter_id,
            ~Encounter.is_deleted,
        )
        .first()
    )


def get_encounters_by_patient(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[Encounter]:
    return (
        db.query(Encounter)
        .filter(
            Encounter.patient_id == patient_id,
            ~Encounter.is_deleted,
        )
        .order_by(
            Encounter.period_start.desc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_encounter(db: Session, data: dict[str, Any]) -> Encounter:
    encounter = Encounter(**{k: v for k, v in data.items() if hasattr(Encounter, k)})
    db.add(encounter)
    db.flush()
    return encounter


def update_encounter(
    db: Session,
    encounter_id: str,
    data: dict[str, Any],
) -> Encounter:
    encounter = get_encounter(db, encounter_id)
    if not encounter:
        raise EncounterNotFoundError(encounter_id)
    for key, value in data.items():
        if hasattr(encounter, key) and value is not None:
            setattr(encounter, key, value)
    db.flush()
    return encounter


def complete_encounter(
    db: Session,
    encounter_id: str,
    user_id: str,
) -> Encounter:
    encounter = get_encounter(db, encounter_id)
    if not encounter:
        raise EncounterNotFoundError(encounter_id)
    encounter.status = EncounterStatus.COMPLETED
    encounter.period_end = datetime.now()
    db.flush()
    return encounter


def cancel_encounter(
    db: Session,
    encounter_id: str,
    user_id: str,
) -> Encounter:
    encounter = get_encounter(db, encounter_id)
    if not encounter:
        raise EncounterNotFoundError(encounter_id)
    encounter.status = EncounterStatus.CANCELLED
    db.flush()
    return encounter


def delete_encounter(db: Session, encounter_id: str) -> None:
    encounter = get_encounter(db, encounter_id)
    if not encounter:
        raise EncounterNotFoundError(encounter_id)
    encounter.soft_delete()
    db.flush()


def get_active_encounters_by_patient(
    db: Session,
    patient_id: str,
) -> list[Encounter]:
    return (
        db.query(Encounter)
        .filter(
            Encounter.patient_id == patient_id,
            ~Encounter.is_deleted,
            Encounter.status.notin_(
                [
                    EncounterStatus.COMPLETED,
                    EncounterStatus.CANCELLED,
                ],
            ),
        )
        .order_by(
            Encounter.period_start.desc(),
        )
        .all()
    )


def search_encounters(
    db: Session,
    patient_id: str | None = None,
    encounter_type: str | None = None,
    status: str | None = None,
    facility_id: str | None = None,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
    practitioner_id: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Encounter]:
    query = db.query(Encounter).filter(~~Encounter.is_deleted)

    filters = []
    if patient_id is not None:
        filters.append(Encounter.patient_id == patient_id)
    if encounter_type is not None:
        filters.append(Encounter.encounter_type == encounter_type)
    if status is not None:
        filters.append(Encounter.status == status)
    if facility_id is not None:
        filters.append(Encounter.facility_id == facility_id)
    if period_start is not None:
        filters.append(Encounter.period_start >= period_start)
    if period_end is not None:
        filters.append(Encounter.period_end <= period_end)
    if practitioner_id is not None:
        filters.append(Encounter.practitioner_id == practitioner_id)

    if filters:
        query = query.filter(and_(*filters))

    return (
        query.order_by(
            Encounter.period_start.desc(),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
