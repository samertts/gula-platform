from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.national.domain.observation import Observation
from app.national.exceptions import PatientNotFoundError


def get_observation(db: Session, observation_id: str) -> Observation | None:
    return db.query(Observation).filter(
        Observation.id == observation_id,
        ~Observation.is_deleted,
    ).first()


def get_observations_by_patient(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[Observation]:
    return db.query(Observation).filter(
        Observation.patient_id == patient_id,
        ~Observation.is_deleted,
    ).order_by(
        Observation.effective_datetime.desc(),
    ).offset(skip).limit(limit).all()


def get_observations_by_encounter(
    db: Session,
    encounter_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[Observation]:
    return db.query(Observation).filter(
        Observation.encounter_id == encounter_id,
        ~Observation.is_deleted,
    ).order_by(
        Observation.effective_datetime.desc(),
    ).offset(skip).limit(limit).all()


def get_vital_signs_by_patient(
    db: Session,
    patient_id: str,
    limit: int = 100,
) -> list[Observation]:
    return db.query(Observation).filter(
        Observation.patient_id == patient_id,
        Observation.category == "vital-signs",
        ~Observation.is_deleted,
    ).order_by(
        Observation.effective_datetime.desc(),
    ).limit(limit).all()


def create_observation(db: Session, data: dict[str, Any]) -> Observation:
    observation = Observation(**{k: v for k, v in data.items() if hasattr(Observation, k)})
    db.add(observation)
    db.flush()
    return observation


def update_observation(
    db: Session,
    observation_id: str,
    data: dict[str, Any],
) -> Observation:
    observation = get_observation(db, observation_id)
    if not observation:
        raise PatientNotFoundError(observation_id)
    for key, value in data.items():
        if hasattr(observation, key) and value is not None:
            setattr(observation, key, value)
    db.flush()
    return observation


def delete_observation(db: Session, observation_id: str) -> None:
    observation = get_observation(db, observation_id)
    if not observation:
        raise PatientNotFoundError(observation_id)
    observation.soft_delete()
    db.flush()


def search_observations(
    db: Session,
    patient_id: str | None = None,
    category: str | None = None,
    code: str | None = None,
    status: str | None = None,
    effective_start: datetime | None = None,
    effective_end: datetime | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Observation]:
    query = db.query(Observation).filter(~~Observation.is_deleted)

    filters = []
    if patient_id is not None:
        filters.append(Observation.patient_id == patient_id)
    if category is not None:
        filters.append(Observation.category == category)
    if code is not None:
        filters.append(Observation.code == code)
    if status is not None:
        filters.append(Observation.status == status)
    if effective_start is not None:
        filters.append(Observation.effective_datetime >= effective_start)
    if effective_end is not None:
        filters.append(Observation.effective_datetime <= effective_end)

    if filters:
        query = query.filter(and_(*filters))

    return query.order_by(
        Observation.effective_datetime.desc(),
    ).offset(skip).limit(limit).all()
