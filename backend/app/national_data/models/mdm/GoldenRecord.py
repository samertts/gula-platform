from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text

from app.national_data.base import BaseEntity


class GoldenRecord(BaseEntity):
    __tablename__ = "dp_golden_records"

    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True)
    national_patient_id = Column(String(26), nullable=True, index=True)
    citizen_id = Column(String(26), nullable=True, index=True)

    confidence_score = Column(Float, default=0.0, nullable=False)
    matching_algorithm = Column(String(100), nullable=True)
    matched_fields = Column(Text, nullable=True)
    merge_history = Column(Text, nullable=True)

    is_active_golden = Column(Integer, default=1, nullable=False)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)

    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_dp_golden_patient", "patient_id"),
        Index("ix_dp_golden_national_patient", "national_patient_id"),
        Index("ix_dp_golden_citizen", "citizen_id"),
        Index("ix_dp_golden_active", "is_active_golden", "patient_id"),
        {"extend_existing": True},
    )
