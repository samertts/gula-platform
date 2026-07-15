from __future__ import annotations

from datetime import date
from typing import Any, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.database import Base
from app.models.patient import Patient as LimsPatient
from app.national.domain.citizen import Citizen
from app.national.domain.patient import Patient as NationalPatient


class CanonicalPatient(Base):
    __abstract__ = True

    id: int
    lab_id: int
    health_id: Optional[str]
    national_id_hash: Optional[str]
    family_id_hash: Optional[str]
    full_name: str
    phone: str
    birth_date: Optional[date]
    gender: Optional[str]
    email: Optional[str]
    guardian_id: Optional[int]

    national_patient_id: Optional[str]
    citizen_id: Optional[str]
    first_name: Optional[str]
    father_name: Optional[str]
    grandfather_name: Optional[str]
    last_name: Optional[str]
    mother_name: Optional[str]
    full_name_ar: Optional[str]
    date_of_birth: Optional[date]
    blood_group: Optional[str]
    governorate: Optional[str]
    district: Optional[str]
    nationality: Optional[str]

    @classmethod
    def query_all(cls, db: Session, lab_id: int | None = None, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        query = db.query(
            LimsPatient.id,
            LimsPatient.lab_id,
            LimsPatient.health_id,
            LimsPatient.national_id_hash,
            LimsPatient.family_id_hash,
            LimsPatient.full_name,
            LimsPatient.phone,
            LimsPatient.birth_date,
            LimsPatient.gender,
            LimsPatient.email,
            LimsPatient.guardian_id,
            NationalPatient.id.label("national_patient_id"),
            Citizen.id.label("citizen_id"),
            Citizen.first_name,
            Citizen.father_name,
            Citizen.grandfather_name,
            Citizen.last_name,
            Citizen.mother_name,
            Citizen.full_name_ar,
            Citizen.date_of_birth,
            Citizen.blood_group,
            Citizen.governorate,
            Citizen.district,
            Citizen.nationality,
        ).outerjoin(
            NationalPatient,
            and_(
                NationalPatient.lab_patient_id == LimsPatient.id,
                NationalPatient.lab_id == LimsPatient.lab_id,
            ),
        ).outerjoin(
            Citizen,
            Citizen.id == NationalPatient.citizen_id,
        )

        if lab_id is not None:
            query = query.filter(LimsPatient.lab_id == lab_id)

        rows = query.offset(skip).limit(limit).all()
        return [dict(row._mapping) for row in rows]

    @classmethod
    def get_by_id(cls, db: Session, patient_id: int, lab_id: int | None = None) -> dict[str, Any] | None:
        query = db.query(
            LimsPatient.id,
            LimsPatient.lab_id,
            LimsPatient.health_id,
            LimsPatient.national_id_hash,
            LimsPatient.family_id_hash,
            LimsPatient.full_name,
            LimsPatient.phone,
            LimsPatient.birth_date,
            LimsPatient.gender,
            LimsPatient.email,
            LimsPatient.guardian_id,
            NationalPatient.id.label("national_patient_id"),
            Citizen.id.label("citizen_id"),
            Citizen.first_name,
            Citizen.father_name,
            Citizen.grandfather_name,
            Citizen.last_name,
            Citizen.mother_name,
            Citizen.full_name_ar,
            Citizen.date_of_birth,
            Citizen.blood_group,
            Citizen.governorate,
            Citizen.district,
            Citizen.nationality,
        ).outerjoin(
            NationalPatient,
            and_(
                NationalPatient.lab_patient_id == LimsPatient.id,
                NationalPatient.lab_id == LimsPatient.lab_id,
            ),
        ).outerjoin(
            Citizen,
            Citizen.id == NationalPatient.citizen_id,
        ).filter(
            LimsPatient.id == patient_id,
        )

        if lab_id is not None:
            query = query.filter(LimsPatient.lab_id == lab_id)

        row = query.first()
        return dict(row._mapping) if row else None
