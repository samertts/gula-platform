from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app.identity.base import IdentityBaseEntity


class NiamHealthIdentityOperation(IdentityBaseEntity):
    """Evidence/action ledger; CitizenLifecycle remains the Health ID owner."""

    __tablename__ = "niam_health_identity_operations"

    operation_id = Column(String(100), unique=True, nullable=False, index=True)
    account_id = Column(String(26), ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    identity_id = Column(String(26), ForeignKey("niam_identities.id", ondelete="CASCADE"), nullable=False, index=True)
    person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True)
    operation_type = Column(String(40), nullable=False, index=True)
    status = Column(String(24), nullable=False, default="PENDING", index=True)
    method = Column(String(32), nullable=False)
    provider = Column(String(80), nullable=False, default="SYNTHETIC_ADAPTER")
    assurance_level = Column(String(16), nullable=False, default="L0")
    provider_reference = Column(String(160), nullable=True)
    evidence_digest = Column(String(128), nullable=True)
    verified_attributes = Column(JSON, nullable=True)
    purpose = Column(String(160), nullable=False)
    reason = Column(Text, nullable=True)
    source = Column(String(32), nullable=False, default="SYNTHETIC")
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("operation_type IN ('VERIFICATION','HEALTH_ID_ISSUANCE','RECOVERY','CONSENT_GRANT','CONSENT_REVOKE','DEVICE_TRUST')", name="ck_niam_health_operation_type"),
        CheckConstraint("status IN ('PENDING','VERIFIED','COMPLETED','FAILED','REJECTED','REVOKED')", name="ck_niam_health_operation_status"),
        CheckConstraint("method IN ('SYNTHETIC','OTP','OCR','NFC','LIVENESS','GOVERNMENT')", name="ck_niam_health_operation_method"),
        CheckConstraint("assurance_level IN ('L0','L1','L2','L3')", name="ck_niam_health_operation_assurance"),
        CheckConstraint("source = 'SYNTHETIC'", name="ck_niam_health_operation_synthetic_source"),
        CheckConstraint("version > 0", name="ck_niam_health_operation_version"),
    )

    @staticmethod
    def now() -> datetime:
        return datetime.now(UTC)
