from sqlalchemy import Boolean, Column, Date, ForeignKey, Index, Integer, String, Text
from sqlalchemy import Enum as SAEnum

from app.national.base import TenantAuditEntity
from app.national.enums import CoverageStatus


class Coverage(TenantAuditEntity):
    __tablename__ = "national_coverages"

    status = Column(SAEnum(CoverageStatus), nullable=False, default=CoverageStatus.ACTIVE)

    patient_id = Column(
        String(26),
        ForeignKey("national_patients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    citizen_id = Column(
        String(26),
        ForeignKey("national_citizens.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    insurance_id = Column(
        String(26),
        ForeignKey("national_insurances.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    policy_number = Column(String(100), nullable=False, index=True)
    group_number = Column(String(100), nullable=True)
    subscriber_id = Column(String(100), nullable=True)
    subscriber_name = Column(String(200), nullable=True)

    relationship_to_subscriber = Column(String(50), nullable=True)
    coverage_type = Column(String(50), nullable=True)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    copay_percentage = Column(Integer, nullable=True)
    deductible = Column(Integer, nullable=True)
    max_out_of_pocket = Column(Integer, nullable=True)

    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_coverages_patient", "patient_id"),
        Index("ix_national_coverages_insurance", "insurance_id"),
        Index("ix_national_coverages_policy", "policy_number"),
        Index("ix_national_coverages_period", "start_date", "end_date"),
        {"extend_existing": True},
    )
