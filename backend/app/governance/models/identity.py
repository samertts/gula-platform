from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text

from app._compat import UTC

from ..base import GovernanceBaseEntity


class GovernanceIdentityRecord(GovernanceBaseEntity):
    __tablename__ = "gov_identity_records"

    id = Column(String(36), primary_key=True)
    health_number = Column(String(50), unique=True, nullable=False, index=True)
    national_id_hash = Column(String(255), nullable=True, index=True)
    full_name = Column(String(300), nullable=False)
    date_of_birth = Column(DateTime(timezone=True), nullable=True)
    gender = Column(String(20), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(200), nullable=True)
    address = Column(Text, nullable=True)
    identity_type = Column(String(30), nullable=False, default="citizen", index=True)
    identity_status = Column(String(20), nullable=False, default="active")
    documents_json = Column(JSON, nullable=True)
    relationships_json = Column(JSON, nullable=True)
    history_json = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class GovernanceBreakGlassAccess(GovernanceBaseEntity):
    __tablename__ = "gov_break_glass_accesses"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(100), nullable=False, index=True)
    user_name = Column(String(200), nullable=True)
    user_role = Column(String(50), nullable=True)
    reason = Column(String(50), nullable=False)
    reason_detail = Column(Text, nullable=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)
    patient_id = Column(String(36), nullable=True, index=True)
    accessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class MergeProposal(GovernanceBaseEntity):
    __tablename__ = "gov_merge_proposals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    proposal_key = Column(String(200), unique=True, nullable=False, index=True)
    primary_hn = Column(String(50), nullable=False, index=True)
    duplicate_hn = Column(String(50), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False, default=0.0)
    matched_fields = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    reviewed_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    resolved_at = Column(DateTime(timezone=True), nullable=True)
