from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from app._compat import UTC
from app.national.base import BaseEntity, NationalBase


class Partner(BaseEntity):
    __tablename__ = "ecosystem_partners"

    name = Column(String(255), nullable=False, index=True)
    org_type = Column(String(100), nullable=False)
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True, index=True)
    contact_phone = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False, default="active")
    tier = Column(String(20), nullable=False, default="bronze")
    agreement_date = Column(DateTime(timezone=True), nullable=True)
    agreement_version = Column(String(20), nullable=True)
    api_quota = Column(Integer, nullable=False, default=1000)
    rate_limit = Column(Integer, nullable=False, default=60)
    created_by = Column(Integer, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True, default=dict)


class PartnerCredential(NationalBase):
    __tablename__ = "ecosystem_partner_credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    partner_id = Column(String(26), ForeignKey("ecosystem_partners.id"), nullable=False, index=True)
    credential_type = Column(String(50), nullable=False)
    credential_name = Column(String(255), nullable=False)
    credential_value = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="active")
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class PartnerCertificate(BaseEntity):
    __tablename__ = "ecosystem_partner_certificates"

    partner_id = Column(String(26), ForeignKey("ecosystem_partners.id"), nullable=False, index=True)
    certificate_pem = Column(Text, nullable=False)
    certificate_serial = Column(String(255), nullable=True, index=True)
    issuer = Column(String(255), nullable=True)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    fingerprint = Column(String(255), nullable=True, index=True)


class PartnerRateLimit(NationalBase):
    __tablename__ = "ecosystem_partner_rate_limits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    partner_id = Column(String(26), ForeignKey("ecosystem_partners.id"), nullable=False, index=True)
    endpoint_pattern = Column(String(500), nullable=False)
    requests_per_minute = Column(Integer, nullable=False, default=60)
    requests_per_hour = Column(Integer, nullable=False, default=1000)
    requests_per_day = Column(Integer, nullable=False, default=10000)
    concurrent_limit = Column(Integer, nullable=False, default=10)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)


class PartnerAuditLog(NationalBase):
    __tablename__ = "ecosystem_partner_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    partner_id = Column(String(26), ForeignKey("ecosystem_partners.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    resource = Column(String(255), nullable=True)
    details = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default="success")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True)


class PartnerAgreement(BaseEntity):
    __tablename__ = "ecosystem_partner_agreements"

    partner_id = Column(String(26), ForeignKey("ecosystem_partners.id"), nullable=False, index=True)
    agreement_type = Column(String(50), nullable=False)
    version = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    accepted_by = Column(String(255), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
