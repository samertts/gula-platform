from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.database import Base
from app.models.lab_order import LabOrder
from app.national.domain.encounter import Encounter
from app.national.domain.patient import Patient as NationalPatient


class CanonicalEncounter(Base):
    __abstract__ = True

    id: str
    encounter_type: Optional[str]
    status: Optional[str]
    patient_id: Optional[str]
    citizen_id: Optional[str]
    organization_id: Optional[str]
    facility_id: Optional[str]
    practitioner_id: Optional[str]
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    reason_code: Optional[str]
    reason_description: Optional[str]
    diagnosis_code: Optional[str]
    icd10_code: Optional[str]
    lab_id: Optional[int]
    lab_order_id: Optional[int]

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
