"""GULA Blood Network (GBN) — create all blood-network tables.

New tables (all prefixed gbn_):
  gbn_donors          — blood donor registry
  gbn_blood_units     — individual units + components (whole/RBC/plasma/platelets/cryo)
  gbn_plasma_products — manufactured plasma-derived products (Factor VIII, Albumin, IVIG…)
  gbn_blood_requests  — hospital/clinic requests for blood
  gbn_transfusions    — recorded transfusion events with crossmatch + reaction tracking
  gbn_blood_transfers — inter-lab unit transfers for national coordination

All tables are wrapped in _table_exists() guards → fully idempotent.
All new columns are nullable or have server_default → safe on existing DBs.

Revision ID : 20260402_0013
Revises     : 20260329_0012
Create Date : 2026-04-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text

revision      = "20260402_0013"
down_revision = "20260329_0012"
branch_labels = None
depends_on    = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _pg() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:

    # ── 1. gbn_donors ─────────────────────────────────────────────────────────
    if not _table_exists("gbn_donors"):
        op.create_table(
            "gbn_donors",
            sa.Column("id",               sa.Integer(),    primary_key=True, autoincrement=True),
            sa.Column("user_id",          sa.Integer(),    sa.ForeignKey("users.id",  ondelete="SET NULL"),  nullable=True),
            sa.Column("lab_id",           sa.Integer(),    sa.ForeignKey("labs.id",   ondelete="SET NULL"),  nullable=True),
            sa.Column("full_name",        sa.String(200),  nullable=False),
            sa.Column("national_id_hash", sa.String(255),  nullable=True),
            sa.Column("phone",            sa.String(20),   nullable=True),
            sa.Column("blood_type",       sa.String(5),    nullable=False),
            sa.Column("gender",           sa.String(1),    nullable=True),
            sa.Column("birth_date",       sa.Date(),       nullable=True),
            sa.Column("city",             sa.String(100),  nullable=True),
            sa.Column("eligibility_status",  sa.String(30), nullable=False, server_default="eligible"),
            sa.Column("deferral_reason",     sa.Text(),     nullable=True),
            sa.Column("deferral_until",      sa.Date(),     nullable=True),
            sa.Column("last_donation_date",  sa.Date(),     nullable=True),
            sa.Column("total_donations",     sa.Integer(),  nullable=False, server_default="0"),
            sa.Column("last_hb_g_dl",        sa.Float(),    nullable=True),
            sa.Column("last_weight_kg",      sa.Float(),    nullable=True),
            sa.Column("is_active",           sa.Boolean(),  nullable=False, server_default="true"),
            sa.Column("notes",               sa.Text(),     nullable=True),
            sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at",  sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_gbn_donors_id",          "gbn_donors", ["id"])
        op.create_index("ix_gbn_donors_user_id",     "gbn_donors", ["user_id"])
        op.create_index("ix_gbn_donors_lab_id",      "gbn_donors", ["lab_id"])
        op.create_index("ix_gbn_donors_blood_type",  "gbn_donors", ["blood_type"])
        op.create_index("ix_gbn_donors_eligibility", "gbn_donors", ["eligibility_status"])
        op.create_index("ix_gbn_donors_city",        "gbn_donors", ["city"])
        op.create_index("ix_gbn_donors_phone",       "gbn_donors", ["phone"])
        op.create_index("ix_gbn_donors_nid",         "gbn_donors", ["national_id_hash"])
        if _pg():
            op.execute(text("""
                ALTER TABLE gbn_donors ADD CONSTRAINT ck_gbn_donors_blood_type
                CHECK (blood_type IN ('A+','A-','B+','B-','AB+','AB-','O+','O-'))
            """))

    # ── 2. gbn_blood_units ────────────────────────────────────────────────────
    if not _table_exists("gbn_blood_units"):
        op.create_table(
            "gbn_blood_units",
            sa.Column("id",             sa.Integer(),    primary_key=True, autoincrement=True),
            sa.Column("lab_id",         sa.Integer(),    sa.ForeignKey("labs.id",       ondelete="RESTRICT"), nullable=False),
            sa.Column("donor_id",       sa.Integer(),    sa.ForeignKey("gbn_donors.id", ondelete="SET NULL"), nullable=True),
            sa.Column("barcode",        sa.String(30),   nullable=False, unique=True),
            sa.Column("blood_type",     sa.String(5),    nullable=False),
            sa.Column("component",      sa.String(20),   nullable=False),
            sa.Column("volume_ml",      sa.Integer(),    nullable=True),
            sa.Column("collection_date",sa.Date(),       nullable=False),
            sa.Column("expiry_date",    sa.Date(),       nullable=False),
            sa.Column("status",         sa.String(20),   nullable=False, server_default="quarantine"),
            sa.Column("storage_location",  sa.String(100), nullable=True),
            sa.Column("storage_temp_c",    sa.Float(),     nullable=True),
            sa.Column("temp_alert_flag",   sa.Boolean(),   nullable=False, server_default="false"),
            sa.Column("hiv_screened",      sa.Boolean(),   nullable=True),
            sa.Column("hbsag_screened",    sa.Boolean(),   nullable=True),
            sa.Column("hcv_screened",      sa.Boolean(),   nullable=True),
            sa.Column("syphilis_screened", sa.Boolean(),   nullable=True),
            sa.Column("screening_passed",  sa.Boolean(),   nullable=True),
            sa.Column("collected_by",  sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("processed_by",  sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("notes",         sa.Text(),    nullable=True),
            sa.Column("created_at",    sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at",    sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_gbn_units_id",        "gbn_blood_units", ["id"])
        op.create_index("ix_gbn_units_lab_id",    "gbn_blood_units", ["lab_id"])
        op.create_index("ix_gbn_units_blood_type","gbn_blood_units", ["blood_type"])
        op.create_index("ix_gbn_units_component", "gbn_blood_units", ["component"])
        op.create_index("ix_gbn_units_status",    "gbn_blood_units", ["status"])
        op.create_index("ix_gbn_units_expiry",    "gbn_blood_units", ["expiry_date"])
        op.create_index("ix_gbn_units_barcode",   "gbn_blood_units", ["barcode"])
        op.create_index("ix_gbn_units_available", "gbn_blood_units",
                        ["lab_id", "blood_type", "component", "status"])
        if _pg():
            op.execute(text("""
                ALTER TABLE gbn_blood_units
                ADD CONSTRAINT ck_gbn_units_blood_type
                    CHECK (blood_type IN ('A+','A-','B+','B-','AB+','AB-','O+','O-')),
                ADD CONSTRAINT ck_gbn_units_component
                    CHECK (component IN ('whole','RBC','plasma','platelets','cryo')),
                ADD CONSTRAINT ck_gbn_units_status
                    CHECK (status IN ('quarantine','available','reserved','used','expired','discarded'))
            """))

    # ── 3. gbn_plasma_products ────────────────────────────────────────────────
    if not _table_exists("gbn_plasma_products"):
        op.create_table(
            "gbn_plasma_products",
            sa.Column("id",               sa.Integer(),    primary_key=True, autoincrement=True),
            sa.Column("lab_id",           sa.Integer(),    sa.ForeignKey("labs.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("product_type",     sa.String(50),   nullable=False),
            sa.Column("brand_name",       sa.String(200),  nullable=True),
            sa.Column("batch_number",     sa.String(100),  nullable=False),
            sa.Column("lot_number",       sa.String(100),  nullable=True),
            sa.Column("quantity_units",   sa.Integer(),    nullable=False),
            sa.Column("unit_volume_ml",   sa.Float(),      nullable=True),
            sa.Column("concentration",    sa.String(50),   nullable=True),
            sa.Column("manufacturer",     sa.String(200),  nullable=True),
            sa.Column("country_of_origin",sa.String(100),  nullable=True),
            sa.Column("storage_condition",sa.String(100),  nullable=True),
            sa.Column("expiry_date",      sa.Date(),       nullable=False),
            sa.Column("status",           sa.String(20),   nullable=False, server_default="available"),
            sa.Column("recall_reason",    sa.Text(),       nullable=True),
            sa.Column("received_date",    sa.Date(),       nullable=False),
            sa.Column("received_by",  sa.Integer(), sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("notes",        sa.Text(),    nullable=True),
            sa.Column("created_at",   sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_gbn_plasma_id",       "gbn_plasma_products", ["id"])
        op.create_index("ix_gbn_plasma_lab_id",   "gbn_plasma_products", ["lab_id"])
        op.create_index("ix_gbn_plasma_type",     "gbn_plasma_products", ["product_type"])
        op.create_index("ix_gbn_plasma_batch",    "gbn_plasma_products", ["batch_number"])
        op.create_index("ix_gbn_plasma_expiry",   "gbn_plasma_products", ["expiry_date"])
        op.create_index("ix_gbn_plasma_status",   "gbn_plasma_products", ["status"])

    # ── 4. gbn_blood_requests ─────────────────────────────────────────────────
    if not _table_exists("gbn_blood_requests"):
        op.create_table(
            "gbn_blood_requests",
            sa.Column("id",                sa.Integer(),   primary_key=True, autoincrement=True),
            sa.Column("requesting_lab_id", sa.Integer(),   sa.ForeignKey("labs.id",      ondelete="RESTRICT"), nullable=False),
            sa.Column("patient_id",        sa.Integer(),   sa.ForeignKey("patients.id",  ondelete="SET NULL"), nullable=True),
            sa.Column("requested_by",      sa.Integer(),   sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("blood_type",        sa.String(5),   nullable=False),
            sa.Column("component",         sa.String(30),  nullable=False),
            sa.Column("units_required",    sa.Integer(),   nullable=False, server_default="1"),
            sa.Column("units_fulfilled",   sa.Integer(),   nullable=False, server_default="0"),
            sa.Column("urgency",           sa.String(30),  nullable=False, server_default="routine"),
            sa.Column("clinical_indication", sa.Text(),    nullable=True),
            sa.Column("status",            sa.String(30),  nullable=False, server_default="pending"),
            sa.Column("fulfilling_lab_id", sa.Integer(),   sa.ForeignKey("labs.id", ondelete="SET NULL"), nullable=True),
            sa.Column("matched_at",        sa.DateTime(timezone=True), nullable=True),
            sa.Column("fulfilled_at",      sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_reason",  sa.Text(),      nullable=True),
            sa.Column("notes",             sa.Text(),      nullable=True),
            sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at",  sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_gbn_req_id",         "gbn_blood_requests", ["id"])
        op.create_index("ix_gbn_req_lab_id",     "gbn_blood_requests", ["requesting_lab_id"])
        op.create_index("ix_gbn_req_status",     "gbn_blood_requests", ["status"])
        op.create_index("ix_gbn_req_urgency",    "gbn_blood_requests", ["urgency"])
        op.create_index("ix_gbn_req_blood_type", "gbn_blood_requests", ["blood_type"])
        op.create_index("ix_gbn_req_created",    "gbn_blood_requests", ["created_at"])
        if _pg():
            op.execute(text("""
                ALTER TABLE gbn_blood_requests
                ADD CONSTRAINT ck_gbn_req_urgency
                    CHECK (urgency IN ('routine','urgent','critical','massive_transfusion')),
                ADD CONSTRAINT ck_gbn_req_status
                    CHECK (status IN ('pending','matching','matched','in_transit','fulfilled','cancelled'))
            """))

    # ── 5. gbn_transfusions ───────────────────────────────────────────────────
    if not _table_exists("gbn_transfusions"):
        op.create_table(
            "gbn_transfusions",
            sa.Column("id",               sa.Integer(),  primary_key=True, autoincrement=True),
            sa.Column("patient_id",       sa.Integer(),  sa.ForeignKey("patients.id",        ondelete="RESTRICT"), nullable=False),
            sa.Column("unit_id",          sa.Integer(),  sa.ForeignKey("gbn_blood_units.id", ondelete="RESTRICT"), nullable=False, unique=True),
            sa.Column("request_id",       sa.Integer(),  sa.ForeignKey("gbn_blood_requests.id", ondelete="SET NULL"), nullable=True),
            sa.Column("administered_by",  sa.Integer(),  sa.ForeignKey("lab_users.id",       ondelete="SET NULL"), nullable=True),
            sa.Column("crossmatch_result",    sa.String(30), nullable=False),
            sa.Column("crossmatch_notes",     sa.Text(),     nullable=True),
            sa.Column("transfusion_time",     sa.DateTime(timezone=True), nullable=False),
            sa.Column("volume_transfused_ml", sa.Integer(),  nullable=True),
            sa.Column("duration_minutes",     sa.Integer(),  nullable=True),
            sa.Column("reaction_flag",        sa.Boolean(),  nullable=False, server_default="false"),
            sa.Column("reaction_type",        sa.String(30), nullable=True),
            sa.Column("reaction_notes",       sa.Text(),     nullable=True),
            sa.Column("reaction_time",        sa.DateTime(timezone=True), nullable=True),
            sa.Column("pre_transfusion_hb",   sa.Float(),    nullable=True),
            sa.Column("post_transfusion_hb",  sa.Float(),    nullable=True),
            sa.Column("notes",                sa.Text(),     nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_gbn_txfn_id",      "gbn_transfusions", ["id"])
        op.create_index("ix_gbn_txfn_patient", "gbn_transfusions", ["patient_id"])
        op.create_index("ix_gbn_txfn_unit",    "gbn_transfusions", ["unit_id"])
        op.create_index("ix_gbn_txfn_request", "gbn_transfusions", ["request_id"])
        op.create_index("ix_gbn_txfn_date",    "gbn_transfusions", ["transfusion_time"])
        if _pg():
            op.execute(text("""
                ALTER TABLE gbn_transfusions
                ADD CONSTRAINT ck_gbn_xmatch
                    CHECK (crossmatch_result IN ('compatible','incompatible','not_done'))
            """))

    # ── 6. gbn_blood_transfers ────────────────────────────────────────────────
    if not _table_exists("gbn_blood_transfers"):
        op.create_table(
            "gbn_blood_transfers",
            sa.Column("id",           sa.Integer(),  primary_key=True, autoincrement=True),
            sa.Column("from_lab_id",  sa.Integer(),  sa.ForeignKey("labs.id",            ondelete="RESTRICT"), nullable=False),
            sa.Column("to_lab_id",    sa.Integer(),  sa.ForeignKey("labs.id",            ondelete="RESTRICT"), nullable=False),
            sa.Column("unit_id",      sa.Integer(),  sa.ForeignKey("gbn_blood_units.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("request_id",   sa.Integer(),  sa.ForeignKey("gbn_blood_requests.id", ondelete="SET NULL"), nullable=True),
            sa.Column("status",       sa.String(20), nullable=False, server_default="requested"),
            sa.Column("approved_by",  sa.Integer(),  sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("approved_at",  sa.DateTime(timezone=True), nullable=True),
            sa.Column("dispatched_at",sa.DateTime(timezone=True), nullable=True),
            sa.Column("received_at",  sa.DateTime(timezone=True), nullable=True),
            sa.Column("transport_temp_c", sa.Float(),      nullable=True),
            sa.Column("transport_notes",  sa.Text(),       nullable=True),
            sa.Column("tracking_id",      sa.String(100),  nullable=True),
            sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at",  sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_gbn_xfr_id",     "gbn_blood_transfers", ["id"])
        op.create_index("ix_gbn_xfr_from",   "gbn_blood_transfers", ["from_lab_id"])
        op.create_index("ix_gbn_xfr_to",     "gbn_blood_transfers", ["to_lab_id"])
        op.create_index("ix_gbn_xfr_unit",   "gbn_blood_transfers", ["unit_id"])
        op.create_index("ix_gbn_xfr_status", "gbn_blood_transfers", ["status"])
        if _pg():
            op.execute(text("""
                ALTER TABLE gbn_blood_transfers
                ADD CONSTRAINT ck_gbn_transfer_status
                    CHECK (status IN ('requested','approved','dispatched','received','cancelled'))
            """))


def downgrade() -> None:
    for table in [
        "gbn_blood_transfers",
        "gbn_transfusions",
        "gbn_blood_requests",
        "gbn_plasma_products",
        "gbn_blood_units",
        "gbn_donors",
    ]:
        if _table_exists(table):
            op.drop_table(table)
