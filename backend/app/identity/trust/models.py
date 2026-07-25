from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.identity.base import IdentityBaseEntity

IAL1 = "IAL1"
IAL2 = "IAL2"
IAL3 = "IAL3"
IAL4 = "IAL4"

AAL1 = "AAL1"
AAL2 = "AAL2"
AAL3 = "AAL3"

FAL1 = "FAL1"
FAL2 = "FAL2"
FAL3 = "FAL3"


class TrustFramework(IdentityBaseEntity):
    __tablename__ = "niam_trust_frameworks"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    framework_id = Column(String(100), unique=True, nullable=False, index=True)
    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=False)
    version = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="draft", index=True)
    effective_date = Column(DateTime(timezone=True), nullable=True)
    supersedes_framework_id = Column(
        String(26),
        ForeignKey("niam_trust_frameworks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    authority_id = Column(
        String(26),
        ForeignKey("niam_identity_authorities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    scope = Column(JSON, nullable=True)
    assurance_policies = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class IdentityAssuranceProfile(IdentityBaseEntity):
    __tablename__ = "niam_trust_assurance_profiles"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    person_id = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    identity_id = Column(
        String(26),
        ForeignKey("niam_identities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ial = Column(String(10), nullable=False)
    aal = Column(String(10), nullable=False)
    fal = Column(String(10), nullable=False)
    overall_assurance = Column(String(10), nullable=True)
    profile_version = Column(String(20), nullable=True)
    assessed_by = Column(String(200), nullable=True)
    assessed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_reviewed = Column(DateTime(timezone=True), nullable=True)
    next_review = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="active", index=True)
    evidence = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class TrustAnchor(IdentityBaseEntity):
    __tablename__ = "niam_trust_anchors"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    anchor_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(300), nullable=False)
    anchor_type = Column(String(30), nullable=False, index=True)
    public_key_hash = Column(String(255), nullable=True)
    certificate_chain = Column(Text, nullable=True)
    issuer = Column(String(500), nullable=True)
    subject = Column(String(500), nullable=True)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="active", index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(String(500), nullable=True)
    signed_by = Column(
        String(26),
        ForeignKey("niam_trust_anchors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active = Column(Boolean, default=True, nullable=False)


class FederationTrust(IdentityBaseEntity):
    __tablename__ = "niam_trust_federation"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    trust_id = Column(String(100), unique=True, nullable=False, index=True)
    source_org_id = Column(
        String(26),
        ForeignKey("niam_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_org_id = Column(
        String(26),
        ForeignKey("niam_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trust_type = Column(String(20), nullable=False, index=True)
    trust_level = Column(String(20), nullable=False)
    scope = Column(JSON, nullable=True)
    agreement_id = Column(String(100), nullable=True)
    established_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_reviewed = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="active", index=True)
    terms = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class IdentityProofing(IdentityBaseEntity):
    __tablename__ = "niam_trust_proofing"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    proofing_id = Column(String(100), unique=True, nullable=False, index=True)
    person_id = Column(
        String(26), ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    identity_id = Column(
        String(26),
        ForeignKey("niam_identities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    proofing_level = Column(String(10), nullable=False)
    method = Column(String(30), nullable=False)
    evidence_type = Column(JSON, nullable=True)
    evidence_documents = Column(JSON, nullable=True)
    verified_by = Column(String(200), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    authority_id = Column(
        String(26),
        ForeignKey("niam_identity_authorities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = Column(String(20), nullable=False, default="pending", index=True)
    rejection_reason = Column(Text, nullable=True)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_to = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class TrustEvaluation(IdentityBaseEntity):
    __tablename__ = "niam_trust_evaluations"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    evaluation_id = Column(String(100), unique=True, nullable=False, index=True)
    target_type = Column(String(30), nullable=False, index=True)
    target_id = Column(String(26), nullable=False, index=True)
    evaluated_by = Column(String(200), nullable=True)
    evaluated_at = Column(DateTime(timezone=True), nullable=True)
    assurance_score = Column(Integer, nullable=True)
    confidence_score = Column(Integer, nullable=True)
    risk_score = Column(Integer, nullable=True)
    evaluation_method = Column(String(50), nullable=True)
    findings = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    next_evaluation_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    is_active = Column(Boolean, default=True, nullable=False)
