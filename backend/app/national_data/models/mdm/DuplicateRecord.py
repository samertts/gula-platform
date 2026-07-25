from sqlalchemy import Column, Float, ForeignKey, Index, Integer, String, Text

from app.national_data.base import BaseEntity


class DuplicateRecord(BaseEntity):
    __tablename__ = "dp_duplicate_records"

    golden_record_id = Column(
        Integer, ForeignKey("dp_golden_records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_patient_id = Column(
        Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True
    )
    source_national_patient_id = Column(String(26), nullable=True)
    source_system = Column(String(50), nullable=False)

    duplicate_probability = Column(Float, default=0.0, nullable=False)
    matching_algorithm = Column(String(100), nullable=True)
    matched_fields = Column(Text, nullable=True)
    match_details = Column(Text, nullable=True)

    status = Column(String(20), default="pending", nullable=False, index=True)
    resolution = Column(String(50), nullable=True)

    __table_args__ = (
        Index("ix_dp_duplicate_golden", "golden_record_id"),
        Index("ix_dp_duplicate_status", "status"),
        {"extend_existing": True},
    )
