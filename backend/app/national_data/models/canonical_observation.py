from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.lab_order import LabOrder
from app.models.lab_result import LabResult
from app.models.patient import Patient
from app.national.domain.encounter import Encounter
from app.national.domain.patient import Patient as NationalPatient
from app.national_data.base import DataPlatformBase


class CanonicalObservation(DataPlatformBase):
    __abstract__ = True

    id: int
    lab_id: int
    patient_id: int
    order_id: int
    test_name: str
    test_code: str | None
    value: str | None
    value_text: str | None
    value_numeric: float | None
    unit: str | None
    flag: str | None
    reference_range: str | None
    normal_range_low: str | None
    normal_range_high: str | None
    result_status: str | None
    observed_at: datetime | None
    created_at: datetime | None

    encounter_id: str | None
    practitioner_id: str | None
    facility_id: str | None
    national_patient_id: str | None
    citizen_id: str | None

    @classmethod
    def query_all(cls, db: Session, lab_id: int | None = None, patient_id: int | None = None, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        query = db.query(
            LabResult.id,
            LabResult.lab_id,
            LabResult.patient_id,
            LabResult.order_id,
            LabResult.test_name,
            LabResult.test_code,
            LabResult.value,
            LabResult.value_text,
            LabResult.value_numeric,
            LabResult.unit,
            LabResult.flag,
            LabResult.reference_range,
            LabResult.normal_range_low,
            LabResult.normal_range_high,
            LabResult.result_status,
            LabResult.observed_at,
            LabResult.created_at,
            Encounter.id.label("encounter_id"),
            Encounter.practitioner_id,
            Encounter.facility_id,
            NationalPatient.id.label("national_patient_id"),
            NationalPatient.citizen_id,
        ).outerjoin(
            Patient, Patient.id == LabResult.patient_id,
        ).outerjoin(
            NationalPatient,
            and_(
                NationalPatient.lab_patient_id == Patient.id,
                NationalPatient.lab_id == LabResult.lab_id,
            ),
        ).outerjoin(
            LabOrder, LabOrder.id == LabResult.order_id,
        ).outerjoin(
            Encounter,
            and_(
                Encounter.patient_id == NationalPatient.id,
            ),
        )

        if lab_id is not None:
            query = query.filter(LabResult.lab_id == lab_id)

        if patient_id is not None:
            query = query.filter(LabResult.patient_id == patient_id)

        rows = query.order_by(LabResult.created_at.desc().nullslast()).offset(skip).limit(limit).all()
        return [dict(row._mapping) for row in rows]

    @classmethod
    def get_by_id(cls, db: Session, observation_id: int, lab_id: int | None = None) -> dict[str, Any] | None:
        query = db.query(
            LabResult.id,
            LabResult.lab_id,
            LabResult.patient_id,
            LabResult.order_id,
            LabResult.test_name,
            LabResult.test_code,
            LabResult.value,
            LabResult.value_text,
            LabResult.value_numeric,
            LabResult.unit,
            LabResult.flag,
            LabResult.reference_range,
            LabResult.normal_range_low,
            LabResult.normal_range_high,
            LabResult.result_status,
            LabResult.observed_at,
            LabResult.created_at,
            Encounter.id.label("encounter_id"),
            Encounter.practitioner_id,
            Encounter.facility_id,
            NationalPatient.id.label("national_patient_id"),
            NationalPatient.citizen_id,
        ).outerjoin(
            Patient, Patient.id == LabResult.patient_id,
        ).outerjoin(
            NationalPatient,
            and_(
                NationalPatient.lab_patient_id == Patient.id,
                NationalPatient.lab_id == LabResult.lab_id,
            ),
        ).outerjoin(
            LabOrder, LabOrder.id == LabResult.order_id,
        ).outerjoin(
            Encounter,
            and_(
                Encounter.patient_id == NationalPatient.id,
            ),
        ).filter(
            LabResult.id == observation_id,
        )

        if lab_id is not None:
            query = query.filter(LabResult.lab_id == lab_id)

        row = query.first()
        return dict(row._mapping) if row else None
