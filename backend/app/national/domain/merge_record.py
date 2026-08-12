from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy import Enum as SAEnum

from app.national.base import AuditEntity
from app.national.enums import MergeMethod, MergeStatus


class MergeRecord(AuditEntity):
    __tablename__ = "national_merge_records"

    status = Column(SAEnum(MergeStatus), nullable=False, default=MergeStatus.PENDING)
    method = Column(SAEnum(MergeMethod), nullable=False)

    primary_citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=False, index=True)
    secondary_citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=False, index=True)

    confidence_score = Column(Integer, nullable=True)
    match_features = Column(JSON, nullable=True)

    requested_by = Column(String(26), nullable=False)
    approved_by = Column(String(26), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(String(26), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    completed_at = Column(DateTime(timezone=True), nullable=True)
    is_auto_merge = Column(Boolean, default=False)
    requires_human_approval = Column(Boolean, default=True)

    notes = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_merge_records_primary", "primary_citizen_id"),
        Index("ix_national_merge_records_secondary", "secondary_citizen_id"),
        Index("ix_national_merge_records_status", "status"),
        {"extend_existing": True},
    )


class MergeAudit(AuditEntity):
    __tablename__ = "national_merge_audit"

    event_type = Column(String(20), nullable=False)
    merge_record_id = Column(String(26), ForeignKey("national_merge_records.id", ondelete="RESTRICT"), nullable=True, index=True)

    primary_citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=False, index=True)
    secondary_citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)

    action = Column(String(50), nullable=False)
    performed_by = Column(String(26), nullable=False)
    performed_at = Column(DateTime(timezone=True), nullable=False)

    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)

    prev_hash = Column(String(64), nullable=True)
    entry_hash = Column(String(64), nullable=False, unique=True)

    __table_args__ = (
        Index("ix_national_merge_audit_primary", "primary_citizen_id"),
        Index("ix_national_merge_audit_secondary", "secondary_citizen_id"),
        Index("ix_national_merge_audit_performed", "performed_at"),
        {"extend_existing": True},
    )
