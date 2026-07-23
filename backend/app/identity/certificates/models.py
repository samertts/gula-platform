from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text

from app._compat import UTC
from app.identity.base import IdentityBaseEntity


class DigitalCertificate(IdentityBaseEntity):
    __tablename__ = "niam_cert_certificates"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    certificate_id = Column(String(100), unique=True, nullable=False, index=True)
    serial_number = Column(String(100), unique=True, nullable=False, index=True)

    subject = Column(String(500), nullable=False)
    issuer = Column(String(500), nullable=False)

    certificate_type = Column(String(50), nullable=False, index=True)

    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True, index=True)
    machine_id = Column(String(26), ForeignKey("niam_machine_identities.id", ondelete="SET NULL"), nullable=True, index=True)

    public_key = Column(Text, nullable=False)
    private_key_encrypted = Column(Text, nullable=True)
    certificate_pem = Column(Text, nullable=False)
    certificate_chain = Column(Text, nullable=True)

    signature_algorithm = Column(String(50), nullable=False)
    key_size = Column(Integer, nullable=True)

    thumbprint = Column(String(64), unique=True, nullable=False, index=True)

    issued_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(String(200), nullable=True)
    revocation_date = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(20), default="active", nullable=False, index=True)

    last_rotated_at = Column(DateTime(timezone=True), nullable=True)
    rotation_period_days = Column(Integer, nullable=True)

    issuer_ca_id = Column(String(26), ForeignKey("niam_cert_certificates.id", ondelete="SET NULL"), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)


class CertificateAuthority(IdentityBaseEntity):
    __tablename__ = "niam_cert_authorities"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    ca_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)

    ca_type = Column(String(20), nullable=False, index=True)

    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="SET NULL"), nullable=True, index=True)

    certificate = Column(Text, nullable=False)
    private_key_encrypted = Column(Text, nullable=True)
    public_key = Column(Text, nullable=False)

    serial_number = Column(String(100), nullable=True)
    thumbprint = Column(String(64), unique=True, nullable=True, index=True)

    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=False)

    status = Column(String(20), default="active", nullable=False, index=True)

    signing_algorithm = Column(String(50), nullable=False)
    key_size = Column(Integer, nullable=True)
    path_length_constraint = Column(Integer, nullable=True)

    issued_certificate_count = Column(Integer, default=0, nullable=False)
    revoked_certificate_count = Column(Integer, default=0, nullable=False)

    parent_ca_id = Column(String(26), ForeignKey("niam_cert_authorities.id", ondelete="SET NULL"), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)


class CertificateRevocationList(IdentityBaseEntity):
    __tablename__ = "niam_cert_crls"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    crl_id = Column(String(100), unique=True, nullable=False, index=True)

    ca_id = Column(String(26), ForeignKey("niam_cert_authorities.id", ondelete="CASCADE"), nullable=False, index=True)

    crl_number = Column(Integer, nullable=False)
    this_update = Column(DateTime(timezone=True), nullable=False)
    next_update = Column(DateTime(timezone=True), nullable=False)

    revoked_certificates = Column(JSON, nullable=True)

    crl_pem = Column(Text, nullable=False)
    signature = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)


class APIKey(IdentityBaseEntity):
    __tablename__ = "niam_cert_api_keys"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    api_key_id = Column(String(100), unique=True, nullable=False, index=True)

    key_prefix = Column(String(10), nullable=False, index=True)
    key_hash = Column(String(255), nullable=False)

    name = Column(String(200), nullable=False)

    organization_id = Column(String(26), ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    enterprise_account_id = Column(String(26), ForeignKey("niam_enterprise_accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    person_id = Column(String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True, index=True)

    scopes = Column(JSON, nullable=True)
    permissions = Column(JSON, nullable=True)

    allowed_ips = Column(JSON, nullable=True)
    allowed_referrers = Column(JSON, nullable=True)

    rate_limit = Column(Integer, nullable=True)

    created_by = Column(String(26), ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True)

    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    rotated_at = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(20), default="active", nullable=False, index=True)

    is_active = Column(Boolean, default=True, nullable=False)
