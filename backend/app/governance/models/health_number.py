from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text

from app._compat import UTC

from ..base import GovernanceBaseEntity
from ..enums import CardLifecycleEvent, HealthCardType, HealthNumberStatus, IdentityMergeAction


class HealthNumberRecord(GovernanceBaseEntity):
    __tablename__ = "gov_health_numbers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    health_number = Column(String(50), unique=True, nullable=False, index=True)
    citizen_ulid = Column(String(26), nullable=False, index=True)
    national_id_hash = Column(String(255), nullable=True, index=True)
    status = Column(Enum(HealthNumberStatus), nullable=False, default=HealthNumberStatus.ACTIVE, index=True)
    issued_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    activated_at = Column(DateTime(timezone=True), nullable=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    is_public = Column(Boolean, default=True)
    is_printed = Column(Boolean, default=False)
    barcode_data = Column(String(500), nullable=True)
    qr_code_data = Column(Text, nullable=True)
    previous_health_number = Column(String(50), nullable=True, index=True)
    merged_into_health_number = Column(String(50), nullable=True, index=True)
    metadata_json = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class HealthNumberAudit(GovernanceBaseEntity):
    __tablename__ = "gov_health_number_audit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    health_number = Column(String(50), nullable=False, index=True)
    event = Column(String(50), nullable=False)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    changed_by = Column(String(200), nullable=True)
    reason = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class HealthCardLifecycle(GovernanceBaseEntity):
    __tablename__ = "gov_health_cards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    health_number = Column(String(50), nullable=False, index=True)
    citizen_ulid = Column(String(26), nullable=False, index=True)
    card_type = Column(Enum(HealthCardType), nullable=False)
    card_number = Column(String(100), unique=True, nullable=False, index=True)
    event = Column(Enum(CardLifecycleEvent), nullable=False, index=True)
    previous_card_number = Column(String(100), nullable=True)
    reason = Column(Text, nullable=True)
    issued_by = Column(String(200), nullable=True)
    issued_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    metadata_json = Column(String(1000), nullable=True)


class MergedIdentityRecord(GovernanceBaseEntity):
    __tablename__ = "gov_merged_identities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    primary_health_number = Column(String(50), nullable=False, index=True)
    secondary_health_number = Column(String(50), nullable=False, index=True)
    primary_citizen_ulid = Column(String(26), nullable=False, index=True)
    secondary_citizen_ulid = Column(String(26), nullable=False, index=True)
    action = Column(Enum(IdentityMergeAction), nullable=False, index=True)
    reason = Column(Text, nullable=True)
    decision_by = Column(String(200), nullable=True)
    occurred_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    historical_data_json = Column(Text, nullable=True)
    is_historical_link = Column(Boolean, default=False)
