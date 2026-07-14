from app.national.base import TenantAuditEntity
from app.national.enums import Gender, MaritalStatus
from sqlalchemy import JSON, Boolean, Column, Date, Enum as SAEnum, ForeignKey, Index, Integer, SmallInteger, String


class Patient(TenantAuditEntity):
    __tablename__ = "national_patients"

    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    health_number = Column(String(20), nullable=False, index=True)
    lab_patient_id = Column(Integer, nullable=True)

    first_name = Column(String(100), nullable=False)
    father_name = Column(String(100), nullable=True)
    grandfather_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False)
    mother_name = Column(String(100), nullable=True)
    full_name = Column(String(400), nullable=True)

    date_of_birth = Column(Date, nullable=False)
    birth_year = Column(SmallInteger, nullable=True)
    birth_month = Column(SmallInteger, nullable=True)
    birth_day = Column(SmallInteger, nullable=True)
    gender = Column(SAEnum(Gender), nullable=False)
    marital_status = Column(SAEnum(MaritalStatus), default=MaritalStatus.UNKNOWN)
    blood_group = Column(String(5), nullable=True)

    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    governorate = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    subdistrict = Column(String(100), nullable=True)
    address_line = Column(String(500), nullable=True)

    nationality = Column(String(100), default="Iraqi")
    language = Column(String(10), default="ar")

    is_active = Column(Boolean, default=True)
    has_guardian = Column(Boolean, default=False)
    guardian_id = Column(String(26), ForeignKey("national_guardians.id", ondelete="SET NULL"), nullable=True, index=True)
    is_merged = Column(Boolean, default=False)
    merged_into_patient_id = Column(String(26), nullable=True)

    identity_type = Column(String(20), nullable=True)
    identity_number_hash = Column(String(255), nullable=True)
    family_id_hash = Column(String(255), nullable=True, index=True)

    tags = Column(JSON, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_national_patients_lab_health_number", "lab_id", "health_number", unique=True),
        Index("ix_national_patients_lab_citizen", "lab_id", "citizen_id"),
        Index("ix_national_patients_guardian", "guardian_id"),
        Index("ix_national_patients_family", "family_id_hash"),
        {"extend_existing": True},
    )
