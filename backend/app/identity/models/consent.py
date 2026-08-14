from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)

from app._compat import UTC
from app.identity.base import IdentityBaseEntity


class NiamConsentStatus(StrEnum):
    active = "ACTIVE"
    withdrawn = "WITHDRAWN"
    expired = "EXPIRED"
    revoked = "REVOKED"


class NiamConsentSource(StrEnum):
    user_portal = "USER_PORTAL"
    verified_workflow = "VERIFIED_WORKFLOW"
    authorized_administrator = "AUTHORIZED_ADMINISTRATOR"


class NiamConsent(IdentityBaseEntity):
    __tablename__ = "niam_consents"
    __table_args__ = (
        UniqueConstraint("subject_account_id", "grantee_account_id", "purpose", "resource_domain", "version", name="uq_niam_consent_version"),
    )

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    subject_account_id = Column(String(26), ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    grantee_account_id = Column(String(26), ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    purpose = Column(String(80), nullable=False, index=True)
    scope = Column(JSON, nullable=False)
    resource_domain = Column(String(120), nullable=False, index=True)
    status = Column(String(20), nullable=False, default=NiamConsentStatus.active.value, index=True)
    granted_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    withdrawn_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)
    source = Column(String(40), nullable=False, default=NiamConsentSource.user_portal.value)
    legal_basis = Column(String(120), nullable=True)
    created_by = Column(String(26), ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True)
    supersedes_id = Column(String(26), ForeignKey("niam_consents.id", ondelete="SET NULL"), nullable=True, index=True)
    reason = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")

    def is_valid_now(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(UTC)
        expiry = self.expires_at
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=UTC)
        return self.status == NiamConsentStatus.active.value and expiry > current
