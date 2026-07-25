from sqlalchemy import JSON, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SAEnum

from app.national.base import TenantAuditEntity
from app.national.enums import EpisodeOfCareStatus


class EpisodeOfCare(TenantAuditEntity):
    __tablename__ = "national_episodes_of_care"

    status = Column(
        SAEnum(EpisodeOfCareStatus), nullable=False, default=EpisodeOfCareStatus.PLANNED,
    )

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

    organization_id = Column(
        String(26),
        ForeignKey("national_organizations.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    care_manager_id = Column(
        String(26),
        ForeignKey("national_practitioners.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )

    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=True)

    diagnosis_code = Column(String(50), nullable=True)
    diagnosis_description = Column(Text, nullable=True)
    icd10_code = Column(String(20), nullable=True)

    team = Column(JSON, nullable=True)
    goals = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_national_eoc_patient", "patient_id"),
        Index("ix_national_eoc_citizen", "citizen_id"),
        {"extend_existing": True},
    )
