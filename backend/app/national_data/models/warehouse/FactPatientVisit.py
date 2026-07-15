from app.national_data.base import BaseEntity
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String


class FactPatientVisit(BaseEntity):
    __tablename__ = "dw_fact_patient_visits"

    dim_patient_id = Column(Integer, ForeignKey("dw_dim_patient.id", ondelete="RESTRICT"), nullable=False, index=True)
    dim_date_id = Column(Integer, ForeignKey("dw_dim_date.id", ondelete="RESTRICT"), nullable=False, index=True)
    dim_facility_id = Column(Integer, ForeignKey("dw_dim_facility.id", ondelete="RESTRICT"), nullable=True, index=True)
    dim_provider_id = Column(Integer, ForeignKey("dw_dim_provider.id", ondelete="RESTRICT"), nullable=True, index=True)
    dim_diagnosis_id = Column(Integer, ForeignKey("dw_dim_diagnosis.id", ondelete="RESTRICT"), nullable=True, index=True)

    encounter_type = Column(String(50), nullable=False)
    visit_status = Column(String(20), nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    is_emergency = Column(Integer, default=0, nullable=False)

    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True, index=True)
    encounter_source_id = Column(String(26), nullable=True)

    visit_date = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_dw_fact_visit_patient", "dim_patient_id"),
        Index("ix_dw_fact_visit_date", "dim_date_id"),
        Index("ix_dw_fact_visit_facility", "dim_facility_id"),
        Index("ix_dw_fact_visit_lab", "lab_id"),
        {"extend_existing": True},
    )
