"""Create government popular-clinic clinical and ticketing domain.

Revision ID: 20260815_0021
Revises: 20260815_0020
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260815_0021"
down_revision = "20260815_0020"
branch_labels = None
depends_on = None

MONEY = sa.Numeric(18, 2)


def upgrade() -> None:
    op.create_table(
        "popular_clinics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("province_id", sa.Integer(), nullable=False),
        sa.Column("administrative_unit_code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("opening_time", sa.String(5), nullable=False, server_default="14:00"),
        sa.Column("closing_time", sa.String(5), nullable=False, server_default="18:00"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("province_id", "administrative_unit_code", name="uq_popular_clinic_admin_unit"),
    )
    op.create_index("ix_popular_clinics_lab_id", "popular_clinics", ["lab_id"])
    op.create_index("ix_popular_clinics_province_id", "popular_clinics", ["province_id"])
    op.create_index("ix_popular_clinics_is_active", "popular_clinics", ["is_active"])
    op.create_index("ix_popular_clinics_lab_active", "popular_clinics", ["lab_id", "is_active"])

    op.create_table(
        "popular_chronic_patient_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("popular_clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attending_doctor_id", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("conditions", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="active"),
        sa.Column("enrolled_at", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("clinic_id", "patient_id", name="uq_popular_chronic_clinic_patient"),
    )
    op.create_index("ix_popular_chronic_patient_clinic", "popular_chronic_patient_profiles", ["clinic_id", "patient_id"])
    op.create_index("ix_popular_chronic_patient_profiles_status", "popular_chronic_patient_profiles", ["status"])

    op.create_table(
        "popular_treatment_plans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("patient_profile_id", sa.Integer(), sa.ForeignKey("popular_chronic_patient_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prescribed_by_id", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("medication_name", sa.String(255), nullable=False),
        sa.Column("medication_code", sa.String(128), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("dosage", sa.String(255), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="active"),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("quantity > 0", name="ck_popular_treatment_quantity_positive"),
    )
    op.create_index("ix_popular_treatment_patient_status", "popular_treatment_plans", ["patient_profile_id", "status"])

    op.create_table(
        "popular_monthly_dispensations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("popular_clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("treatment_plan_id", sa.Integer(), sa.ForeignKey("popular_treatment_plans.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_by_id", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("dispensed_by_id", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("dispense_year", sa.Integer(), nullable=False),
        sa.Column("dispense_month", sa.Integer(), nullable=False),
        sa.Column("dispensed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("medication_name", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("dosage", sa.String(255), nullable=False),
        sa.Column("blood_pressure", sa.String(64), nullable=True),
        sa.Column("blood_tests", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="dispensed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("clinic_id", "patient_id", "dispense_year", "dispense_month", name="uq_popular_monthly_dispense_once"),
        sa.CheckConstraint("dispense_month >= 1 AND dispense_month <= 12", name="ck_popular_dispense_month"),
        sa.CheckConstraint("quantity > 0", name="ck_popular_dispense_quantity_positive"),
    )
    op.create_index("ix_popular_dispensation_clinic_month", "popular_monthly_dispensations", ["clinic_id", "dispense_year", "dispense_month"])
    op.create_index("ix_popular_monthly_dispensations_status", "popular_monthly_dispensations", ["status"])

    op.create_table(
        "popular_service_catalog",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("popular_clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("price_cash", MONEY, nullable=False, server_default="0"),
        sa.Column("price_electronic", MONEY, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("clinic_id", "service_code", name="uq_popular_service_code"),
        sa.CheckConstraint("price_cash >= 0 AND price_electronic >= 0", name="ck_popular_service_prices"),
    )
    op.create_index("ix_popular_service_catalog_is_active", "popular_service_catalog", ["is_active"])

    op.create_table(
        "popular_service_visits",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("popular_clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=True),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("popular_service_catalog.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("provider_id", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("report", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="completed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_popular_service_visit_patient", "popular_service_visits", ["clinic_id", "patient_id", "created_at"])
    op.create_index("ix_popular_service_visits_status", "popular_service_visits", ["status"])

    op.create_table(
        "popular_clinical_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("popular_clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("record_type", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_popular_clinical_record_patient", "popular_clinical_records", ["clinic_id", "patient_id", "created_at"])

    op.create_table(
        "popular_clinic_tickets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("popular_clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("ticket_number", sa.String(64), nullable=False),
        sa.Column("service_code", sa.String(64), nullable=False),
        sa.Column("payment_method", sa.String(24), nullable=False),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column("payment_invoice_id", sa.String(36), nullable=True),
        sa.Column("payment_intent_id", sa.String(36), nullable=True),
        sa.Column("issued_by_id", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("captured_by_id", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("cash_shift_id", sa.String(36), nullable=True),
        sa.Column("payment_reference", sa.String(128), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="payment_pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("clinic_id", "ticket_number", name="uq_popular_ticket_number"),
    )
    op.create_index("ix_popular_ticket_clinic_status", "popular_clinic_tickets", ["clinic_id", "status"])
    op.create_index("ix_popular_clinic_tickets_payment_invoice_id", "popular_clinic_tickets", ["payment_invoice_id"])
    op.create_index("ix_popular_clinic_tickets_payment_intent_id", "popular_clinic_tickets", ["payment_intent_id"])
    op.create_index("ix_popular_clinic_tickets_cash_shift_id", "popular_clinic_tickets", ["cash_shift_id"])
    op.create_index("ix_popular_clinic_tickets_status", "popular_clinic_tickets", ["status"])

    op.create_table(
        "popular_clinic_workers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("clinic_id", sa.Integer(), sa.ForeignKey("popular_clinics.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("worker_role", sa.String(64), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("clinic_id", "user_id", "worker_role", name="uq_popular_clinic_worker_role"),
    )
    op.create_index("ix_popular_clinic_worker_active", "popular_clinic_workers", ["clinic_id", "active"])


def downgrade() -> None:
    for table in (
        "popular_clinic_workers",
        "popular_clinic_tickets",
        "popular_clinical_records",
        "popular_service_visits",
        "popular_service_catalog",
        "popular_monthly_dispensations",
        "popular_treatment_plans",
        "popular_chronic_patient_profiles",
        "popular_clinics",
    ):
        op.drop_table(table)
