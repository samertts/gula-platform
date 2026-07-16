from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.database import Base
from app.models.lab_order import LabOrder
from app.national.domain.encounter import Encounter
from app.national.domain.patient import Patient as NationalPatient


class CanonicalEncounter(Base):
    __abstract__ = True

    id: str
    encounter_type: str | None
    status: str | None
    patient_id: str | None
    citizen_id: str | None
    organization_id: str | None
    facility_id: str | None
    practitioner_id: str | None
    period_start: datetime | None
    period_end: datetime | None
    reason_code: str | None
    reason_description: str | None
    diagnosis_code: str | None
    icd10_code: str | None
    lab_id: int | None
    lab_order_id: int | None

    @classmethod
    def query_all(cls, db: Session, lab_id: int | None = None, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        query = db.query(
            Encounter.id,
            Encounter.encounter_type,
            Encounter.status,
            Encounter.patient_id,
            Encounter.citizen_id,
            Encounter.organization_id,
            Encounter.facility_id,
            Encounter.practitioner_id,
            Encounter.period_start,
            Encounter.period_end,
            Encounter.reason_code,
            Encounter.reason_description,
            Encounter.diagnosis_code,
            Encounter.icd10_code,
            NationalPatient.lab_id,
            LabOrder.id.label("lab_order_id"),
        ).outerjoin(
            NationalPatient,
            NationalPatient.id == Encounter.patient_id,
        ).outerjoin(
            LabOrder,
            and_(
                LabOrder.patient_id == NationalPatient.lab_patient_id,
                LabOrder.lab_id == NationalPatient.lab_id,
            ),
        )

        if lab_id is not None:
            query = query.filter(NationalPatient.lab_id == lab_id)

        rows = query.order_by(Encounter.period_start.desc().nullslast()).offset(skip).limit(limit).all()
        return [dict(row._mapping) for row in rows]

    @classmethod
    def get_by_id(cls, db: Session, encounter_id: str, lab_id: int | None = None) -> dict[str, Any] | None:
        query = db.query(
            Encounter.id,
            Encounter.encounter_type,
            Encounter.status,
            Encounter.patient_id,
            Encounter.citizen_id,
            Encounter.organization_id,
            Encounter.facility_id,
            Encounter.practitioner_id,
            Encounter.period_start,
            Encounter.period_end,
            Encounter.reason_code,
            Encounter.reason_description,
            Encounter.diagnosis_code,
            Encounter.icd10_code,
            NationalPatient.lab_id,
            LabOrder.id.label("lab_order_id"),
        ).outerjoin(
            NationalPatient,
            NationalPatient.id == Encounter.patient_id,
        ).outerjoin(
            LabOrder,
            and_(
                LabOrder.patient_id == NationalPatient.lab_patient_id,
                LabOrder.lab_id == NationalPatient.lab_id,
            ),
        ).filter(
            Encounter.id == encounter_id,
        )

        if lab_id is not None:
            query = query.filter(NationalPatient.lab_id == lab_id)

        row = query.first()
        return dict(row._mapping) if row else None
