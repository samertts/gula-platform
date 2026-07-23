from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app._compat import UTC
from app.identity.base import IdentityBaseEntity


class IdentityAuthority(IdentityBaseEntity):
    __tablename__ = "niam_gov_authorities"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    authority_id = Column(String(100), unique=True, nullable=False, index=True)

    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)

    authority_type = Column(
        String(50), nullable=False, index=True,
        default="identity_authority",
    )

    jurisdiction = Column(
        String(30), nullable=False, default="national",
    )

    parent_authority_id = Column(
        String(26), ForeignKey("niam_gov_authorities.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    contact_email = Column(String(200), nullable=True)

    status = Column(String(20), default="active", nullable=False, index=True)

    established_date = Column(DateTime(timezone=True), nullable=True)
    accredited_by = Column(String(200), nullable=True)
    accreditation_expires = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)


class DigitalIdentityCouncil(IdentityBaseEntity):
    __tablename__ = "niam_gov_councils"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    council_id = Column(String(100), unique=True, nullable=False, index=True)

    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)

    council_type = Column(
        String(30), nullable=False, index=True,
        default="governance",
    )

    authority_id = Column(
        String(26), ForeignKey("niam_gov_authorities.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    chairperson_id = Column(String(100), nullable=False)
    members = Column(JSON, nullable=True)

    meeting_frequency = Column(String(50), nullable=True)
    last_meeting = Column(DateTime(timezone=True), nullable=True)
    next_meeting = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(20), default="active", nullable=False, index=True)

    is_active = Column(Boolean, default=True, nullable=False)


class PolicyApprovalWorkflow(IdentityBaseEntity):
    __tablename__ = "niam_gov_policy_approvals"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    workflow_id = Column(String(100), unique=True, nullable=False, index=True)

    policy_id = Column(String(100), nullable=False, index=True)
    submitted_by = Column(String(100), nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    status = Column(String(20), default="draft", nullable=False, index=True)

    reviewers = Column(JSON, nullable=True)
    review_comments = Column(JSON, nullable=True)

    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    rejected_by = Column(String(100), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    version = Column(Integer, default=1, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)


class IdentityAppeal(IdentityBaseEntity):
    __tablename__ = "niam_gov_appeals"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    appeal_id = Column(String(100), unique=True, nullable=False, index=True)

    appellant_person_id = Column(String(100), nullable=False, index=True)
    identity_id = Column(String(100), nullable=False, index=True)

    appeal_type = Column(
        String(30), nullable=False, index=True,
        default="suspension",
    )

    reason = Column(Text, nullable=False)
    supporting_documents = Column(JSON, nullable=True)

    status = Column(String(20), default="submitted", nullable=False, index=True)

    assigned_to = Column(String(100), nullable=True)

    council_id = Column(
        String(26), ForeignKey("niam_gov_councils.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    decision = Column(Text, nullable=True)
    decision_at = Column(DateTime(timezone=True), nullable=True)
    decision_by = Column(String(100), nullable=True)

    notes = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)


class IdentitySuspension(IdentityBaseEntity):
    __tablename__ = "niam_gov_suspensions"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    suspension_id = Column(String(100), unique=True, nullable=False, index=True)

    person_id = Column(String(100), nullable=False, index=True)
    identity_id = Column(String(100), nullable=False, index=True)
    account_id = Column(String(100), nullable=True, index=True)

    reason = Column(Text, nullable=False)

    severity = Column(String(20), default="medium", nullable=False, index=True)

    suspended_by = Column(String(100), nullable=False)
    suspended_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)

    duration_hours = Column(Integer, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    lifted_by = Column(String(100), nullable=True)
    lifted_at = Column(DateTime(timezone=True), nullable=True)
    lift_reason = Column(Text, nullable=True)

    status = Column(String(20), default="active", nullable=False, index=True)

    notification_sent = Column(Boolean, default=False, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)


class IdentityRestoration(IdentityBaseEntity):
    __tablename__ = "niam_gov_restorations"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    restoration_id = Column(String(100), unique=True, nullable=False, index=True)

    person_id = Column(String(100), nullable=False, index=True)
    identity_id = Column(String(100), nullable=False, index=True)

    suspension_id = Column(
        String(26), ForeignKey("niam_gov_suspensions.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    request_reason = Column(Text, nullable=False)
    requested_by = Column(String(100), nullable=False)

    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(20), default="requested", nullable=False, index=True)

    restoration_type = Column(
        String(30), default="automatic", nullable=False,
    )

    post_restoration_actions = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)


class NationalIdentityRegistry(IdentityBaseEntity):
    __tablename__ = "niam_gov_registry"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    registry_id = Column(String(100), unique=True, nullable=False, index=True)

    person_id = Column(String(100), nullable=False, index=True)
    identity_id = Column(String(100), nullable=False, index=True)

    registry_type = Column(
        String(30), nullable=False, index=True,
        default="citizen",
    )

    registration_number = Column(String(100), unique=True, nullable=False, index=True)

    registered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    registered_by = Column(String(100), nullable=False)

    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(100), nullable=True)

    certificate_id = Column(String(100), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(20), default="active", nullable=False, index=True)

    data_quality_score = Column(Integer, nullable=True)
    last_verified = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)


class IdentityCertificationRegistry(IdentityBaseEntity):
    __tablename__ = "niam_gov_certifications"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    certification_id = Column(String(100), unique=True, nullable=False, index=True)

    person_id = Column(String(100), nullable=False, index=True)
    organization_id = Column(String(100), nullable=True, index=True)

    certifying_authority_id = Column(
        String(26), ForeignKey("niam_gov_authorities.id", ondelete="SET NULL"),
        nullable=False, index=True,
    )

    certification_type = Column(String(50), nullable=False)
    certification_number = Column(String(100), unique=True, nullable=False, index=True)

    issue_date = Column(DateTime(timezone=True), nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=True)

    status = Column(String(20), default="active", nullable=False, index=True)

    verified_by = Column(String(100), nullable=True)
    verification_method = Column(String(100), nullable=True)
    digital_signature = Column(Text, nullable=True)

    revocation_reason = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)


class IdentityReviewBoard(IdentityBaseEntity):
    __tablename__ = "niam_gov_review_boards"

    uuid = Column(String(36), unique=True, nullable=False, index=True)
    board_id = Column(String(100), unique=True, nullable=False, index=True)

    name_en = Column(String(300), nullable=False)
    name_ar = Column(String(300), nullable=True)

    board_type = Column(String(50), nullable=False, index=True)

    authority_id = Column(
        String(26), ForeignKey("niam_gov_authorities.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    chairperson_id = Column(String(100), nullable=False)
    members = Column(JSON, nullable=True)

    quorum_size = Column(Integer, default=3, nullable=False)

    meeting_schedule = Column(JSON, nullable=True)
    case_load = Column(Integer, default=0, nullable=False)

    status = Column(String(20), default="active", nullable=False, index=True)

    is_active = Column(Boolean, default=True, nullable=False)