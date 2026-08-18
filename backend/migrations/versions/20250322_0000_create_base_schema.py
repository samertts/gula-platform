"""Create base schema — all core tables.

This migration must run FIRST on a fresh database.
All tables are created inside _table_exists() guards so the migration
is fully idempotent on databases that were bootstrapped via create_all().

Tables created (FK-dependency order):
  1.  labs
  2.  test_types
  3.  users
  4.  lab_users
  5.  patients
  6.  lab_orders
  7.  lab_results
  8.  audit_logs
  9.  outbox_events
  10. samples
  11. quality_controls
  12. lab_subscriptions
  13. upgrade_requests
  14. upgrade_demand_scores
  15. feature_flags
  16. idempotency_keys

Revision ID : 20250322_0000
Revises     : (none — initial migration)
Create Date : 2025-03-22
"""

from alembic import context, op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision      = "20250322_0000"
down_revision = None
branch_labels = None
depends_on    = None


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _table_exists(table: str) -> bool:
    # Offline SQL generation has no inspectable connection. The initial
    # migration is intended for a fresh schema, so emit the CREATE statements
    # in offline mode; preserve idempotent inspection for online upgrades.
    if context.is_offline_mode():
        return False
    return inspect(op.get_bind()).has_table(table)


def _pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


# ─── Upgrade ─────────────────────────────────────────────────────────────────

def upgrade() -> None:

    # ── 1. labs ───────────────────────────────────────────────────────────────
    if not _table_exists("labs"):
        op.create_table(
            "labs",
            sa.Column("id",             sa.Integer(),     primary_key=True, autoincrement=True),
            sa.Column("name",           sa.String(200),   nullable=False),
            sa.Column("license_number", sa.String(100),   nullable=True,  unique=True),
            sa.Column("lab_type",       sa.String(50),    nullable=True),
            sa.Column("director_name",  sa.String(200),   nullable=True),
            sa.Column("website",        sa.String(300),   nullable=True),
            sa.Column("city",           sa.String(100),   nullable=True),
            sa.Column("address",        sa.String(500),   nullable=True),
            sa.Column("phone",          sa.String(20),    nullable=True),
            sa.Column("is_active",      sa.Boolean(),     nullable=False, server_default="true"),
            sa.Column("created_at",     sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_labs_id",        "labs", ["id"])
        op.create_index("ix_labs_is_active",  "labs", ["is_active"])
        op.create_index("ix_labs_lab_type",   "labs", ["lab_type"])

    # ── 2. test_types ─────────────────────────────────────────────────────────
    if not _table_exists("test_types"):
        op.create_table(
            "test_types",
            sa.Column("id",                    sa.Integer(),    primary_key=True, autoincrement=True),
            sa.Column("test_code",             sa.String(50),   nullable=False,  unique=True),
            sa.Column("test_name",             sa.String(200),  nullable=False),
            sa.Column("test_name_ar",          sa.String(200),  nullable=True),
            sa.Column("category",              sa.String(50),   nullable=True),
            sa.Column("unit",                  sa.String(20),   nullable=True),
            sa.Column("normal_range_low",      sa.Float(),      nullable=True),
            sa.Column("normal_range_high",     sa.Float(),      nullable=True),
            sa.Column("interpretation_low",    sa.String(500),  nullable=True),
            sa.Column("interpretation_normal", sa.String(500),  nullable=True),
            sa.Column("interpretation_high",   sa.String(500),  nullable=True),
            sa.Column("interpretation_low_ar",    sa.String(500), nullable=True),
            sa.Column("interpretation_normal_ar", sa.String(500), nullable=True),
            sa.Column("interpretation_high_ar",   sa.String(500), nullable=True),
            sa.Column("created_at",            sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_test_types_id", "test_types", ["id"])

    # ── 3. users ──────────────────────────────────────────────────────────────
    if not _table_exists("users"):
        op.create_table(
            "users",
            sa.Column("id",               sa.Integer(),    primary_key=True, autoincrement=True),
            sa.Column("email",            sa.String(100),  nullable=True,  unique=True),
            sa.Column("phone",            sa.String(20),   nullable=True,  unique=True),
            sa.Column("password_hash",    sa.String(255),  nullable=False),
            sa.Column("full_name",        sa.String(200),  nullable=False),
            sa.Column("role",             sa.String(50),   nullable=False, server_default="citizen"),
            sa.Column("lab_id",           sa.Integer(),    sa.ForeignKey("labs.id", ondelete="SET NULL"), nullable=True),
            sa.Column("is_active",        sa.Boolean(),    nullable=False, server_default="true"),
            sa.Column("is_verified",      sa.Boolean(),    nullable=False, server_default="false"),
            sa.Column("national_id_hash", sa.String(255),  nullable=True),
            sa.Column("license_number",   sa.String(100),  nullable=True),
            sa.Column("specialty",        sa.String(200),  nullable=True),
            sa.Column("created_at",       sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("last_login",       sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_users_id",               "users", ["id"])
        op.create_index("ix_users_email",            "users", ["email"])
        op.create_index("ix_users_phone",            "users", ["phone"])
        op.create_index("ix_users_national_id_hash", "users", ["national_id_hash"])

    # ── 4. lab_users ──────────────────────────────────────────────────────────
    # Includes columns added by migration 0001 (national_id_hash, province_id,
    # created_by) so 0001 is a no-op on fresh databases.
    if not _table_exists("lab_users"):
        op.create_table(
            "lab_users",
            sa.Column("id",               sa.Integer(),    primary_key=True, autoincrement=True),
            sa.Column("lab_id",           sa.Integer(),    sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name",             sa.String(200),  nullable=False),
            sa.Column("email",            sa.String(100),  nullable=False, unique=True),
            sa.Column("password_hash",    sa.String(255),  nullable=False),
            sa.Column("role",             sa.String(50),   nullable=False, server_default="staff"),
            sa.Column("is_active",        sa.Boolean(),    nullable=False, server_default="true"),
            sa.Column("perm_version",     sa.Integer(),    nullable=False, server_default="1"),
            sa.Column("created_at",       sa.DateTime(timezone=True), server_default=sa.func.now()),
            # Added by migration 0001 — included here so 0001 becomes a no-op
            sa.Column("national_id_hash", sa.String(255),  nullable=True, unique=True),
            sa.Column("province_id",      sa.Integer(),    nullable=True),
            sa.Column("created_by",       sa.Integer(),    sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
        )
        op.create_index("ix_lab_users_id",               "lab_users", ["id"])
        op.create_index("ix_lab_users_lab_id",           "lab_users", ["lab_id"])
        op.create_index("ix_lab_users_email",            "lab_users", ["email"])
        op.create_index("ix_lab_users_role",             "lab_users", ["role"])
        op.create_index("ix_lab_users_is_active",        "lab_users", ["is_active"])
        op.create_index("ix_lab_users_national_id_hash", "lab_users", ["national_id_hash"], unique=True)
        op.create_index("ix_lab_users_province_id",      "lab_users", ["province_id"])

    # ── 5. patients ───────────────────────────────────────────────────────────
    # Includes columns added by migrations 0005 (email nullable) and 0006
    # (family_id_hash, guardian_id) so those become no-ops on fresh databases.
    if not _table_exists("patients"):
        op.create_table(
            "patients",
            sa.Column("id",               sa.Integer(),    primary_key=True, autoincrement=True),
            sa.Column("lab_id",           sa.Integer(),    sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("health_id",        sa.String(20),   nullable=True, unique=True),
            sa.Column("national_id_hash", sa.String(255),  nullable=True),
            sa.Column("family_id_hash",   sa.String(255),  nullable=True),
            sa.Column("guardian_id",      sa.Integer(),    sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
            sa.Column("full_name",        sa.String(200),  nullable=False),
            sa.Column("phone",            sa.String(20),   nullable=False),
            sa.Column("birth_date",       sa.Date(),       nullable=True),
            sa.Column("gender",           sa.String(1),    nullable=True),
            sa.Column("email",            sa.String(100),  nullable=True),
            sa.Column("created_at",       sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_patients_id",               "patients", ["id"])
        op.create_index("ix_patients_health_id",        "patients", ["health_id"])
        op.create_index("ix_patients_national_id_hash", "patients", ["national_id_hash"])
        op.create_index("ix_patients_family_id_hash",   "patients", ["family_id_hash"])
        op.create_index("ix_patients_guardian_id",      "patients", ["guardian_id"])
        op.create_index("ix_patients_phone",            "patients", ["phone"])
        op.create_index("ix_patients_lab_id",           "patients", ["lab_id"])
        op.create_index("ix_patients_lab_phone",        "patients", ["lab_id", "phone"])
        op.create_index("ix_patients_lab_nid",          "patients", ["lab_id", "national_id_hash"])

    # ── 6. lab_orders ─────────────────────────────────────────────────────────
    # Includes columns added by migrations 0002 (doctor_user_id),
    # 0003 (validated_by, validated_at, locked_at), 0004 (version)
    # so those migrations become no-ops on fresh databases.
    if not _table_exists("lab_orders"):
        op.create_table(
            "lab_orders",
            sa.Column("id",             sa.Integer(),    primary_key=True, autoincrement=True),
            sa.Column("patient_id",     sa.Integer(),    sa.ForeignKey("patients.id", ondelete="CASCADE"),  nullable=False),
            sa.Column("lab_id",         sa.Integer(),    sa.ForeignKey("labs.id", ondelete="CASCADE"),      nullable=False),
            sa.Column("doctor_name",    sa.String(200),  nullable=True),
            # Added by migration 0002
            sa.Column("doctor_user_id", sa.Integer(),    sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("status",         sa.String(20),   nullable=False, server_default="pending"),
            # Added by migration 0003
            sa.Column("validated_by",   sa.Integer(),    sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("validated_at",   sa.DateTime(timezone=True), nullable=True),
            sa.Column("locked_at",      sa.DateTime(timezone=True), nullable=True),
            # Added by migration 0004
            sa.Column("version",        sa.Integer(),    nullable=False, server_default="1"),
            sa.Column("created_at",     sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_lab_orders_id",             "lab_orders", ["id"])
        op.create_index("ix_lab_orders_patient_id",     "lab_orders", ["patient_id"])
        op.create_index("ix_lab_orders_lab_id",         "lab_orders", ["lab_id"])
        op.create_index("ix_lab_orders_status",         "lab_orders", ["status"])
        op.create_index("ix_lab_orders_created_at",     "lab_orders", ["created_at"])
        op.create_index("ix_lab_orders_doctor_user_id", "lab_orders", ["doctor_user_id"])
        op.create_index("ix_lab_orders_validated_by",   "lab_orders", ["validated_by"])
        if _pg():
            op.execute(text(
                "CREATE INDEX ix_lab_orders_status_pending "
                "ON lab_orders (lab_id, created_at DESC) WHERE status = 'pending'"
            ))

    # ── 7. lab_results ────────────────────────────────────────────────────────
    # Includes columns added by migration 0009 (clinical_engine_version)
    # and 0012 (version) so those become no-ops on fresh databases.
    if not _table_exists("lab_results"):
        op.create_table(
            "lab_results",
            sa.Column("id",             sa.Integer(),    primary_key=True, autoincrement=True),
            sa.Column("order_id",       sa.Integer(),    sa.ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False),
            sa.Column("test_type_id",   sa.Integer(),    sa.ForeignKey("test_types.id", ondelete="SET NULL"), nullable=True),
            sa.Column("test_name",      sa.String(200),  nullable=False),
            sa.Column("value",          sa.Float(),      nullable=True),
            sa.Column("value_text",     sa.String(200),  nullable=True),
            sa.Column("unit",           sa.String(20),   nullable=True),
            sa.Column("normal_range_low",  sa.Float(),   nullable=True),
            sa.Column("normal_range_high", sa.Float(),   nullable=True),
            sa.Column("flag",           sa.String(10),   nullable=True),
            sa.Column("token",          sa.String(64),   nullable=False, unique=True),
            sa.Column("token_hash",     sa.String(64),   nullable=True,  unique=True),
            sa.Column("expires_at",     sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at",     sa.DateTime(timezone=True), server_default=sa.func.now()),
            # Added by migration 0009
            sa.Column("clinical_engine_version", sa.String(20), nullable=True),
            # Added by migration 0012
            sa.Column("version",        sa.Integer(),    nullable=False, server_default="1"),
        )
        op.create_index("ix_lab_results_id",         "lab_results", ["id"])
        op.create_index("ix_lab_results_order_id",   "lab_results", ["order_id"])
        op.create_index("ix_lab_results_flag",       "lab_results", ["flag"])
        op.create_index("ix_lab_results_token",      "lab_results", ["token"])
        op.create_index("ix_lab_results_token_hash", "lab_results", ["token_hash"])
        op.create_index("ix_lab_results_expires_at", "lab_results", ["expires_at"])

    # ── 8. audit_logs ─────────────────────────────────────────────────────────
    # Includes chain_hash added by migration 0009.
    if not _table_exists("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id",            sa.Integer(),    primary_key=True, autoincrement=True),
            sa.Column("user_id",       sa.Integer(),    nullable=True),
            sa.Column("user_role",     sa.String(50),   nullable=True),
            sa.Column("action",        sa.String(50),   nullable=False),
            sa.Column("resource_type", sa.String(50),   nullable=False),
            sa.Column("resource_id",   sa.Integer(),    nullable=True),
            sa.Column("details",       sa.Text(),       nullable=True),
            sa.Column("ip_address",    sa.String(45),   nullable=True),
            sa.Column("created_at",    sa.DateTime(timezone=True), server_default=sa.func.now()),
            # Added by migration 0009
            sa.Column("chain_hash",    sa.String(64),   nullable=True),
        )
        op.create_index("ix_audit_logs_id",           "audit_logs", ["id"])
        op.create_index("ix_audit_logs_user_id",      "audit_logs", ["user_id"])
        op.create_index("ix_audit_logs_action",       "audit_logs", ["action"])
        op.create_index("ix_audit_logs_resource_type","audit_logs", ["resource_type"])
        op.create_index("ix_audit_logs_created_at",   "audit_logs", ["created_at"])
        op.create_index("ix_audit_logs_chain_hash",   "audit_logs", ["chain_hash"])
        op.create_index("ix_audit_logs_user_created", "audit_logs", ["user_id", "created_at"])

    # ── 9. outbox_events ──────────────────────────────────────────────────────
    # Also created (idempotently) by migration 0004.
    if not _table_exists("outbox_events"):
        op.create_table(
            "outbox_events",
            sa.Column("id",             sa.Integer(),    primary_key=True, autoincrement=True),
            sa.Column("event_type",     sa.String(100),  nullable=False),
            sa.Column("aggregate_type", sa.String(100),  nullable=True),
            sa.Column("aggregate_id",   sa.Integer(),    nullable=True),
            sa.Column("payload",        sa.Text(),       nullable=False),
            sa.Column("status",         sa.String(20),   nullable=False, server_default="pending"),
            sa.Column("attempts",       sa.Integer(),    nullable=False, server_default="0"),
            sa.Column("last_error",     sa.Text(),       nullable=True),
            sa.Column("created_at",     sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("processed_at",   sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_outbox_events_event_type",   "outbox_events", ["event_type"])
        op.create_index("ix_outbox_events_aggregate_id", "outbox_events", ["aggregate_id"])
        op.create_index("ix_outbox_events_created_at",   "outbox_events", ["created_at"])
        if _pg():
            op.execute(text(
                "CREATE INDEX ix_outbox_events_pending "
                "ON outbox_events (created_at ASC) "
                "WHERE status IN ('pending', 'failed')"
            ))

    # ── 10. samples ───────────────────────────────────────────────────────────
    if not _table_exists("samples"):
        op.create_table(
            "samples",
            sa.Column("id",               sa.Integer(),    primary_key=True, autoincrement=True),
            sa.Column("order_id",         sa.Integer(),    sa.ForeignKey("lab_orders.id", ondelete="CASCADE"), nullable=False),
            sa.Column("barcode",          sa.String(20),   nullable=False, unique=True),
            sa.Column("sample_type",      sa.String(50),   nullable=False),
            sa.Column("collection_time",  sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("collected_by",     sa.String(200),  nullable=True),
            sa.Column("status",           sa.String(30),   nullable=False, server_default="collected"),
            sa.Column("rejection_reason", sa.Text(),       nullable=True),
            sa.Column("notes",            sa.Text(),       nullable=True),
            sa.Column("storage_location", sa.String(100),  nullable=True),
            sa.Column("created_at",       sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_samples_id",       "samples", ["id"])
        op.create_index("ix_samples_order_id", "samples", ["order_id"])
        op.create_index("ix_samples_barcode",  "samples", ["barcode"])
        op.create_index("ix_samples_status",   "samples", ["status"])

    # ── 11. quality_controls ──────────────────────────────────────────────────
    if not _table_exists("quality_controls"):
        op.create_table(
            "quality_controls",
            sa.Column("id",             sa.Integer(),    primary_key=True, autoincrement=True),
            sa.Column("lab_id",         sa.Integer(),    sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("test_code",      sa.String(50),   nullable=False),
            sa.Column("instrument_name",sa.String(200),  nullable=True),
            sa.Column("lot_number",     sa.String(100),  nullable=True),
            sa.Column("level",          sa.String(20),   nullable=False),
            sa.Column("expected_value", sa.Float(),      nullable=False),
            sa.Column("measured_value", sa.Float(),      nullable=False),
            sa.Column("sd",             sa.Float(),      nullable=True),
            sa.Column("unit",           sa.String(30),   nullable=True),
            sa.Column("status",         sa.String(20),   nullable=False, server_default="pass"),
            sa.Column("violation",      sa.String(50),   nullable=True),
            sa.Column("notes",          sa.Text(),       nullable=True),
            sa.Column("performed_by",   sa.String(200),  nullable=True),
            sa.Column("created_at",     sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_quality_controls_id",        "quality_controls", ["id"])
        op.create_index("ix_quality_controls_lab_id",    "quality_controls", ["lab_id"])
        op.create_index("ix_quality_controls_test_code", "quality_controls", ["test_code"])

    # ── 12. lab_subscriptions ─────────────────────────────────────────────────
    if not _table_exists("lab_subscriptions"):
        op.create_table(
            "lab_subscriptions",
            sa.Column("id",                  sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("lab_id",              sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("tier",                sa.String(30), nullable=False, server_default="starter"),
            sa.Column("deployment_mode",     sa.String(30), nullable=False, server_default="single"),
            sa.Column("security_level",      sa.String(30), nullable=False, server_default="standard"),
            sa.Column("is_active",           sa.Boolean(),  nullable=False, server_default="true"),
            sa.Column("trial_ends_at",       sa.DateTime(timezone=True), nullable=True),
            sa.Column("billing_cycle",       sa.String(20), nullable=True, server_default="monthly"),
            sa.Column("monthly_price_usd",   sa.Float(),    nullable=True, server_default="0"),
            sa.Column("max_patients",        sa.Integer(),  nullable=True, server_default="500"),
            sa.Column("max_staff",           sa.Integer(),  nullable=True, server_default="5"),
            sa.Column("max_branches",        sa.Integer(),  nullable=True, server_default="1"),
            sa.Column("max_orders_per_day",  sa.Integer(),  nullable=True, server_default="100"),
            sa.Column("max_ai_calls_per_day",sa.Integer(),  nullable=True, server_default="0"),
            sa.Column("notes",               sa.Text(),     nullable=True),
            sa.Column("activated_at",        sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("expires_at",          sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at",          sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at",          sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_lab_subscriptions_id",     "lab_subscriptions", ["id"])
        op.create_index("ix_lab_subscriptions_lab_id", "lab_subscriptions", ["lab_id"])
        op.create_index("ix_lab_subscriptions_tier",   "lab_subscriptions", ["tier"])

    # ── 13. upgrade_requests ──────────────────────────────────────────────────
    if not _table_exists("upgrade_requests"):
        op.create_table(
            "upgrade_requests",
            sa.Column("id",                    sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("lab_id",                sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("requester_id",          sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("target_tier",           sa.String(30), nullable=False),
            sa.Column("target_deployment_mode",sa.String(30), nullable=True),
            sa.Column("target_security_level", sa.String(30), nullable=True),
            sa.Column("reason",                sa.Text(),    nullable=True),
            sa.Column("status",                sa.String(20), nullable=False, server_default="pending"),
            sa.Column("weight",                sa.Float(),   nullable=True, server_default="1.0"),
            sa.Column("reviewed_by",           sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("reviewed_at",           sa.DateTime(timezone=True), nullable=True),
            sa.Column("review_note",           sa.Text(),   nullable=True),
            sa.Column("created_at",            sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_upgrade_requests_id",         "upgrade_requests", ["id"])
        op.create_index("ix_upgrade_requests_lab_id",     "upgrade_requests", ["lab_id"])
        op.create_index("ix_upgrade_requests_status",     "upgrade_requests", ["status"])
        op.create_index("ix_upgrade_requests_created_at", "upgrade_requests", ["created_at"])
        op.create_index("ix_upgrade_requests_lab_status", "upgrade_requests", ["lab_id", "status"])

    # ── 14. upgrade_demand_scores ─────────────────────────────────────────────
    if not _table_exists("upgrade_demand_scores"):
        op.create_table(
            "upgrade_demand_scores",
            sa.Column("id",               sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("lab_id",           sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("raw_score",        sa.Float(),   nullable=True, server_default="0"),
            sa.Column("unique_requesters",sa.Integer(), nullable=True, server_default="0"),
            sa.Column("weighted_score",   sa.Float(),   nullable=True, server_default="0"),
            sa.Column("last_request_at",  sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at",       sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_upgrade_demand_scores_id",     "upgrade_demand_scores", ["id"])
        op.create_index("ix_upgrade_demand_scores_lab_id", "upgrade_demand_scores", ["lab_id"])

    # ── 15. feature_flags ─────────────────────────────────────────────────────
    if not _table_exists("feature_flags"):
        op.create_table(
            "feature_flags",
            sa.Column("id",          sa.Integer(),    primary_key=True, autoincrement=True),
            sa.Column("lab_id",      sa.Integer(),    sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("feature_key", sa.String(100),  nullable=False),
            sa.Column("is_enabled",  sa.Boolean(),    nullable=False, server_default="true"),
            sa.Column("reason",      sa.String(300),  nullable=True),
            sa.Column("set_by",      sa.Integer(),    sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("expires_at",  sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_feature_flags_id",      "feature_flags", ["id"])
        op.create_index("ix_feature_flags_lab_id",  "feature_flags", ["lab_id"])
        op.create_index("ix_feature_flags_lab_key", "feature_flags", ["lab_id", "feature_key"], unique=True)

    # ── 16. idempotency_keys ──────────────────────────────────────────────────
    # Also created (idempotently) by migration 0004.
    if not _table_exists("idempotency_keys"):
        op.create_table(
            "idempotency_keys",
            sa.Column("key",          sa.String(255), primary_key=True),
            sa.Column("lab_id",       sa.Integer(),   sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=True),
            sa.Column("endpoint",     sa.String(255), nullable=True),
            sa.Column("status_code",  sa.Integer(),   nullable=True),
            sa.Column("response_body",sa.Text(),      nullable=True),
            sa.Column("created_at",   sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_idempotency_keys_lab_id",    "idempotency_keys", ["lab_id"])
        op.create_index("ix_idempotency_keys_created_at","idempotency_keys", ["created_at"])


# ─── Downgrade ────────────────────────────────────────────────────────────────

def downgrade() -> None:
    # Drop in reverse FK order
    for table in [
        "idempotency_keys",
        "feature_flags",
        "upgrade_demand_scores",
        "upgrade_requests",
        "lab_subscriptions",
        "quality_controls",
        "samples",
        "outbox_events",
        "audit_logs",
        "lab_results",
        "lab_orders",
        "patients",
        "lab_users",
        "users",
        "test_types",
        "labs",
    ]:
        if _table_exists(table):
            op.drop_table(table)
