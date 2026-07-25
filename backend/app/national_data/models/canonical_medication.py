from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.ehr.models.medication import (
    MedicationAdministration,
    MedicationDispense,
    MedicationRequest,
    MedicationStatement,
)
from app.national.domain.patient import Patient as NationalPatient
from app.national_data.base import DataPlatformBase


class CanonicalMedication(DataPlatformBase):
    __abstract__ = True

    source: str
    medication_id: str
    patient_id: str
    citizen_id: str | None
    encounter_id: str | None
    practitioner_id: str | None
    medication_code: str | None
    medication_name: str
    medication_name_ar: str | None
    status: str
    dosage_text: str | None
    route: str | None
    frequency: str | None
    reason_code: str | None
    started_at: date | None
    ended_at: date | None
    recorded_at: datetime | None
    lab_id: int | None

    @classmethod
    def query_all(
        cls,
        db: Session,
        lab_id: int | None = None,
        patient_lims_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        np_sub = db.query(NationalPatient).subquery()

        stmt_q = db.query(
            MedicationStatement.id.label("medication_id"),
            MedicationStatement.patient_id,
            MedicationStatement.citizen_id,
            MedicationStatement.encounter_id,
            MedicationStatement.practitioner_id,
            MedicationStatement.medication_code,
            MedicationStatement.medication_name,
            MedicationStatement.medication_name_ar,
            MedicationStatement.status,
            MedicationStatement.dosage_text,
            MedicationStatement.route,
            MedicationStatement.frequency,
            MedicationStatement.reason_code,
            MedicationStatement.date_started.label("started_at"),
            MedicationStatement.date_ended.label("ended_at"),
            MedicationStatement.date_recorded.label("recorded_at"),
            np_sub.c.lab_id,
        ).outerjoin(
            np_sub,
            np_sub.c.id == MedicationStatement.patient_id,
        )

        req_q = db.query(
            MedicationRequest.id.label("medication_id"),
            MedicationRequest.patient_id,
            MedicationRequest.citizen_id,
            MedicationRequest.encounter_id,
            MedicationRequest.prescriber_id.label("practitioner_id"),
            MedicationRequest.medication_code,
            MedicationRequest.medication_name,
            MedicationRequest.medication_name_ar,
            MedicationRequest.status,
            MedicationRequest.dosage_instruction.label("dosage_text"),
            MedicationRequest.route,
            MedicationRequest.frequency,
            MedicationRequest.reason_code,
            MedicationRequest.authored_on.label("started_at"),
            MedicationRequest.valid_to.label("ended_at"),
            MedicationRequest.authored_on.label("recorded_at"),
            np_sub.c.lab_id,
        ).outerjoin(
            np_sub,
            np_sub.c.id == MedicationRequest.patient_id,
        )

        disp_q = db.query(
            MedicationDispense.id.label("medication_id"),
            MedicationDispense.patient_id,
            MedicationDispense.citizen_id,
            None.label("encounter_id"),
            MedicationDispense.dispenser_id.label("practitioner_id"),
            MedicationDispense.medication_code,
            MedicationDispense.medication_name,
            MedicationDispense.medication_name_ar,
            MedicationDispense.status,
            MedicationDispense.dosage_instruction.label("dosage_text"),
            MedicationDispense.route,
            MedicationDispense.frequency,
            None.label("reason_code"),
            MedicationDispense.dispensed_at.label("started_at"),
            MedicationDispense.expiry_date.label("ended_at"),
            MedicationDispense.dispensed_at.label("recorded_at"),
            np_sub.c.lab_id,
        ).outerjoin(
            np_sub,
            np_sub.c.id == MedicationDispense.patient_id,
        )

        admin_q = db.query(
            MedicationAdministration.id.label("medication_id"),
            MedicationAdministration.patient_id,
            MedicationAdministration.citizen_id,
            MedicationAdministration.encounter_id,
            MedicationAdministration.administrator_id.label("practitioner_id"),
            MedicationAdministration.medication_code,
            MedicationAdministration.medication_name,
            MedicationAdministration.medication_name_ar,
            MedicationAdministration.status,
            None.label("dosage_text"),
            MedicationAdministration.route,
            None.label("frequency"),
            None.label("reason_code"),
            MedicationAdministration.administration_time.label("started_at"),
            None.label("ended_at"),
            MedicationAdministration.recorded_time.label("recorded_at"),
            np_sub.c.lab_id,
        ).outerjoin(
            np_sub,
            np_sub.c.id == MedicationAdministration.patient_id,
        )

        union_q = stmt_q.union_all(req_q, disp_q, admin_q).subquery()

        query = db.query(union_q).select_entity_from(union_q)

        if lab_id is not None:
            query = query.filter(union_q.c.lab_id == lab_id)

        rows = (
            query.order_by(union_q.c.recorded_at.desc().nullslast()).offset(skip).limit(limit).all()
        )
        return [dict(row._mapping) for row in rows]
