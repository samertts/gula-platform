from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy import Enum as SAEnum

from app.national.base import AuditEntity
from app.national.enums import BiometricType


class BiometricRecord(AuditEntity):
    __tablename__ = "national_biometrics"

    biometric_type = Column(SAEnum(BiometricType), nullable=False)
    citizen_id = Column(
        String(26),
        ForeignKey("national_citizens.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    data_hash = Column(String(255), nullable=False)
    data_url = Column(String(1000), nullable=True)
    quality_score = Column(Integer, nullable=True)

    captured_at = Column(DateTime(timezone=True), nullable=False)
    captured_by = Column(String(26), nullable=True)
    captured_by_device = Column(String(200), nullable=True)

    is_primary = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(26), nullable=True)

    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1, nullable=False)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_biometrics_citizen", "citizen_id"),
        Index("ix_national_biometrics_type", "biometric_type"),
        {"extend_existing": True},
    )
