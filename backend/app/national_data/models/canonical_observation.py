from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import and_, null
from sqlalchemy.orm import Session

from app.models.lab_order import LabOrder
from app.models.lab_result import LabResult
from app.models.patient import Patient
from app.models.test_type import TestType
from app.national.domain.encounter import Encounter
from app.national.domain.patient import Patient as NationalPatient
from app.national_data.base import DataPlatformBase


# ``LabResult`` is a slim model: it has no ``lab_id``, ``patient_id``, ``test_code``,
# ``value_numeric``, ``reference_range``, ``result_status`` or ``observed_at``. This
# projection was written against a LabResult that does not exist, so every attribute
# access raised AttributeError and both queries below were dead.
#
# The tenant and patient keys come from the order the result belongs to
# (LabResult.order_id -> LabOrder.lab_id / LabOrder.patient_id), which is how a result
# is scoped everywhere else in the platform. ``test_code`` comes from the test type.
#
# ``result_status``, ``observed_at`` and ``reference_range`` are exposed as NULL rather
# than substituted: FHIR Observation.status and effective time are clinical statements
# about the observation, and LabOrder.status / LabResult.created_at are not the same
# facts. A national feed must not assert them. Supplying them is a data-contract
# decision for the national data owner — see NR-046.
def _observation_query(db: Session):
    """The canonical observation projection, joined from the order outwards."""
    return (
        db.query(
            LabResult.id,
            LabOrder.lab_id,
            LabOrder.patient_id,
            LabResult.order_id,
            LabResult.test_name,
            TestType.test_code.label("test_code"),
            LabResult.value,
            LabResult.value_text,
            LabResult.value.label("value_numeric"),
            LabResult.unit,
            LabResult.flag,
            null().label("reference_range"),
            LabResult.normal_range_low,
            LabResult.normal_range_high,
            null().label("result_status"),
            null().label("observed_at"),
            LabResult.created_at,
            Encounter.id.label("encounter_id"),
            Encounter.practitioner_id,
            Encounter.facility_id,
            NationalPatient.id.label("national_patient_id"),
            NationalPatient.citizen_id,
        )
        .outerjoin(LabOrder, LabOrder.id == LabResult.order_id)
        .outerjoin(TestType, TestType.id == LabResult.test_type_id)
        .outerjoin(Patient, Patient.id == LabOrder.patient_id)
        .outerjoin(
            NationalPatient,
            and_(
                NationalPatient.lab_patient_id == Patient.id,
                NationalPatient.lab_id == LabOrder.lab_id,
            ),
        )
        .outerjoin(Encounter, Encounter.patient_id == NationalPatient.id)
    )


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
        query = _observation_query(db)

        if lab_id is not None:
            query = query.filter(LabOrder.lab_id == lab_id)

        if patient_id is not None:
            query = query.filter(LabOrder.patient_id == patient_id)

        rows = query.order_by(LabResult.created_at.desc().nullslast()).offset(skip).limit(limit).all()
        return [dict(row._mapping) for row in rows]

    @classmethod
    def get_by_id(cls, db: Session, observation_id: int, lab_id: int | None = None) -> dict[str, Any] | None:
        query = _observation_query(db).filter(LabResult.id == observation_id)

        if lab_id is not None:
            query = query.filter(LabOrder.lab_id == lab_id)

        row = query.first()
        return dict(row._mapping) if row else None
