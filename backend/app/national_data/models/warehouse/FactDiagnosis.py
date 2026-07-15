from app.national_data.base import BaseEntity
from sqlalchemy import Boolean, Column, Date, ForeignKey, Index, Integer, String


class FactDiagnosis(BaseEntity):
    __tablename__ = "dw_fact_diagnoses"

    dim_patient_id = Column(Integer, ForeignKey("dw_dim_patient.id", ondelete="RESTRICT"), nullable=False, index=True)
    dim_date_id = Column(Integer, ForeignKey("dw_dim_date.id", ondelete="RESTRICT"), nullable=False, index=True)
    dim_diagnosis_id = Column(Integer, ForeignKey("dw_dim_diagnosis.id", ondelete="RESTRICT"), nullable=False, index=True)
    dim_facility_id = Column(Integer, ForeignKey("dw_dim_facility.id", ondelete="RESTRICT"), nullable=True, index=True)
    dim_provider_id = Column(Integer, ForeignKey("dw_dim_provider.id", ondelete="RESTRICT"), nullable=True, index=True)

    diagnosis_type = Column(String(50), nullable=False)
    is_chronic = Column(Boolean, default=False, nullable=False)
    certainty = Column(String(50), nullable=True)

    encounter_type = Column(String(50), nullable=True)
    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True, index=True)

    diagnosis_source_id = Column(String(26), nullable=True)

    diagnosis_date = Column(Date, nullable=True)

    __table_args__ = (
        Index("ix_dw_fact_diag_patient", "dim_patient_id"),
        Index("ix_dw_fact_diag_date", "dim_date_id"),
        Index("ix_dw_fact_diag_diagnosis", "dim_diagnosis_id"),
        Index("ix_dw_fact_diag_chronic", "is_chronic"),
        {"extend_existing": True},
    )
