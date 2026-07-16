from sqlalchemy import Boolean, Column, DateTime, Index, String, Text

from app.national.base import BaseEntity


class NationalIdentifierMapping(BaseEntity):
    __tablename__ = "national_identifier_mappings"

    citizen_id = Column(String(26), nullable=False, index=True)
    national_id_hash = Column(String(255), nullable=False, index=True)
    national_id_algorithm = Column(String(20), nullable=False)

    is_primary = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by_system = Column(String(100), nullable=True)

    effective_start = Column(DateTime(timezone=True), nullable=False)
    effective_end = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_id_mappings_citizen", "citizen_id"),
        Index("ix_national_id_mappings_hash", "national_id_hash"),
        {"extend_existing": True},
    )
