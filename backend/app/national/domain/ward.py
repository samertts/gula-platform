from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String

from app.national.base import AuditEntity


class Ward(AuditEntity):
    __tablename__ = "national_wards"

    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    code = Column(String(20), nullable=True, index=True)

    hospital_id = Column(String(26), ForeignKey("national_hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)

    ward_type = Column(String(50), nullable=False)
    bed_count = Column(Integer, default=0)
    available_beds = Column(Integer, default=0)
    phone = Column(String(20), nullable=True)

    is_active = Column(Boolean, default=True)
    is_emergency_ward = Column(Boolean, default=False)
    is_icu = Column(Boolean, default=False)
    isolation_capable = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_national_wards_hospital", "hospital_id"),
        Index("ix_national_wards_facility", "facility_id"),
        {"extend_existing": True},
    )
