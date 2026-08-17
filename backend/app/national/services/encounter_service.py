from __future__ import annotations

from datetime import datetime

from app._compat import UTC
from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.domain.exceptions import ConflictError
from app.national.domain.encounter import Encounter
from app.national.enums import EncounterStatus
from app.national.exceptions import EncounterNotFoundError
from app.services.audit_service import log_action


FLOW_TRANSITIONS: dict[str, set[str]] = {
    "planned": {"arrived", "cancelled"},
    "arrived": {"triaged", "cancelled"},
    "triaged": {"in_progress", "cancelled"},
    "in_progress": {"admitted", "discharge_pending", "transfer_pending", "cancelled"},
    "admitted": {"in_progress", "discharge_pending", "transfer_pending"},
    "transfer_pending": {"admitted", "cancelled"},
    "discharge_pending": {"discharged", "in_progress"},
    "discharged": set(),
    "cancelled": set(),
}

_FLOW_TO_FHIR_STATUS = {
    "planned": EncounterStatus.PLANNED,
    "arrived": EncounterStatus.PLANNED,
    "triaged": EncounterStatus.PLANNED,
    "in_progress": EncounterStatus.IN_PROGRESS,
    "admitted": EncounterStatus.IN_PROGRESS,
    "transfer_pending": EncounterStatus.IN_PROGRESS,
    "discharge_pending": EncounterStatus.IN_PROGRESS,
    "discharged": EncounterStatus.DISCHARGED,
    "cancelled": EncounterStatus.CANCELLED,
}


def get_encounter(db: Session, encounter_id: str, lab_id: int | None = None, for_update: bool = False) -> Encounter | None:
    query = db.query(Encounter).filter(
        Encounter.id == encounter_id,
        ~Encounter.is_deleted,
    )
    if lab_id is not None:
        query = query.filter(Encounter.lab_id == lab_id)
    if for_update:
        query = query.with_for_update()
    return query.first()


def get_encounters_by_patient(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 50,
    lab_id: int | None = None,
) -> list[Encounter]:
    query = db.query(Encounter).filter(
        Encounter.patient_id == patient_id,
        ~Encounter.is_deleted,
    )
    if lab_id is not None:
        query = query.filter(Encounter.lab_id == lab_id)
    return query.order_by(
        Encounter.period_start.desc(),
    ).offset(skip).limit(limit).all()


def create_encounter(db: Session, data: dict[str, Any]) -> Encounter:
    encounter = Encounter(**{k: v for k, v in data.items() if hasattr(Encounter, k)})
    db.add(encounter)
    db.flush()
    return encounter


def transition_flow_state(
    db: Session,
    encounter_id: str,
    target_state: str,
    user_id: int,
    expected_version: int | None = None,
    lab_id: int | None = None,
) -> Encounter:
    """Move an encounter through the short government-hospital workflow.

    Invalid transitions are hard failures. Repeating the current state is
    idempotent and returns the current resource without a duplicate side effect.
    """
    if target_state not in FLOW_TRANSITIONS:
        raise ConflictError(f"Unknown flow state: {target_state}")
    encounter = get_encounter(db, encounter_id, lab_id=lab_id, for_update=True)
    if encounter is None:
        raise EncounterNotFoundError(encounter_id)
    current_state = encounter.flow_state or "planned"
    if expected_version is not None and encounter.version != expected_version:
        raise ConflictError("Encounter version conflict; refresh before retrying")
    if current_state == target_state:
        return encounter
    if target_state not in FLOW_TRANSITIONS.get(current_state, set()):
        raise ConflictError(f"Invalid encounter transition: {current_state} -> {target_state}")

    now = datetime.now(UTC)
    before = {"flow_state": current_state, "status": str(encounter.status), "version": encounter.version}
    encounter.flow_state = target_state
    encounter.status = _FLOW_TO_FHIR_STATUS[target_state]
    if target_state == "arrived":
        encounter.arrival_at = now
    elif target_state == "triaged":
        encounter.triage_at = now
    elif target_state == "admitted":
        encounter.admission_at = now
    elif target_state == "discharged":
        encounter.discharge_at = now
        encounter.period_end = now
    if target_state == "cancelled":
        encounter.period_end = encounter.period_end or now
    encounter.version = (encounter.version or 1) + 1
    db.flush()
    log_action(db, "encounter.flow_transition", encounter.id, encounter.lab_id, user_id, {
        "before": before,
        "after": {"flow_state": target_state, "status": str(encounter.status), "version": encounter.version},
    })
    return encounter


def update_encounter(
    db: Session,
    encounter_id: str,
    data: dict[str, Any],
    lab_id: int | None = None,
) -> Encounter:
    encounter = get_encounter(db, encounter_id, lab_id=lab_id)
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
    lab_id: int | None = None,
) -> Encounter:
    encounter = get_encounter(db, encounter_id, lab_id=lab_id)
    if not encounter:
        raise EncounterNotFoundError(encounter_id)
    if encounter.flow_state == "discharged":
        return encounter
    return transition_flow_state(
        db,
        encounter_id,
        "discharged",
        int(user_id),
        expected_version=encounter.version,
        lab_id=lab_id,
    )


def cancel_encounter(
    db: Session,
    encounter_id: str,
    user_id: str,
    lab_id: int | None = None,
) -> Encounter:
    encounter = get_encounter(db, encounter_id, lab_id=lab_id)
    if not encounter:
        raise EncounterNotFoundError(encounter_id)
    if encounter.flow_state == "cancelled":
        return encounter
    return transition_flow_state(
        db,
        encounter_id,
        "cancelled",
        int(user_id),
        expected_version=encounter.version,
        lab_id=lab_id,
    )


def delete_encounter(db: Session, encounter_id: str, lab_id: int | None = None) -> None:
    encounter = get_encounter(db, encounter_id, lab_id=lab_id)
    if not encounter:
        raise EncounterNotFoundError(encounter_id)
    encounter.soft_delete()
    db.flush()


def get_active_encounters_by_patient(
    db: Session,
    patient_id: str,
) -> list[Encounter]:
    return db.query(Encounter).filter(
        Encounter.patient_id == patient_id,
        ~Encounter.is_deleted,
        Encounter.status.notin_([
            EncounterStatus.COMPLETED,
            EncounterStatus.CANCELLED,
        ]),
    ).order_by(
        Encounter.period_start.desc(),
    ).all()


def search_encounters(
    db: Session,
    patient_id: str | None = None,
    encounter_type: str | None = None,
    lab_id: int | None = None,
    status: str | None = None,
    facility_id: str | None = None,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
    practitioner_id: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Encounter]:
    query = db.query(Encounter).filter(~Encounter.is_deleted)

    filters = []
    if lab_id is not None:
        filters.append(Encounter.lab_id == lab_id)
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

    return query.order_by(
        Encounter.period_start.desc(),
    ).offset(skip).limit(limit).all()
