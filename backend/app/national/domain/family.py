from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SAEnum

from app.national.base import TenantAuditEntity
from app.national.enums import FamilyRelationshipType


class Family(TenantAuditEntity):
    __tablename__ = "national_families"

    family_id_hash = Column(String(255), nullable=False, unique=True, index=True)
    family_name = Column(String(200), nullable=True)
    family_name_ar = Column(String(200), nullable=True)

    family_type = Column(String(50), nullable=True)
    ration_card_number = Column(String(50), nullable=True, index=True)
    ration_card_governorate = Column(String(100), nullable=True)
    ration_card_district = Column(String(100), nullable=True)

    head_of_family_citizen_id = Column(
        String(26),
        ForeignKey("national_citizens.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    head_of_family_name = Column(String(200), nullable=True)

    governorate = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    subdistrict = Column(String(100), nullable=True)
    address_line = Column(String(500), nullable=True)

    is_active = Column(Boolean, default=True)
    is_historical = Column(Boolean, default=False)
    merged_into_family_id = Column(String(26), nullable=True, index=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_families_head", "head_of_family_citizen_id"),
        Index("ix_national_families_ration_card", "ration_card_number"),
        Index("ix_national_families_merged", "merged_into_family_id"),
        {"extend_existing": True},
    )


class FamilyMember(TenantAuditEntity):
    __tablename__ = "national_family_members"

    family_id = Column(
        String(26),
        ForeignKey("national_families.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    citizen_id = Column(
        String(26),
        ForeignKey("national_citizens.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    relationship = Column(SAEnum(FamilyRelationshipType), nullable=False)
    is_head_of_family = Column(Boolean, default=False)

    is_dependent = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime(timezone=True), nullable=True)
    left_at = Column(DateTime(timezone=True), nullable=True)
    is_historical = Column(Boolean, default=False)

    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_family_members_citizen", "citizen_id"),
        Index("ix_national_family_members_family_citizen", "family_id", "citizen_id", unique=True),
        {"extend_existing": True},
    )
