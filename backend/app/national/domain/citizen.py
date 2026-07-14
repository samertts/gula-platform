from datetime import datetime

from app._compat import UTC
from app.national.base import BaseEntity
from app.national.enums import Gender, IdentityStatus, MaritalStatus
from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Enum as SAEnum, Index, Integer, SmallInteger, String


class Citizen(BaseEntity):
    __tablename__ = "national_citizens"

    national_id_hash = Column(String(255), nullable=True, unique=True)
    national_id_verified = Column(Boolean, default=False, nullable=False)
    health_number = Column(String(20), nullable=False, unique=True, index=True)

    first_name = Column(String(100), nullable=False)
    father_name = Column(String(100), nullable=True)
    grandfather_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False)
    mother_name = Column(String(100), nullable=True)
    full_name_ar = Column(String(400), nullable=True)
    full_name_en = Column(String(400), nullable=True)

    date_of_birth = Column(Date, nullable=False)
    birth_year = Column(SmallInteger, nullable=True)
    birth_month = Column(SmallInteger, nullable=True)
    birth_day = Column(SmallInteger, nullable=True)
    gender = Column(SAEnum(Gender), nullable=False)
    marital_status = Column(SAEnum(MaritalStatus), default=MaritalStatus.UNKNOWN)
    blood_group = Column(String(5), nullable=True)

    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    photo_url = Column(String(500), nullable=True)

    governorate = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    subdistrict = Column(String(100), nullable=True)
    locality = Column(String(200), nullable=True)
    street = Column(String(200), nullable=True)
    building = Column(String(50), nullable=True)

    nationality = Column(String(100), default="Iraqi")
    language = Column(String(10), default="ar")
    occupation = Column(String(200), nullable=True)

    identity_status = Column(SAEnum(IdentityStatus), default=IdentityStatus.ACTIVE, nullable=False)
    merged_into_id = Column(String(26), nullable=True, index=True)
    is_deceased = Column(Boolean, default=False)
    deceased_date = Column(DateTime(timezone=True), nullable=True)

    biometrics_enrolled = Column(Boolean, default=False)
    has_health_card = Column(Boolean, default=False)
    is_vip = Column(Boolean, default=False)
    is_restricted = Column(Boolean, default=False)

    external_id = Column(String(255), nullable=True)
    external_system = Column(String(50), nullable=True)

    name_blocking_key = Column(String(20), nullable=True, index=True)
    phone_last10 = Column(String(10), nullable=True, index=True)
    family_id_hash = Column(String(255), nullable=True, index=True)

    tags = Column(JSON, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    version = Column(Integer, default=1, nullable=False)

    __table_args__ = (
        Index("ix_national_citizens_health_number", "health_number"),
        Index("ix_national_citizens_name_blocking", "name_blocking_key", "birth_year", "gender"),
        Index("ix_national_citizens_identity_status", "identity_status"),
        Index("ix_national_citizens_merged", "merged_into_id"),
        {"extend_existing": True},
    )

    @property
    def full_name(self) -> str:
        parts = [p for p in [self.first_name, self.father_name, self.last_name] if p]
        return " ".join(parts)

    @property
    def is_iraqi(self) -> bool:
        return self.nationality == "Iraqi" or self.nationality is None

    def mark_deceased(self, date: datetime | None = None) -> None:
        self.is_deceased = True
        self.identity_status = IdentityStatus.DECEASED
        self.deceased_date = date or datetime.now(UTC)

    def merge_into(self, target_id: str) -> None:
        self.merged_into_id = target_id
        self.identity_status = IdentityStatus.MERGED
