from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.lab_order import LabOrder
from app.national.domain.encounter import Encounter
from app.national.domain.patient import Patient as NationalPatient
from app.national_data.base import DataPlatformBase


class CanonicalProcedure(DataPlatformBase):
    __abstract__ = True

    procedure_id: int
    lab_id: int
    patient_id: int
    order_id: int
    procedure_name: str
    procedure_code: str | None
    status: str
    performed_at: datetime | None
    created_at: datetime | None
    doctor_name: str | None
    encounter_id: str | None
    facility_id: str | None
    national_patient_id: str | None
    citizen_id: str | None

    @classmethod
    def query_all(cls, db: Session, lab_id: int | None = None, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        query = db.query(
            LabOrder.id.label("procedure_id"),
            LabOrder.lab_id,
            LabOrder.patient_id,
            LabOrder.id.label("order_id"),
            LabOrder.status.label("procedure_name"),
            LabOrder.status,
            LabOrder.created_at.label("performed_at"),
            LabOrder.created_at,
            LabOrder.doctor_name,
            Encounter.id.label("encounter_id"),
            Encounter.facility_id,
            NationalPatient.id.label("national_patient_id"),
            NationalPatient.citizen_id,
        ).outerjoin(
            NationalPatient,
            and_(
                NationalPatient.lab_patient_id == LabOrder.patient_id,
                NationalPatient.lab_id == LabOrder.lab_id,
            ),
        ).outerjoin(
            Encounter,
            Encounter.patient_id == NationalPatient.id,
        )

        if lab_id is not None:
            query = query.filter(LabOrder.lab_id == lab_id)

        rows = query.order_by(LabOrder.created_at.desc()).offset(skip).limit(limit).all()
        return [dict(row._mapping) for row in rows]

    @classmethod
    def get_by_id(cls, db: Session, procedure_id: int, lab_id: int | None = None) -> dict[str, Any] | None:
        query = db.query(
            LabOrder.id.label("procedure_id"),
            LabOrder.lab_id,
            LabOrder.patient_id,
            LabOrder.id.label("order_id"),
            LabOrder.status.label("procedure_name"),
            LabOrder.status,
            LabOrder.created_at.label("performed_at"),
            LabOrder.created_at,
            LabOrder.doctor_name,
            Encounter.id.label("encounter_id"),
            Encounter.facility_id,
            NationalPatient.id.label("national_patient_id"),
            NationalPatient.citizen_id,
        ).outerjoin(
            NationalPatient,
            and_(
                NationalPatient.lab_patient_id == LabOrder.patient_id,
                NationalPatient.lab_id == LabOrder.lab_id,
            ),
        ).outerjoin(
            Encounter,
            Encounter.patient_id == NationalPatient.id,
        ).filter(
            LabOrder.id == procedure_id,
        )

        if lab_id is not None:
            query = query.filter(LabOrder.lab_id == lab_id)

        row = query.first()
        return dict(row._mapping) if row else None
