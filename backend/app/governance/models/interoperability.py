from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, Date, DateTime, Enum, Integer, String, Text

from app._compat import UTC

from ..base import GovernanceBaseEntity
from ..enums import InteropProtocolStatus, InteropProtocolType


def _interop_values(enum_class):
    return [e.value for e in enum_class]


class InteropProtocol(GovernanceBaseEntity):
    __tablename__ = "gov_interop_protocols"

    id = Column(Integer, primary_key=True, autoincrement=True)
    protocol_code = Column(String(50), unique=True, nullable=False, index=True)
    name_ar = Column(String(300), nullable=False)
    name_en = Column(String(300), nullable=True)
    protocol_type = Column(
        Enum(InteropProtocolType, values_callable=_interop_values), nullable=False, index=True
    )
    version = Column(String(20), nullable=False, default="1.0")
    status = Column(
        Enum(InteropProtocolStatus), nullable=False, default=InteropProtocolStatus.DRAFT, index=True
    )
    specification_url = Column(String(500), nullable=True)
    profile = Column(String(200), nullable=True)
    implementation_guide = Column(Text, nullable=True)
    security_profile = Column(String(200), nullable=True)
    is_mandatory = Column(Boolean, default=False)
    effective_date = Column(Date, nullable=True)
    review_date = Column(Date, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class MasterDataAgreement(GovernanceBaseEntity):
    __tablename__ = "gov_master_data_agreements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agreement_code = Column(String(50), unique=True, nullable=False, index=True)
    name_ar = Column(String(300), nullable=False)
    name_en = Column(String(300), nullable=True)
    domain = Column(String(100), nullable=False, index=True)
    source_system = Column(String(200), nullable=False)
    target_system = Column(String(200), nullable=False)
    status = Column(String(20), default="active", index=True)
    version = Column(String(20), default="1.0")
    mapping_rules = Column(JSON, nullable=True)
    sync_frequency = Column(String(50), nullable=True)
    conflict_resolution = Column(String(100), nullable=True)
    effective_date = Column(Date, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class TerminologyMapping(GovernanceBaseEntity):
    __tablename__ = "gov_terminology_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_system = Column(String(200), nullable=False)
    source_code = Column(String(100), nullable=False, index=True)
    source_display = Column(String(300), nullable=True)
    target_system = Column(String(200), nullable=False)
    target_code = Column(String(100), nullable=False, index=True)
    target_display = Column(String(300), nullable=True)
    mapping_type = Column(String(50), nullable=False)
    equivalence = Column(String(20), default="equivalent")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class CanonicalMapping(GovernanceBaseEntity):
    __tablename__ = "gov_canonical_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_type = Column(String(100), nullable=False, index=True)
    source_system = Column(String(200), nullable=False)
    source_field = Column(String(200), nullable=False)
    canonical_field = Column(String(200), nullable=False)
    transformation = Column(String(500), nullable=True)
    is_required = Column(Boolean, default=False)
    data_type = Column(String(50), nullable=True)
    validation_rules = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
