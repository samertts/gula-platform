from app.care_continuum.base import CareContinuumTenantAuditEntity
from app.care_continuum.enums import ReferralDirection
from app.national.enums import ReferralPriority, ReferralStatus
from sqlalchemy import JSON, Boolean, Column, DateTime, Enum as SAEnum, ForeignKey, Index, String, Text


class ReferralRequest(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_referral_requests"

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)
    national_referral_id = Column(String(26), ForeignKey("national_referrals.id", ondelete="SET NULL"), nullable=True, index=True)
    encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), nullable=True, index=True)

    direction = Column(SAEnum(ReferralDirection), nullable=False, default=ReferralDirection.OUTGOING)
    status = Column(SAEnum(ReferralStatus), nullable=False, default=ReferralStatus.DRAFT)
    priority = Column(SAEnum(ReferralPriority), default=ReferralPriority.ROUTINE)

    referring_practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=False, index=True)
    referring_facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    referring_department_id = Column(String(26), ForeignKey("national_departments.id", ondelete="SET NULL"), nullable=True)

    receiving_practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=True, index=True)
    receiving_facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)
    receiving_department_id = Column(String(26), ForeignKey("national_departments.id", ondelete="SET NULL"), nullable=True)

    referral_reason = Column(Text, nullable=False)
    clinical_summary = Column(Text, nullable=True)
    diagnosis_code = Column(String(50), nullable=True)
    icd10_code = Column(String(20), nullable=True)
    additional_notes = Column(Text, nullable=True)

    is_cross_org = Column(Boolean, default=False)
    cross_org_status = Column(String(50), nullable=True)

    sent_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_referral_req_patient", "patient_id"),
        Index("ix_cc_referral_req_referring", "referring_facility_id"),
        Index("ix_cc_referral_req_receiving", "receiving_facility_id"),
        Index("ix_cc_referral_req_status", "status"),
        Index("ix_cc_referral_req_direction", "direction"),
        {"extend_existing": True},
    )


class ReferralResponse(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_referral_responses"

    referral_request_id = Column(String(26), ForeignKey("cc_referral_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    national_referral_id = Column(String(26), ForeignKey("national_referrals.id", ondelete="SET NULL"), nullable=True)

    responding_practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="RESTRICT"), nullable=False, index=True)
    responding_facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True)

    response_date = Column(DateTime(timezone=True), nullable=False)
    decision = Column(String(50), nullable=False)
    decision_reason = Column(Text, nullable=True)
    response_notes = Column(Text, nullable=True)
    clinical_impression = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    follow_up_actions = Column(JSON, nullable=True)
    attachments = Column(JSON, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_referral_resp_request", "referral_request_id"),
        Index("ix_cc_referral_resp_responder", "responding_practitioner_id"),
        {"extend_existing": True},
    )


class CrossOrgReferral(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_cross_org_referrals"

    referral_request_id = Column(String(26), ForeignKey("cc_referral_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    national_referral_id = Column(String(26), ForeignKey("national_referrals.id", ondelete="SET NULL"), nullable=True)

    patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), nullable=True, index=True)

    source_organization_id = Column(String(26), ForeignKey("national_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)

    target_organization_id = Column(String(26), ForeignKey("national_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    target_facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="RESTRICT"), nullable=True, index=True)

    exchange_protocol = Column(String(50), nullable=True)
    exchange_id = Column(String(100), nullable=True, index=True)
    exchanged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledgement_received = Column(Boolean, default=False)
    acknowledgement_at = Column(DateTime(timezone=True), nullable=True)
    acknowledgement_status = Column(String(50), nullable=True)

    clinical_data = Column(JSON, nullable=True)
    attachments = Column(JSON, nullable=True)
    consent_verified = Column(Boolean, default=False)
    consent_id = Column(String(26), ForeignKey("national_consents.id", ondelete="SET NULL"), nullable=True)

    status = Column(String(50), nullable=False, default="pending")
    error_details = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_cross_org_ref_source", "source_organization_id"),
        Index("ix_cc_cross_org_ref_target", "target_organization_id"),
        Index("ix_cc_cross_org_ref_patient", "patient_id"),
        Index("ix_cc_cross_org_ref_exchange", "exchange_id"),
        {"extend_existing": True},
    )


class ReferralAttachment(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_referral_attachments"

    referral_request_id = Column(String(26), ForeignKey("cc_referral_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    referral_response_id = Column(String(26), ForeignKey("cc_referral_responses.id", ondelete="CASCADE"), nullable=True, index=True)

    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    content_hash = Column(String(64), nullable=True)

    document_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    is_clinical = Column(Boolean, default=True)
    is_confidential = Column(Boolean, default=False)
    uploaded_by_practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)

    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_ref_attachments_request", "referral_request_id"),
        Index("ix_cc_ref_attachments_response", "referral_response_id"),
        {"extend_existing": True},
    )


class ReferralTimeline(CareContinuumTenantAuditEntity):
    __tablename__ = "cc_referral_timelines"

    referral_request_id = Column(String(26), ForeignKey("cc_referral_requests.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(String(100), nullable=False)
    event_date = Column(DateTime(timezone=True), nullable=False)
    description = Column(Text, nullable=True)

    actor_practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), nullable=True)
    actor_facility_id = Column(String(26), ForeignKey("national_facilities.id", ondelete="SET NULL"), nullable=True)

    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    duration_hours = Column(Integer, nullable=True)

    details = Column(JSON, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)

    __table_args__ = (
        Index("ix_cc_ref_timeline_request", "referral_request_id"),
        Index("ix_cc_ref_timeline_event", "event_type"),
        Index("ix_cc_ref_timeline_date", "event_date"),
        {"extend_existing": True},
    )
