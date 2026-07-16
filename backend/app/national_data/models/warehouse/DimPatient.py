from sqlalchemy import Column, Date, Index, Integer, String

from app.national_data.base import BaseEntity


class DimPatient(BaseEntity):
    __tablename__ = "dw_dim_patient"

    source_patient_id = Column(Integer, nullable=True)
    national_patient_id = Column(String(26), nullable=True)
    citizen_id = Column(String(26), nullable=True)

    full_name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=True)
    gender = Column(String(1), nullable=True)
    birth_date = Column(Date, nullable=True)
    age_group = Column(String(20), nullable=True)

    governorate = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    nationality = Column(String(100), nullable=True)
    blood_group = Column(String(5), nullable=True)

    lab_id = Column(Integer, nullable=True, index=True)
    is_active = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index("ix_dw_dim_patient_source", "source_patient_id"),
        Index("ix_dw_dim_patient_national", "national_patient_id"),
        Index("ix_dw_dim_patient_lab", "lab_id"),
        {"extend_existing": True},
    )
