from app.national_data.base import BaseEntity
from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String


class FactLabResult(BaseEntity):
    __tablename__ = "dw_fact_lab_results"

    dim_patient_id = Column(Integer, ForeignKey("dw_dim_patient.id", ondelete="RESTRICT"), nullable=False, index=True)
    dim_date_id = Column(Integer, ForeignKey("dw_dim_date.id", ondelete="RESTRICT"), nullable=False, index=True)
    dim_facility_id = Column(Integer, ForeignKey("dw_dim_facility.id", ondelete="RESTRICT"), nullable=True, index=True)
    dim_provider_id = Column(Integer, ForeignKey("dw_dim_provider.id", ondelete="RESTRICT"), nullable=True, index=True)

    test_name = Column(String(200), nullable=False)
    test_code = Column(String(50), nullable=True, index=True)

    result_value_numeric = Column(Float, nullable=True)
    result_value_text = Column(String(500), nullable=True)
    result_unit = Column(String(50), nullable=True)
    result_flag = Column(String(10), nullable=True)

    normal_range_low = Column(Float, nullable=True)
    normal_range_high = Column(Float, nullable=True)
    is_abnormal = Column(Integer, default=0, nullable=False)
    is_critical = Column(Integer, default=0, nullable=False)

    lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True, index=True)
    result_source_id = Column(Integer, nullable=True)

    result_date = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_dw_fact_result_patient", "dim_patient_id"),
        Index("ix_dw_fact_result_date", "dim_date_id"),
        Index("ix_dw_fact_result_test", "test_code"),
        Index("ix_dw_fact_result_abnormal", "is_abnormal"),
        Index("ix_dw_fact_result_lab", "lab_id"),
        {"extend_existing": True},
    )
