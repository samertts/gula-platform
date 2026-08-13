"""NIAM governance, trust, lifecycle, federation, certificates, workflows,
notifications, adaptive auth, admin & compliance tables (Program NIAM-002)

Revision ID: 20260723_0002
Revises: 20260723_0001
Create Date: 2026-07-23

Tables:
  Governance    (9): niam_gov_authorities, _councils, _policy_approvals, _appeals,
                     _suspensions, _restorations, _registry, _certifications, _review_boards
  Trust         (6): niam_trust_frameworks, _assurance_profiles, _anchors,
                     _federation, _proofing, _evaluations
  Lifecycle     (8): niam_lifecycle_enterprise_reg, _enterprise_steps, _workforce_requests,
                     _gov_appointments, _citizen, _guardians, _family_links, _consents
  Federation    (6): niam_fed_providers, _identities, _links, _sessions,
                     _cross_org_trust, _agreements
  Certificates  (4): niam_cert_certificates, _authorities, _crls, _api_keys
  Workflows     (4): niam_wf_definitions, _instances, _approvals, _notifications
  Notifications (3): niam_notif_templates, _queue, _preferences
  Adaptive Auth (5): niam_adaptive_risk_events, _risk_policies, _mfa_sessions,
                     _travel_events, _session_policies
  Admin         (7): niam_admin_portals, _branches, _facilities, _departments,
                     _subscriptions, _audit_logs, _fhir_connections
  Compliance    (3): niam_comp_frameworks, _checks, _reports
"""
from __future__ import annotations

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260723_0002"
down_revision: Union[str, None] = "20260723_0001"


def _has_table(name: str) -> bool:
    conn = op.get_bind()
    return conn.dialect.has_table(conn, name)


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    if not conn.dialect.has_table(conn, table):
        return False
    insp = sa.inspect(conn)
    cols = [c["name"] for c in insp.get_columns(table)]
    return column in cols


def upgrade() -> None:
    # ── GOVERNANCE ─────────────────────────────────────────────────────────

    # ── 1. niam_gov_authorities ──────────────────────────────────────────────
    if not _has_table("niam_gov_authorities"):
        op.create_table(
            "niam_gov_authorities",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("authority_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("name_en", sa.String(length=300), nullable=False),
            sa.Column("name_ar", sa.String(length=300), nullable=True),
            sa.Column("authority_type", sa.String(length=50), nullable=False, index=True),
            sa.Column("jurisdiction", sa.String(length=30), nullable=False),
            sa.Column("parent_authority_id", sa.String(length=26), sa.ForeignKey("niam_gov_authorities.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("contact_email", sa.String(length=200), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("established_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("accredited_by", sa.String(length=200), nullable=True),
            sa.Column("accreditation_expires", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("authority_id"),
        )

    # ── 2. niam_gov_suspensions ──────────────────────────────────────────────
    if not _has_table("niam_gov_suspensions"):
        op.create_table(
            "niam_gov_suspensions",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("suspension_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("person_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("identity_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("account_id", sa.String(length=100), nullable=True, index=True),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("severity", sa.String(length=20), nullable=False, index=True),
            sa.Column("suspended_by", sa.String(length=100), nullable=False),
            sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("duration_hours", sa.Integer(), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("lifted_by", sa.String(length=100), nullable=True),
            sa.Column("lifted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("lift_reason", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("notification_sent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("suspension_id"),
        )

    # ── 3. niam_gov_registry ─────────────────────────────────────────────────
    if not _has_table("niam_gov_registry"):
        op.create_table(
            "niam_gov_registry",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("registry_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("person_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("identity_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("registry_type", sa.String(length=30), nullable=False, index=True),
            sa.Column("registration_number", sa.String(length=100), nullable=False, index=True),
            sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("registered_by", sa.String(length=100), nullable=False),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("verified_by", sa.String(length=100), nullable=True),
            sa.Column("certificate_id", sa.String(length=100), nullable=True),
            sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("data_quality_score", sa.Integer(), nullable=True),
            sa.Column("last_verified", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("registry_id"),
            sa.UniqueConstraint("registration_number"),
        )

    # ── 4. niam_gov_policy_approvals ─────────────────────────────────────────
    if not _has_table("niam_gov_policy_approvals"):
        op.create_table(
            "niam_gov_policy_approvals",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("workflow_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("policy_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("submitted_by", sa.String(length=100), nullable=False),
            sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("reviewers", sa.JSON(), nullable=True),
            sa.Column("review_comments", sa.JSON(), nullable=True),
            sa.Column("approved_by", sa.String(length=100), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rejected_by", sa.String(length=100), nullable=True),
            sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rejection_reason", sa.Text(), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("workflow_id"),
        )

    # ── 5. niam_gov_councils ─────────────────────────────────────────────────
    if not _has_table("niam_gov_councils"):
        op.create_table(
            "niam_gov_councils",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("council_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("name_en", sa.String(length=300), nullable=False),
            sa.Column("name_ar", sa.String(length=300), nullable=True),
            sa.Column("council_type", sa.String(length=30), nullable=False, index=True),
            sa.Column("authority_id", sa.String(length=26), sa.ForeignKey("niam_gov_authorities.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("chairperson_id", sa.String(length=100), nullable=False),
            sa.Column("members", sa.JSON(), nullable=True),
            sa.Column("meeting_frequency", sa.String(length=50), nullable=True),
            sa.Column("last_meeting", sa.DateTime(timezone=True), nullable=True),
            sa.Column("next_meeting", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("council_id"),
        )

    # ── 6. niam_gov_review_boards ────────────────────────────────────────────
    if not _has_table("niam_gov_review_boards"):
        op.create_table(
            "niam_gov_review_boards",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("board_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("name_en", sa.String(length=300), nullable=False),
            sa.Column("name_ar", sa.String(length=300), nullable=True),
            sa.Column("board_type", sa.String(length=50), nullable=False, index=True),
            sa.Column("authority_id", sa.String(length=26), sa.ForeignKey("niam_gov_authorities.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("chairperson_id", sa.String(length=100), nullable=False),
            sa.Column("members", sa.JSON(), nullable=True),
            sa.Column("quorum_size", sa.Integer(), nullable=False),
            sa.Column("meeting_schedule", sa.JSON(), nullable=True),
            sa.Column("case_load", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("board_id"),
        )

    # ── 7. niam_gov_certifications ───────────────────────────────────────────
    if not _has_table("niam_gov_certifications"):
        op.create_table(
            "niam_gov_certifications",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("certification_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("person_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("organization_id", sa.String(length=100), nullable=True, index=True),
            sa.Column("certifying_authority_id", sa.String(length=26), sa.ForeignKey("niam_gov_authorities.id", ondelete="SET NULL"), nullable=False, index=True),
            sa.Column("certification_type", sa.String(length=50), nullable=False),
            sa.Column("certification_number", sa.String(length=100), nullable=False, index=True),
            sa.Column("issue_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("verified_by", sa.String(length=100), nullable=True),
            sa.Column("verification_method", sa.String(length=100), nullable=True),
            sa.Column("digital_signature", sa.Text(), nullable=True),
            sa.Column("revocation_reason", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("certification_id"),
            sa.UniqueConstraint("certification_number"),
        )

    # ── 8. niam_gov_restorations ─────────────────────────────────────────────
    if not _has_table("niam_gov_restorations"):
        op.create_table(
            "niam_gov_restorations",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("restoration_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("person_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("identity_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("suspension_id", sa.String(length=26), sa.ForeignKey("niam_gov_suspensions.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("request_reason", sa.Text(), nullable=False),
            sa.Column("requested_by", sa.String(length=100), nullable=False),
            sa.Column("reviewed_by", sa.String(length=100), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("approved_by", sa.String(length=100), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("restoration_type", sa.String(length=30), nullable=False),
            sa.Column("post_restoration_actions", sa.JSON(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("restoration_id"),
        )

    # ── 9. niam_gov_appeals ──────────────────────────────────────────────────
    if not _has_table("niam_gov_appeals"):
        op.create_table(
            "niam_gov_appeals",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("appeal_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("appellant_person_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("identity_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("appeal_type", sa.String(length=30), nullable=False, index=True),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("supporting_documents", sa.JSON(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("assigned_to", sa.String(length=100), nullable=True),
            sa.Column("council_id", sa.String(length=26), sa.ForeignKey("niam_gov_councils.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("decision", sa.Text(), nullable=True),
            sa.Column("decision_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("decision_by", sa.String(length=100), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("appeal_id"),
        )

    # ── TRUST ────────────────────────────────────────────────────────────────

    # ── 10. niam_trust_frameworks ────────────────────────────────────────────
    if not _has_table("niam_trust_frameworks"):
        op.create_table(
            "niam_trust_frameworks",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("framework_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("name_en", sa.String(length=300), nullable=False),
            sa.Column("name_ar", sa.String(length=300), nullable=False),
            sa.Column("version", sa.String(length=20), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("effective_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("supersedes_framework_id", sa.String(length=26), sa.ForeignKey("niam_trust_frameworks.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("authority_id", sa.String(length=26), sa.ForeignKey("niam_gov_authorities.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("scope", sa.JSON(), nullable=True),
            sa.Column("assurance_policies", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("framework_id"),
        )

    # ── 11. niam_trust_anchors ───────────────────────────────────────────────
    if not _has_table("niam_trust_anchors"):
        op.create_table(
            "niam_trust_anchors",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("anchor_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("name", sa.String(length=300), nullable=False),
            sa.Column("anchor_type", sa.String(length=30), nullable=False, index=True),
            sa.Column("public_key_hash", sa.String(length=255), nullable=True),
            sa.Column("certificate_chain", sa.Text(), nullable=True),
            sa.Column("issuer", sa.String(length=500), nullable=True),
            sa.Column("subject", sa.String(length=500), nullable=True),
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
            sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revocation_reason", sa.String(length=500), nullable=True),
            sa.Column("signed_by", sa.String(length=26), sa.ForeignKey("niam_trust_anchors.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("anchor_id"),
        )

    # ── 12. niam_trust_assurance_profiles ────────────────────────────────────
    if not _has_table("niam_trust_assurance_profiles"):
        op.create_table(
            "niam_trust_assurance_profiles",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("identity_id", sa.String(length=26), sa.ForeignKey("niam_identities.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("ial", sa.String(length=10), nullable=False),
            sa.Column("aal", sa.String(length=10), nullable=False),
            sa.Column("fal", sa.String(length=10), nullable=False),
            sa.Column("overall_assurance", sa.String(length=10), nullable=True),
            sa.Column("profile_version", sa.String(length=20), nullable=True),
            sa.Column("assessed_by", sa.String(length=200), nullable=True),
            sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_reviewed", sa.DateTime(timezone=True), nullable=True),
            sa.Column("next_review", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("evidence", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
        )

    # ── 13. niam_trust_proofing ──────────────────────────────────────────────
    if not _has_table("niam_trust_proofing"):
        op.create_table(
            "niam_trust_proofing",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("proofing_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("identity_id", sa.String(length=26), sa.ForeignKey("niam_identities.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("proofing_level", sa.String(length=10), nullable=False),
            sa.Column("method", sa.String(length=30), nullable=False),
            sa.Column("evidence_type", sa.JSON(), nullable=True),
            sa.Column("evidence_documents", sa.JSON(), nullable=True),
            sa.Column("verified_by", sa.String(length=200), nullable=True),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("authority_id", sa.String(length=26), sa.ForeignKey("niam_gov_authorities.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("rejection_reason", sa.Text(), nullable=True),
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
            sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("proofing_id"),
        )

    # ── 14. niam_trust_federation ────────────────────────────────────────────
    if not _has_table("niam_trust_federation"):
        op.create_table(
            "niam_trust_federation",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("trust_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("source_org_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("target_org_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("trust_type", sa.String(length=20), nullable=False, index=True),
            sa.Column("trust_level", sa.String(length=20), nullable=False),
            sa.Column("scope", sa.JSON(), nullable=True),
            sa.Column("agreement_id", sa.String(length=100), nullable=True),
            sa.Column("established_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_reviewed", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("terms", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("trust_id"),
        )

    # ── 15. niam_trust_evaluations ───────────────────────────────────────────
    if not _has_table("niam_trust_evaluations"):
        op.create_table(
            "niam_trust_evaluations",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("evaluation_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("target_type", sa.String(length=30), nullable=False, index=True),
            sa.Column("target_id", sa.String(length=26), nullable=False, index=True),
            sa.Column("evaluated_by", sa.String(length=200), nullable=True),
            sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("assurance_score", sa.Integer(), nullable=True),
            sa.Column("confidence_score", sa.Integer(), nullable=True),
            sa.Column("risk_score", sa.Integer(), nullable=True),
            sa.Column("evaluation_method", sa.String(length=50), nullable=True),
            sa.Column("findings", sa.JSON(), nullable=True),
            sa.Column("recommendations", sa.JSON(), nullable=True),
            sa.Column("next_evaluation_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("evaluation_id"),
        )

    # ── LIFECYCLE ───────────────────────────────────────────────────────────

    # ── 16. niam_lifecycle_enterprise_reg ────────────────────────────────────
    if not _has_table("niam_lifecycle_enterprise_reg"):
        op.create_table(
            "niam_lifecycle_enterprise_reg",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("reg_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("organization_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("status", sa.String(length=50), nullable=False, index=True),
            sa.Column("submitted_by", sa.String(length=100), nullable=True),
            sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("license_document", sa.Text(), nullable=True),
            sa.Column("license_validated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("license_validated_by", sa.String(length=100), nullable=True),
            sa.Column("inspection_report", sa.JSON(), nullable=True),
            sa.Column("inspected_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("inspected_by", sa.String(length=100), nullable=True),
            sa.Column("risk_assessment", sa.JSON(), nullable=True),
            sa.Column("risk_score", sa.Integer(), nullable=True),
            sa.Column("risk_assessed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("approved_by", sa.String(length=100), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("certificate_id", sa.String(length=100), nullable=True),
            sa.Column("rejection_reason", sa.Text(), nullable=True),
            sa.Column("current_step", sa.String(length=50), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("reg_id"),
        )

    # ── 17. niam_lifecycle_enterprise_steps ──────────────────────────────────
    if not _has_table("niam_lifecycle_enterprise_steps"):
        op.create_table(
            "niam_lifecycle_enterprise_steps",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("step_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("reg_id", sa.String(length=26), sa.ForeignKey("niam_lifecycle_enterprise_reg.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("step_name", sa.String(length=100), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("performed_by", sa.String(length=100), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("output", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("step_id"),
        )

    # ── 18. niam_lifecycle_workforce_requests ────────────────────────────────
    if not _has_table("niam_lifecycle_workforce_requests"):
        op.create_table(
            "niam_lifecycle_workforce_requests",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("request_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("request_type", sa.String(length=50), nullable=False, index=True),
            sa.Column("requesting_org_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("requested_by", sa.String(length=100), nullable=True),
            sa.Column("person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("status", sa.String(length=50), nullable=False, index=True),
            sa.Column("national_id_hash", sa.String(length=255), nullable=True),
            sa.Column("license_number", sa.String(length=100), nullable=True),
            sa.Column("board_registration", sa.String(length=100), nullable=True),
            sa.Column("employment_rules_check", sa.JSON(), nullable=True),
            sa.Column("conflict_report", sa.JSON(), nullable=True),
            sa.Column("restrictions", sa.JSON(), nullable=True),
            sa.Column("approved_by", sa.String(length=100), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("suspension_reason", sa.Text(), nullable=True),
            sa.Column("termination_reason", sa.Text(), nullable=True),
            sa.Column("historical_preserved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("request_id"),
        )

    # ── 19. niam_lifecycle_gov_appointments ──────────────────────────────────
    if not _has_table("niam_lifecycle_gov_appointments"):
        op.create_table(
            "niam_lifecycle_gov_appointments",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("appointment_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("organization_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("hr_reference", sa.String(length=100), nullable=False, index=True),
            sa.Column("appointment_type", sa.String(length=30), nullable=False),
            sa.Column("position", sa.String(length=200), nullable=True),
            sa.Column("grade", sa.String(length=50), nullable=True),
            sa.Column("salary_scale", sa.String(length=50), nullable=True),
            sa.Column("department", sa.String(length=200), nullable=True),
            sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("hr_approved_by", sa.String(length=100), nullable=True),
            sa.Column("hr_approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("identity_created", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("credential_issued", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("account_activated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("permissions_assigned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("status", sa.String(length=30), nullable=False, index=True),
            sa.Column("promotion_history", sa.JSON(), nullable=True),
            sa.Column("transfer_history", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("appointment_id"),
            sa.UniqueConstraint("hr_reference"),
        )

    # ── 20. niam_lifecycle_citizen ───────────────────────────────────────────
    if not _has_table("niam_lifecycle_citizen"):
        op.create_table(
            "niam_lifecycle_citizen",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("citizen_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("identity_id", sa.String(length=26), sa.ForeignKey("niam_identities.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("status", sa.String(length=30), nullable=False, index=True),
            sa.Column("registration_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("otp_sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("otp_verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("identity_verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("health_id", sa.String(length=100), nullable=True, index=True),
            sa.Column("guardian_person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("family_tree", sa.JSON(), nullable=True),
            sa.Column("consent_records", sa.JSON(), nullable=True),
            sa.Column("emergency_contacts", sa.JSON(), nullable=True),
            sa.Column("address_history", sa.JSON(), nullable=True),
            sa.Column("document_verification", sa.JSON(), nullable=True),
            sa.Column("self_service_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("last_recovery_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("deactivation_reason", sa.Text(), nullable=True),
            sa.Column("deceased_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("death_certificate_id", sa.String(length=100), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("citizen_id"),
            sa.UniqueConstraint("health_id"),
        )

    # ── 21. niam_lifecycle_guardians ─────────────────────────────────────────
    if not _has_table("niam_lifecycle_guardians"):
        op.create_table(
            "niam_lifecycle_guardians",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("guardian_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("guardian_person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("dependent_person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("relationship", sa.String(length=50), nullable=False),
            sa.Column("guardian_type", sa.String(length=30), nullable=False),
            sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("delegated_access", sa.JSON(), nullable=True),
            sa.Column("consent_inheritance", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("verified_by", sa.String(length=100), nullable=True),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("documents", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("guardian_id"),
        )

    # ── 22. niam_lifecycle_family_links ──────────────────────────────────────
    if not _has_table("niam_lifecycle_family_links"):
        op.create_table(
            "niam_lifecycle_family_links",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("link_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("relative_person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("relationship", sa.String(length=30), nullable=False),
            sa.Column("emergency_contact", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("consent_sharing", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("link_id"),
        )

    # ── 23. niam_lifecycle_consents ──────────────────────────────────────────
    if not _has_table("niam_lifecycle_consents"):
        op.create_table(
            "niam_lifecycle_consents",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("consent_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("consent_type", sa.String(length=50), nullable=False),
            sa.Column("granted_to", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("scope", sa.JSON(), nullable=True),
            sa.Column("terms", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("consent_id"),
        )

    # ── FEDERATION ──────────────────────────────────────────────────────────

    # ── 24. niam_fed_providers ───────────────────────────────────────────────
    if not _has_table("niam_fed_providers"):
        op.create_table(
            "niam_fed_providers",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("provider_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("name_en", sa.String(length=300), nullable=False),
            sa.Column("name_ar", sa.String(length=300), nullable=True),
            sa.Column("provider_type", sa.String(length=50), nullable=False, index=True),
            sa.Column("issuer_url", sa.String(length=500), nullable=False, index=True),
            sa.Column("authorization_endpoint", sa.String(length=500), nullable=True),
            sa.Column("token_endpoint", sa.String(length=500), nullable=True),
            sa.Column("jwks_uri", sa.String(length=500), nullable=True),
            sa.Column("userinfo_endpoint", sa.String(length=500), nullable=True),
            sa.Column("client_id", sa.String(length=500), nullable=True),
            sa.Column("client_secret_encrypted", sa.String(length=500), nullable=True),
            sa.Column("scopes", sa.JSON(), nullable=True),
            sa.Column("redirect_uris", sa.JSON(), nullable=True),
            sa.Column("certificate", sa.Text(), nullable=True),
            sa.Column("signature_algorithm", sa.String(length=50), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("trust_anchor_id", sa.String(length=100), nullable=True),
            sa.Column("metadata_url", sa.String(length=500), nullable=True),
            sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("provider_id"),
            sa.UniqueConstraint("issuer_url"),
        )

    # ── 25. niam_fed_identities ──────────────────────────────────────────────
    if not _has_table("niam_fed_identities"):
        op.create_table(
            "niam_fed_identities",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("fed_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("identity_id", sa.String(length=26), sa.ForeignKey("niam_identities.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("provider_id", sa.String(length=26), sa.ForeignKey("niam_fed_providers.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("external_subject_id", sa.String(length=500), nullable=False, index=True),
            sa.Column("external_attributes", sa.JSON(), nullable=True),
            sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("unlinked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("unlink_reason", sa.String(length=500), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("fed_id"),
        )

    # ── 26. niam_fed_links ───────────────────────────────────────────────────
    if not _has_table("niam_fed_links"):
        op.create_table(
            "niam_fed_links",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("link_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("source_org_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("target_org_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("link_type", sa.String(length=30), nullable=False, index=True),
            sa.Column("external_person_id", sa.String(length=100), nullable=True),
            sa.Column("external_identity_id", sa.String(length=100), nullable=True),
            sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("linked_by", sa.String(length=100), nullable=True),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("verified_by", sa.String(length=100), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("expiry", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("link_id"),
        )

    # ── 27. niam_fed_cross_org_trust ─────────────────────────────────────────
    if not _has_table("niam_fed_cross_org_trust"):
        op.create_table(
            "niam_fed_cross_org_trust",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("trust_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("source_org_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("target_org_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("trust_type", sa.String(length=50), nullable=False),
            sa.Column("trust_level", sa.String(length=30), nullable=False),
            sa.Column("attribute_sharing_agreement", sa.JSON(), nullable=True),
            sa.Column("permission_mapping", sa.JSON(), nullable=True),
            sa.Column("role_mapping", sa.JSON(), nullable=True),
            sa.Column("established_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("established_by", sa.String(length=100), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_reviewed", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("trust_id"),
        )

    # ── 28. niam_fed_agreements ──────────────────────────────────────────────
    if not _has_table("niam_fed_agreements"):
        op.create_table(
            "niam_fed_agreements",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("agreement_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("name", sa.String(length=300), nullable=False),
            sa.Column("parties", sa.JSON(), nullable=False),
            sa.Column("agreement_type", sa.String(length=50), nullable=False, index=True),
            sa.Column("scope", sa.JSON(), nullable=True),
            sa.Column("terms", sa.JSON(), nullable=True),
            sa.Column("security_requirements", sa.JSON(), nullable=True),
            sa.Column("signed_by", sa.JSON(), nullable=True),
            sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("effective_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("governing_law", sa.String(length=100), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("agreement_id"),
        )

    # ── 29. niam_fed_sessions ────────────────────────────────────────────────
    if not _has_table("niam_fed_sessions"):
        op.create_table(
            "niam_fed_sessions",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("session_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("account_id", sa.String(length=26), sa.ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("provider_id", sa.String(length=26), sa.ForeignKey("niam_fed_providers.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("fed_identity_id", sa.String(length=26), sa.ForeignKey("niam_fed_identities.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("id_token", sa.Text(), nullable=True),
            sa.Column("access_token_hash", sa.String(length=128), nullable=True),
            sa.Column("refresh_token_hash", sa.String(length=128), nullable=True),
            sa.Column("token_type", sa.String(length=50), nullable=True),
            sa.Column("scope", sa.String(length=500), nullable=True),
            sa.Column("session_attributes", sa.JSON(), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("terminated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("session_id"),
        )

    # ── CERTIFICATES ────────────────────────────────────────────────────────

    # ── 30. niam_cert_authorities ────────────────────────────────────────────
    if not _has_table("niam_cert_authorities"):
        op.create_table(
            "niam_cert_authorities",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("ca_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("ca_type", sa.String(length=20), nullable=False, index=True),
            sa.Column("organization_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("certificate", sa.Text(), nullable=False),
            sa.Column("private_key_encrypted", sa.Text(), nullable=True),
            sa.Column("public_key", sa.Text(), nullable=False),
            sa.Column("serial_number", sa.String(length=100), nullable=True),
            sa.Column("thumbprint", sa.String(length=64), nullable=True, index=True),
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
            sa.Column("valid_to", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("signing_algorithm", sa.String(length=50), nullable=False),
            sa.Column("key_size", sa.Integer(), nullable=True),
            sa.Column("path_length_constraint", sa.Integer(), nullable=True),
            sa.Column("issued_certificate_count", sa.Integer(), nullable=False),
            sa.Column("revoked_certificate_count", sa.Integer(), nullable=False),
            sa.Column("parent_ca_id", sa.String(length=26), sa.ForeignKey("niam_cert_authorities.id", ondelete="SET NULL"), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("ca_id"),
            sa.UniqueConstraint("thumbprint"),
        )
        op.create_index("ix_niam_cert_authorities_parent_ca", "niam_cert_authorities", ["parent_ca_id"])

    # ── 31. niam_cert_certificates ───────────────────────────────────────────
    if not _has_table("niam_cert_certificates"):
        op.create_table(
            "niam_cert_certificates",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("certificate_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("serial_number", sa.String(length=100), nullable=False, index=True),
            sa.Column("subject", sa.String(length=500), nullable=False),
            sa.Column("issuer", sa.String(length=500), nullable=False),
            sa.Column("certificate_type", sa.String(length=50), nullable=False, index=True),
            sa.Column("organization_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("machine_id", sa.String(length=26), sa.ForeignKey("niam_machine_identities.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("public_key", sa.Text(), nullable=False),
            sa.Column("private_key_encrypted", sa.Text(), nullable=True),
            sa.Column("certificate_pem", sa.Text(), nullable=False),
            sa.Column("certificate_chain", sa.Text(), nullable=True),
            sa.Column("signature_algorithm", sa.String(length=50), nullable=False),
            sa.Column("key_size", sa.Integer(), nullable=True),
            sa.Column("thumbprint", sa.String(length=64), nullable=False, index=True),
            sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revocation_reason", sa.String(length=200), nullable=True),
            sa.Column("revocation_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("last_rotated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rotation_period_days", sa.Integer(), nullable=True),
            sa.Column("issuer_ca_id", sa.String(length=26), sa.ForeignKey("niam_cert_certificates.id", ondelete="SET NULL"), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("certificate_id"),
            sa.UniqueConstraint("serial_number"),
            sa.UniqueConstraint("thumbprint"),
        )
        op.create_index("ix_niam_cert_certificates_issuer_ca", "niam_cert_certificates", ["issuer_ca_id"])

    # ── 32. niam_cert_crls ───────────────────────────────────────────────────
    if not _has_table("niam_cert_crls"):
        op.create_table(
            "niam_cert_crls",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("crl_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("ca_id", sa.String(length=26), sa.ForeignKey("niam_cert_authorities.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("crl_number", sa.Integer(), nullable=False),
            sa.Column("this_update", sa.DateTime(timezone=True), nullable=False),
            sa.Column("next_update", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_certificates", sa.JSON(), nullable=True),
            sa.Column("crl_pem", sa.Text(), nullable=False),
            sa.Column("signature", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("crl_id"),
        )

    # ── 33. niam_cert_api_keys ───────────────────────────────────────────────
    if not _has_table("niam_cert_api_keys"):
        op.create_table(
            "niam_cert_api_keys",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("api_key_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("key_prefix", sa.String(length=10), nullable=False, index=True),
            sa.Column("key_hash", sa.String(length=255), nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("organization_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("enterprise_account_id", sa.String(length=26), sa.ForeignKey("niam_enterprise_accounts.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("scopes", sa.JSON(), nullable=True),
            sa.Column("permissions", sa.JSON(), nullable=True),
            sa.Column("allowed_ips", sa.JSON(), nullable=True),
            sa.Column("allowed_referrers", sa.JSON(), nullable=True),
            sa.Column("rate_limit", sa.Integer(), nullable=True),
            sa.Column("created_by", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("api_key_id"),
        )
        op.create_index("ix_niam_cert_api_keys_created_by", "niam_cert_api_keys", ["created_by"])

    # ── WORKFLOWS ───────────────────────────────────────────────────────────

    # ── 34. niam_wf_definitions ──────────────────────────────────────────────
    if not _has_table("niam_wf_definitions"):
        op.create_table(
            "niam_wf_definitions",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("def_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("workflow_type", sa.String(length=30), nullable=False, index=True),
            sa.Column("version", sa.String(length=20), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("steps", sa.JSON(), nullable=False),
            sa.Column("timeout_hours", sa.Integer(), nullable=True),
            sa.Column("escalation_step", sa.String(length=100), nullable=True),
            sa.Column("retry_policy", sa.JSON(), nullable=True),
            sa.Column("notification_triggers", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("def_id"),
        )

    # ── 35. niam_wf_instances ────────────────────────────────────────────────
    if not _has_table("niam_wf_instances"):
        op.create_table(
            "niam_wf_instances",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("instance_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("def_id", sa.String(length=100), sa.ForeignKey("niam_wf_definitions.def_id", ondelete="RESTRICT"), nullable=False, index=True),
            sa.Column("trigger_type", sa.String(length=50), nullable=False),
            sa.Column("trigger_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("initiator_id", sa.String(length=100), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False, index=True),
            sa.Column("current_step", sa.String(length=100), nullable=True),
            sa.Column("state", sa.JSON(), nullable=True),
            sa.Column("context", sa.JSON(), nullable=True),
            sa.Column("assigned_to", sa.String(length=100), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_action_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("sla_deadline", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("instance_id"),
        )

    # ── 36. niam_wf_approvals ────────────────────────────────────────────────
    if not _has_table("niam_wf_approvals"):
        op.create_table(
            "niam_wf_approvals",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("approval_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("instance_id", sa.String(length=100), sa.ForeignKey("niam_wf_instances.instance_id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("step_name", sa.String(length=100), nullable=False),
            sa.Column("approver_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("comments", sa.Text(), nullable=True),
            sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("action_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("delegated_to", sa.String(length=100), nullable=True),
            sa.Column("escalation_reason", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("approval_id"),
        )

    # ── 37. niam_wf_notifications ────────────────────────────────────────────
    if not _has_table("niam_wf_notifications"):
        op.create_table(
            "niam_wf_notifications",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("notification_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("instance_id", sa.String(length=100), sa.ForeignKey("niam_wf_instances.instance_id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("recipient_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("notification_type", sa.String(length=20), nullable=False),
            sa.Column("channel", sa.String(length=20), nullable=True),
            sa.Column("template_id", sa.String(length=100), nullable=True),
            sa.Column("subject", sa.String(length=200), nullable=True),
            sa.Column("body", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("notification_id"),
        )

    # ── NOTIFICATIONS ───────────────────────────────────────────────────────

    # ── 38. niam_notif_templates ─────────────────────────────────────────────
    if not _has_table("niam_notif_templates"):
        op.create_table(
            "niam_notif_templates",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("template_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("notification_type", sa.String(length=20), nullable=False, index=True),
            sa.Column("subject", sa.String(length=200), nullable=True),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("variables", sa.JSON(), nullable=True),
            sa.Column("locale", sa.String(length=10), nullable=False),
            sa.Column("version", sa.String(length=20), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("template_id"),
        )

    # ── 39. niam_notif_queue ─────────────────────────────────────────────────
    if not _has_table("niam_notif_queue"):
        op.create_table(
            "niam_notif_queue",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("queue_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("recipient_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("recipient_type", sa.String(length=30), nullable=False),
            sa.Column("notification_type", sa.String(length=20), nullable=False),
            sa.Column("channel", sa.String(length=20), nullable=False),
            sa.Column("template_id", sa.String(length=100), sa.ForeignKey("niam_notif_templates.template_id", ondelete="SET NULL"), nullable=True),
            sa.Column("subject", sa.String(length=200), nullable=True),
            sa.Column("body", sa.Text(), nullable=True),
            sa.Column("context", sa.JSON(), nullable=True),
            sa.Column("priority", sa.String(length=20), nullable=False, index=True),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("error_count", sa.Integer(), nullable=False),
            sa.Column("max_retries", sa.Integer(), nullable=False),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("queue_id"),
        )
        op.create_index("ix_niam_notif_queue_template", "niam_notif_queue", ["template_id"])

    # ── 40. niam_notif_preferences ───────────────────────────────────────────
    if not _has_table("niam_notif_preferences"):
        op.create_table(
            "niam_notif_preferences",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("preference_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("recipient_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("recipient_type", sa.String(length=30), nullable=False),
            sa.Column("category", sa.String(length=30), nullable=False),
            sa.Column("channel", sa.String(length=20), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("quiet_hours_start", sa.String(length=5), nullable=True),
            sa.Column("quiet_hours_end", sa.String(length=5), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("preference_id"),
        )

    # ── ADAPTIVE AUTH ───────────────────────────────────────────────────────

    # ── 41. niam_adaptive_risk_events ────────────────────────────────────────
    if not _has_table("niam_adaptive_risk_events"):
        op.create_table(
            "niam_adaptive_risk_events",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("event_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("person_id", sa.String(length=100), sa.ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("account_id", sa.String(length=100), sa.ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("session_id", sa.String(length=100), nullable=True, index=True),
            sa.Column("event_type", sa.String(length=50), nullable=False, index=True),
            sa.Column("severity", sa.String(length=20), nullable=False, index=True),
            sa.Column("risk_score", sa.Integer(), nullable=False),
            sa.Column("details", sa.JSON(), nullable=True),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.String(length=500), nullable=True),
            sa.Column("location_city", sa.String(length=200), nullable=True),
            sa.Column("location_country", sa.String(length=200), nullable=True),
            sa.Column("location_lat", sa.String(length=50), nullable=True),
            sa.Column("location_lng", sa.String(length=50), nullable=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
            sa.Column("mitigated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("mitigation_action", sa.String(length=50), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("event_id"),
        )

    # ── 42. niam_adaptive_risk_policies ──────────────────────────────────────
    if not _has_table("niam_adaptive_risk_policies"):
        op.create_table(
            "niam_adaptive_risk_policies",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("policy_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("risk_threshold_low", sa.Integer(), nullable=False),
            sa.Column("risk_threshold_medium", sa.Integer(), nullable=False),
            sa.Column("risk_threshold_high", sa.Integer(), nullable=False),
            sa.Column("risk_threshold_critical", sa.Integer(), nullable=False),
            sa.Column("actions", sa.JSON(), nullable=False),
            sa.Column("scope", sa.JSON(), nullable=True),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("policy_id"),
        )

    # ── 43. niam_adaptive_mfa_sessions ───────────────────────────────────────
    if not _has_table("niam_adaptive_mfa_sessions"):
        op.create_table(
            "niam_adaptive_mfa_sessions",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("mfa_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("account_id", sa.String(length=100), sa.ForeignKey("niam_accounts.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("session_id", sa.String(length=100), sa.ForeignKey("niam_user_sessions.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("mfa_type", sa.String(length=30), nullable=False),
            sa.Column("challenge", sa.String(length=500), nullable=False),
            sa.Column("challenge_expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("attempts", sa.Integer(), nullable=False),
            sa.Column("max_attempts", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, index=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("mfa_id"),
        )

    # ── 44. niam_adaptive_travel_events ──────────────────────────────────────
    if not _has_table("niam_adaptive_travel_events"):
        op.create_table(
            "niam_adaptive_travel_events",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("travel_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("account_id", sa.String(length=100), sa.ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=False, index=True),
            sa.Column("session_id", sa.String(length=100), nullable=True, index=True),
            sa.Column("previous_ip", sa.String(length=45), nullable=True),
            sa.Column("previous_location_city", sa.String(length=200), nullable=True),
            sa.Column("previous_location_country", sa.String(length=200), nullable=True),
            sa.Column("previous_lat", sa.String(length=50), nullable=True),
            sa.Column("previous_lng", sa.String(length=50), nullable=True),
            sa.Column("previous_timestamp", sa.DateTime(timezone=True), nullable=True),
            sa.Column("current_ip", sa.String(length=45), nullable=False),
            sa.Column("current_location_city", sa.String(length=200), nullable=True),
            sa.Column("current_location_country", sa.String(length=200), nullable=True),
            sa.Column("current_lat", sa.String(length=50), nullable=True),
            sa.Column("current_lng", sa.String(length=50), nullable=True),
            sa.Column("current_timestamp", sa.DateTime(timezone=True), nullable=False),
            sa.Column("distance_km", sa.Float(), nullable=True),
            sa.Column("time_delta_minutes", sa.Float(), nullable=True),
            sa.Column("speed_kmh", sa.Float(), nullable=True),
            sa.Column("impossible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("risk_score", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("travel_id"),
        )

    # ── 45. niam_adaptive_session_policies ───────────────────────────────────
    if not _has_table("niam_adaptive_session_policies"):
        op.create_table(
            "niam_adaptive_session_policies",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("policy_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("applies_to", sa.String(length=50), nullable=False, index=True),
            sa.Column("max_sessions", sa.Integer(), nullable=False),
            sa.Column("allow_concurrent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("require_mfa", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("session_timeout_minutes", sa.Integer(), nullable=True),
            sa.Column("inactivity_timeout_minutes", sa.Integer(), nullable=True),
            sa.Column("notify_previous_device", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("terminate_previous_on_new_login", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("enforce_geo_restriction", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("allowed_geo", sa.JSON(), nullable=True),
            sa.Column("enforce_ip_restriction", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("allowed_ips", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("policy_id"),
        )

    # ── ADMIN ───────────────────────────────────────────────────────────────

    # ── 46. niam_admin_portals ───────────────────────────────────────────────
    if not _has_table("niam_admin_portals"):
        op.create_table(
            "niam_admin_portals",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("portal_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("organization_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("name", sa.String(length=300), nullable=False),
            sa.Column("portal_type", sa.String(length=20), nullable=False, index=True),
            sa.Column("features", sa.JSON(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("created_by", sa.String(length=26), sa.ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True),
            sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_access_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("settings", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("portal_id"),
        )
        op.create_index("ix_niam_admin_portals_created_by", "niam_admin_portals", ["created_by"])

    # ── 47. niam_admin_branches ──────────────────────────────────────────────
    if not _has_table("niam_admin_branches"):
        op.create_table(
            "niam_admin_branches",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("branch_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("portal_id", sa.String(length=26), sa.ForeignKey("niam_admin_portals.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("organization_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("name_en", sa.String(length=300), nullable=False),
            sa.Column("name_ar", sa.String(length=300), nullable=False),
            sa.Column("address", sa.Text(), nullable=True),
            sa.Column("phone", sa.String(length=30), nullable=True),
            sa.Column("email", sa.String(length=200), nullable=True),
            sa.Column("manager_person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("branch_id"),
        )
        op.create_index("ix_niam_admin_branches_manager", "niam_admin_branches", ["manager_person_id"])

    # ── 48. niam_admin_facilities ────────────────────────────────────────────
    if not _has_table("niam_admin_facilities"):
        op.create_table(
            "niam_admin_facilities",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("facility_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("branch_id", sa.String(length=26), sa.ForeignKey("niam_admin_branches.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("organization_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("name_en", sa.String(length=300), nullable=False),
            sa.Column("name_ar", sa.String(length=300), nullable=False),
            sa.Column("facility_type", sa.String(length=50), nullable=False),
            sa.Column("license_number", sa.String(length=100), nullable=True),
            sa.Column("accreditation", sa.String(length=200), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("contact", sa.JSON(), nullable=True),
            sa.Column("address", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("facility_id"),
        )

    # ── 49. niam_admin_departments ───────────────────────────────────────────
    if not _has_table("niam_admin_departments"):
        op.create_table(
            "niam_admin_departments",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("dept_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("facility_id", sa.String(length=26), sa.ForeignKey("niam_admin_facilities.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("name_en", sa.String(length=300), nullable=False),
            sa.Column("name_ar", sa.String(length=300), nullable=False),
            sa.Column("dept_type", sa.String(length=50), nullable=True),
            sa.Column("head_person_id", sa.String(length=26), sa.ForeignKey("niam_persons.id", ondelete="SET NULL"), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("dept_id"),
        )
        op.create_index("ix_niam_admin_departments_head", "niam_admin_departments", ["head_person_id"])

    # ── 50. niam_admin_subscriptions ─────────────────────────────────────────
    if not _has_table("niam_admin_subscriptions"):
        op.create_table(
            "niam_admin_subscriptions",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("sub_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("organization_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("plan_type", sa.String(length=50), nullable=False),
            sa.Column("features", sa.JSON(), nullable=True),
            sa.Column("user_limit", sa.Integer(), nullable=True),
            sa.Column("storage_limit", sa.Integer(), nullable=True),
            sa.Column("api_call_limit", sa.Integer(), nullable=True),
            sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
            sa.Column("renewal_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("billing_cycle", sa.String(length=20), nullable=True),
            sa.Column("billing_amount", sa.Integer(), nullable=True),
            sa.Column("currency", sa.String(length=3), nullable=True),
            sa.Column("payment_method", sa.String(length=50), nullable=True),
            sa.Column("auto_renew", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("sub_id"),
        )

    # ── 51. niam_admin_audit_logs ────────────────────────────────────────────
    if not _has_table("niam_admin_audit_logs"):
        op.create_table(
            "niam_admin_audit_logs",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("log_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("organization_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("portal_id", sa.String(length=26), sa.ForeignKey("niam_admin_portals.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("action", sa.String(length=100), nullable=False),
            sa.Column("performed_by", sa.String(length=26), sa.ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True),
            sa.Column("target_type", sa.String(length=50), nullable=False),
            sa.Column("target_id", sa.String(length=100), nullable=True),
            sa.Column("details", sa.JSON(), nullable=True),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("user_agent", sa.Text(), nullable=True),
            sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
            sa.Column("outcome", sa.String(length=20), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("log_id"),
        )
        op.create_index("ix_niam_admin_audit_logs_performed_by", "niam_admin_audit_logs", ["performed_by"])

    # ── 52. niam_admin_fhir_connections ──────────────────────────────────────
    if not _has_table("niam_admin_fhir_connections"):
        op.create_table(
            "niam_admin_fhir_connections",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("conn_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("organization_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("fhir_version", sa.String(length=10), nullable=False),
            sa.Column("base_url", sa.String(length=500), nullable=False),
            sa.Column("auth_type", sa.String(length=20), nullable=False),
            sa.Column("credentials_encrypted", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("last_test_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_test_result", sa.String(length=100), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("conn_id"),
        )

    # ── COMPLIANCE ──────────────────────────────────────────────────────────

    # ── 53. niam_comp_frameworks ─────────────────────────────────────────────
    if not _has_table("niam_comp_frameworks"):
        op.create_table(
            "niam_comp_frameworks",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("framework_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("name", sa.String(length=300), nullable=False),
            sa.Column("framework_type", sa.String(length=50), nullable=False, index=True),
            sa.Column("version", sa.String(length=20), nullable=True),
            sa.Column("requirements", sa.JSON(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("framework_id"),
        )

    # ── 54. niam_comp_checks ─────────────────────────────────────────────────
    if not _has_table("niam_comp_checks"):
        op.create_table(
            "niam_comp_checks",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("check_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("framework_id", sa.String(length=26), sa.ForeignKey("niam_comp_frameworks.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("requirement_id", sa.String(length=100), nullable=False),
            sa.Column("target_type", sa.String(length=50), nullable=False),
            sa.Column("target_id", sa.String(length=100), nullable=False),
            sa.Column("check_type", sa.String(length=20), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("checked_by", sa.String(length=26), sa.ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True),
            sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("evidence", sa.JSON(), nullable=True),
            sa.Column("finding", sa.Text(), nullable=True),
            sa.Column("recommendation", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("check_id"),
        )
        op.create_index("ix_niam_comp_checks_checked_by", "niam_comp_checks", ["checked_by"])

    # ── 55. niam_comp_reports ────────────────────────────────────────────────
    if not _has_table("niam_comp_reports"):
        op.create_table(
            "niam_comp_reports",
            sa.Column("id", sa.String(length=26), nullable=False),
            sa.Column("uuid", sa.String(length=36), nullable=False, index=True),
            sa.Column("report_id", sa.String(length=100), nullable=False, index=True),
            sa.Column("organization_id", sa.String(length=26), sa.ForeignKey("niam_organizations.id", ondelete="CASCADE"), nullable=True, index=True),
            sa.Column("framework_id", sa.String(length=26), sa.ForeignKey("niam_comp_frameworks.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("report_type", sa.String(length=20), nullable=False),
            sa.Column("overall_score", sa.Integer(), nullable=True),
            sa.Column("passed_count", sa.Integer(), nullable=False),
            sa.Column("failed_count", sa.Integer(), nullable=False),
            sa.Column("warning_count", sa.Integer(), nullable=False),
            sa.Column("not_applicable_count", sa.Integer(), nullable=False),
            sa.Column("findings", sa.JSON(), nullable=True),
            sa.Column("recommendations", sa.JSON(), nullable=True),
            sa.Column("generated_by", sa.String(length=26), sa.ForeignKey("niam_accounts.id", ondelete="SET NULL"), nullable=True),
            sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("uuid"),
            sa.UniqueConstraint("report_id"),
        )
        op.create_index("ix_niam_comp_reports_generated_by", "niam_comp_reports", ["generated_by"])

    # ── ALTER TABLE: niam_audit_entries — add chain columns ──────────────────
    if _has_table("niam_audit_entries"):
        if not _has_column("niam_audit_entries", "entry_hash"):
            bind = op.get_bind()
            if bind.dialect.name == "sqlite":
                with op.batch_alter_table("niam_audit_entries", schema=None) as batch_op:
                    batch_op.add_column(sa.Column("entry_hash", sa.String(length=64), nullable=True))
                    try:
                        batch_op.create_unique_constraint("uq_niam_audit_entries_entry_hash", ["entry_hash"])
                    except Exception:
                        pass
            else:
                op.add_column(
                    "niam_audit_entries",
                    sa.Column("entry_hash", sa.String(length=64), nullable=True, index=True),
                )
                try:
                    op.create_unique_constraint("uq_niam_audit_entries_entry_hash", "niam_audit_entries", ["entry_hash"])
                except Exception:
                    pass
        if not _has_column("niam_audit_entries", "previous_hash"):
            op.add_column(
                "niam_audit_entries",
                sa.Column("previous_hash", sa.String(length=64), nullable=True, index=True),
            )

    # ── ALTER TABLE: niam_sessions — add governance columns ──────────────────
    if _has_table("niam_sessions"):
        if not _has_column("niam_sessions", "policy_id"):
            op.add_column(
                "niam_sessions",
                sa.Column("policy_id", sa.String(length=36), nullable=True, index=True),
            )
        if not _has_column("niam_sessions", "governance_action"):
            op.add_column(
                "niam_sessions",
                sa.Column("governance_action", sa.String(length=50), nullable=True),
            )
        if not _has_column("niam_sessions", "risk_score_at_login"):
            op.add_column(
                "niam_sessions",
                sa.Column("risk_score_at_login", sa.Integer(), nullable=True),
            )
        if not _has_column("niam_sessions", "risk_level_at_login"):
            op.add_column(
                "niam_sessions",
                sa.Column("risk_level_at_login", sa.String(length=20), nullable=True),
            )


def downgrade() -> None:
    # ── DROP tables in reverse order (55 new + 2 modified existing) ─────────

    tables = [
        "niam_comp_reports",
        "niam_comp_checks",
        "niam_comp_frameworks",
        "niam_admin_fhir_connections",
        "niam_admin_audit_logs",
        "niam_admin_subscriptions",
        "niam_admin_departments",
        "niam_admin_facilities",
        "niam_admin_branches",
        "niam_admin_portals",
        "niam_adaptive_session_policies",
        "niam_adaptive_travel_events",
        "niam_adaptive_mfa_sessions",
        "niam_adaptive_risk_policies",
        "niam_adaptive_risk_events",
        "niam_notif_preferences",
        "niam_notif_queue",
        "niam_notif_templates",
        "niam_wf_notifications",
        "niam_wf_approvals",
        "niam_wf_instances",
        "niam_wf_definitions",
        "niam_cert_api_keys",
        "niam_cert_crls",
        "niam_cert_certificates",
        "niam_cert_authorities",
        "niam_fed_sessions",
        "niam_fed_agreements",
        "niam_fed_cross_org_trust",
        "niam_fed_links",
        "niam_fed_identities",
        "niam_fed_providers",
        "niam_lifecycle_consents",
        "niam_lifecycle_family_links",
        "niam_lifecycle_guardians",
        "niam_lifecycle_citizen",
        "niam_lifecycle_gov_appointments",
        "niam_lifecycle_workforce_requests",
        "niam_lifecycle_enterprise_steps",
        "niam_lifecycle_enterprise_reg",
        "niam_trust_evaluations",
        "niam_trust_federation",
        "niam_trust_proofing",
        "niam_trust_assurance_profiles",
        "niam_trust_anchors",
        "niam_trust_frameworks",
        "niam_gov_appeals",
        "niam_gov_restorations",
        "niam_gov_certifications",
        "niam_gov_review_boards",
        "niam_gov_councils",
        "niam_gov_policy_approvals",
        "niam_gov_registry",
        "niam_gov_suspensions",
        "niam_gov_authorities",
    ]

    for table in tables:
        if _has_table(table):
            op.drop_table(table)

    # ── Revert audit columns ────────────────────────────────────────────────
    if _has_table("niam_audit_entries"):
        if _has_column("niam_audit_entries", "entry_hash"):
            op.drop_constraint("uq_niam_audit_entries_entry_hash", "niam_audit_entries", type_="unique")
            op.drop_column("niam_audit_entries", "entry_hash")
        if _has_column("niam_audit_entries", "previous_hash"):
            op.drop_column("niam_audit_entries", "previous_hash")

    # ── Revert session columns ──────────────────────────────────────────────
    if _has_table("niam_sessions"):
        for col in ("policy_id", "governance_action", "risk_score_at_login", "risk_level_at_login"):
            if _has_column("niam_sessions", col):
                op.drop_column("niam_sessions", col)
