"""Edge AI Platform: device registry, tasks, telemetry, models, policies.

Revision ID: 20260428_0001
Revises    : 20260417_0001
Create Date: 2026-04-28

Adds the foundational tables for the Managed Distributed Edge AI Platform:

  - edge_devices       — Device registry with identity, trust, capabilities, role mode
  - edge_tasks         — Queue for distributed task execution
  - edge_telemetry     — Time-series snapshots of device resource usage
  - edge_models        — AI model governance / versioning catalog
  - edge_model_assignments — Which models are deployed to which device/lab
  - edge_policies      — Per-tenant policy & quota config
  - edge_events        — Edge-specific audit / lifecycle events (separate from
                         clinical audit_logs to avoid noise dilution)

Design rules:
  - All tables are tenant-isolated by lab_id (FK to labs)
  - Idempotent — uses IF NOT EXISTS guards via inspector
  - All new columns are nullable or have server defaults
  - Indexes cover the hot paths: device lookup by fingerprint, task pulls by
    (status, priority, dispatched_at), telemetry by (device_id, ts)
"""
from alembic import context, op
import sqlalchemy as sa
from sqlalchemy import inspect


revision      = "20260428_0001"
down_revision = "20260417_0001"
branch_labels = None
depends_on    = None


def _has_table(name: str) -> bool:
    if context.is_offline_mode():
        return False
    return inspect(op.get_bind()).has_table(name)


def _index_exists(index: str) -> bool:
    if context.is_offline_mode():
        return False
    insp = inspect(op.get_bind())
    for tbl in insp.get_table_names():
        if any(i["name"] == index for i in insp.get_indexes(tbl)):
            return True
    return False


def upgrade() -> None:
    # ── edge_devices ──────────────────────────────────────────────────────────
    if not _has_table("edge_devices"):
        op.create_table(
            "edge_devices",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("device_id",     sa.String(64),  nullable=False, unique=True),
            sa.Column("lab_id",        sa.Integer(),
                      sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("owner_user_id", sa.Integer(),
                      sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("display_name",  sa.String(200), nullable=True),
            sa.Column("role_mode",     sa.String(32),  nullable=False, server_default="personal"),
            sa.Column("status",        sa.String(32),  nullable=False, server_default="pending"),
            sa.Column("trust_score",   sa.Float(),     nullable=False, server_default="50.0"),
            sa.Column("public_key_pem", sa.Text(),     nullable=True),
            sa.Column("cert_fingerprint", sa.String(128), nullable=True),
            sa.Column("attestation_blob", sa.Text(),   nullable=True),
            sa.Column("agent_version", sa.String(32),  nullable=True),
            sa.Column("os_platform",   sa.String(64),  nullable=True),
            sa.Column("capabilities",  sa.JSON(),      nullable=True),
            sa.Column("last_seen_at",  sa.DateTime(timezone=True), nullable=True),
            sa.Column("registered_at", sa.DateTime(timezone=True),
                      nullable=False, server_default=sa.func.now()),
            sa.Column("revoked_at",    sa.DateTime(timezone=True), nullable=True),
            sa.Column("quarantined_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("kill_switched", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("notes",         sa.Text(),      nullable=True),
            sa.UniqueConstraint("cert_fingerprint", name="uq_edge_devices_cert_fp"),
        )

    if not _index_exists("idx_edge_devices_lab"):
        op.create_index("idx_edge_devices_lab", "edge_devices",
                        ["lab_id", "status"])
    if not _index_exists("idx_edge_devices_seen"):
        op.create_index("idx_edge_devices_seen", "edge_devices",
                        ["last_seen_at"])

    # ── edge_tasks ────────────────────────────────────────────────────────────
    if not _has_table("edge_tasks"):
        op.create_table(
            "edge_tasks",
            sa.Column("id",          sa.BigInteger(), primary_key=True),
            sa.Column("task_uid",    sa.String(36),   nullable=False, unique=True),
            sa.Column("idempotency_key", sa.String(80), nullable=True),
            sa.Column("lab_id",      sa.Integer(),
                      sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("device_id",   sa.String(64),   nullable=True),
            sa.Column("kind",        sa.String(64),   nullable=False),
            sa.Column("priority",    sa.Integer(),    nullable=False, server_default="5"),
            sa.Column("status",      sa.String(24),   nullable=False, server_default="pending"),
            sa.Column("privacy_level", sa.String(16), nullable=False, server_default="standard"),
            sa.Column("payload",     sa.JSON(),       nullable=True),
            sa.Column("payload_sig", sa.String(256),  nullable=True),
            sa.Column("required_caps", sa.JSON(),     nullable=True),
            sa.Column("min_trust",   sa.Float(),      nullable=False, server_default="0.0"),
            sa.Column("attempts",    sa.Integer(),    nullable=False, server_default="0"),
            sa.Column("max_attempts", sa.Integer(),   nullable=False, server_default="3"),
            sa.Column("timeout_s",   sa.Integer(),    nullable=False, server_default="60"),
            sa.Column("created_at",  sa.DateTime(timezone=True),
                      nullable=False, server_default=sa.func.now()),
            sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at",  sa.DateTime(timezone=True), nullable=True),
            sa.Column("result",      sa.JSON(),       nullable=True),
            sa.Column("error",       sa.Text(),       nullable=True),
            sa.Column("submitted_by_user_id", sa.Integer(),
                      sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
        )

    if not _index_exists("idx_edge_tasks_dispatch"):
        op.create_index("idx_edge_tasks_dispatch", "edge_tasks",
                        ["status", "priority", "created_at"])
    if not _index_exists("idx_edge_tasks_device"):
        op.create_index("idx_edge_tasks_device", "edge_tasks",
                        ["device_id", "status"])
    if not _index_exists("idx_edge_tasks_lab_status"):
        op.create_index("idx_edge_tasks_lab_status", "edge_tasks",
                        ["lab_id", "status", "created_at"])
    if not _index_exists("idx_edge_tasks_idem"):
        op.create_index("idx_edge_tasks_idem", "edge_tasks",
                        ["lab_id", "idempotency_key"])

    # ── edge_telemetry ────────────────────────────────────────────────────────
    if not _has_table("edge_telemetry"):
        op.create_table(
            "edge_telemetry",
            sa.Column("id",          sa.BigInteger(), primary_key=True),
            sa.Column("device_id",   sa.String(64),   nullable=False),
            sa.Column("lab_id",      sa.Integer(),
                      sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("ts",          sa.DateTime(timezone=True),
                      nullable=False, server_default=sa.func.now()),
            sa.Column("cpu_pct",     sa.Float(),      nullable=True),
            sa.Column("mem_mb",      sa.Float(),      nullable=True),
            sa.Column("mem_total_mb", sa.Float(),     nullable=True),
            sa.Column("gpu_pct",     sa.Float(),      nullable=True),
            sa.Column("battery_pct", sa.Float(),      nullable=True),
            sa.Column("on_battery",  sa.Boolean(),    nullable=True),
            sa.Column("idle_s",      sa.Integer(),    nullable=True),
            sa.Column("net_up_kbps", sa.Float(),      nullable=True),
            sa.Column("net_down_kbps", sa.Float(),    nullable=True),
            sa.Column("loaded_models", sa.JSON(),     nullable=True),
            sa.Column("queue_depth", sa.Integer(),    nullable=True),
            sa.Column("agent_uptime_s", sa.Integer(), nullable=True),
            sa.Column("task_completed_total", sa.Integer(), nullable=True),
            sa.Column("task_failed_total",    sa.Integer(), nullable=True),
        )

    if not _index_exists("idx_edge_telemetry_device_ts"):
        op.create_index("idx_edge_telemetry_device_ts", "edge_telemetry",
                        ["device_id", "ts"])
    if not _index_exists("idx_edge_telemetry_ts"):
        op.create_index("idx_edge_telemetry_ts", "edge_telemetry", ["ts"])

    # ── edge_models ───────────────────────────────────────────────────────────
    if not _has_table("edge_models"):
        op.create_table(
            "edge_models",
            sa.Column("id",            sa.Integer(), primary_key=True),
            sa.Column("model_uid",     sa.String(80), nullable=False, unique=True),
            sa.Column("name",          sa.String(120), nullable=False),
            sa.Column("version",       sa.String(40),  nullable=False),
            sa.Column("runtime",       sa.String(32),  nullable=False, server_default="ollama"),
            sa.Column("format",        sa.String(32),  nullable=False, server_default="gguf"),
            sa.Column("quantization",  sa.String(32),  nullable=True),
            sa.Column("size_mb",       sa.Float(),     nullable=True),
            sa.Column("min_ram_mb",    sa.Float(),     nullable=True),
            sa.Column("min_vram_mb",   sa.Float(),     nullable=True),
            sa.Column("sha256",        sa.String(80),  nullable=True),
            sa.Column("source_url",    sa.String(500), nullable=True),
            sa.Column("status",        sa.String(24),  nullable=False, server_default="draft"),
            sa.Column("rollout_pct",   sa.Float(),     nullable=False, server_default="0.0"),
            sa.Column("created_at",    sa.DateTime(timezone=True),
                      nullable=False, server_default=sa.func.now()),
            sa.Column("retired_at",    sa.DateTime(timezone=True), nullable=True),
            sa.Column("metadata_json", sa.JSON(),      nullable=True),
            sa.UniqueConstraint("name", "version", name="uq_edge_models_name_version"),
        )

    if not _index_exists("idx_edge_models_status"):
        op.create_index("idx_edge_models_status", "edge_models",
                        ["status", "rollout_pct"])

    # ── edge_model_assignments ────────────────────────────────────────────────
    if not _has_table("edge_model_assignments"):
        op.create_table(
            "edge_model_assignments",
            sa.Column("id",          sa.Integer(), primary_key=True),
            sa.Column("model_uid",   sa.String(80), nullable=False),
            sa.Column("lab_id",      sa.Integer(),
                      sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=True),
            sa.Column("device_id",   sa.String(64), nullable=True),
            sa.Column("active",      sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("assigned_at", sa.DateTime(timezone=True),
                      nullable=False, server_default=sa.func.now()),
            sa.Column("retired_at",  sa.DateTime(timezone=True), nullable=True),
        )

    if not _index_exists("idx_edge_assignments_lookup"):
        op.create_index("idx_edge_assignments_lookup", "edge_model_assignments",
                        ["lab_id", "device_id", "active"])

    # ── edge_policies ─────────────────────────────────────────────────────────
    if not _has_table("edge_policies"):
        op.create_table(
            "edge_policies",
            sa.Column("id",          sa.Integer(), primary_key=True),
            sa.Column("lab_id",      sa.Integer(),
                      sa.ForeignKey("labs.id", ondelete="CASCADE"),
                      nullable=True, unique=True),
            sa.Column("max_concurrent_per_device", sa.Integer(),
                      nullable=False, server_default="2"),
            sa.Column("max_devices_per_lab", sa.Integer(),
                      nullable=False, server_default="50"),
            sa.Column("idle_only",  sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("battery_floor_pct", sa.Integer(),
                      nullable=False, server_default="30"),
            sa.Column("cpu_cap_pct", sa.Integer(),
                      nullable=False, server_default="60"),
            sa.Column("ram_cap_mb",  sa.Integer(),
                      nullable=False, server_default="2048"),
            sa.Column("allow_kinds",   sa.JSON(), nullable=True),
            sa.Column("deny_kinds",    sa.JSON(), nullable=True),
            sa.Column("min_trust_score", sa.Float(),
                      nullable=False, server_default="50.0"),
            sa.Column("offline_queue_max", sa.Integer(),
                      nullable=False, server_default="500"),
            sa.Column("kill_switch", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("updated_at",  sa.DateTime(timezone=True),
                      nullable=False, server_default=sa.func.now()),
            sa.Column("updated_by_user_id", sa.Integer(),
                      sa.ForeignKey("lab_users.id", ondelete="SET NULL"), nullable=True),
        )

    # ── edge_events ───────────────────────────────────────────────────────────
    # Lifecycle events specific to the edge plane. Kept separate from clinical
    # audit_logs so security investigators can filter without query bloat.
    if not _has_table("edge_events"):
        op.create_table(
            "edge_events",
            sa.Column("id",          sa.BigInteger(), primary_key=True),
            sa.Column("ts",          sa.DateTime(timezone=True),
                      nullable=False, server_default=sa.func.now()),
            sa.Column("lab_id",      sa.Integer(), nullable=True),
            sa.Column("device_id",   sa.String(64), nullable=True),
            sa.Column("event_type",  sa.String(64), nullable=False),
            sa.Column("severity",    sa.String(16),
                      nullable=False, server_default="info"),
            sa.Column("actor_user_id", sa.Integer(), nullable=True),
            sa.Column("details",     sa.JSON(), nullable=True),
        )

    if not _index_exists("idx_edge_events_ts"):
        op.create_index("idx_edge_events_ts", "edge_events", ["ts"])
    if not _index_exists("idx_edge_events_device"):
        op.create_index("idx_edge_events_device", "edge_events",
                        ["device_id", "ts"])
    if not _index_exists("idx_edge_events_type"):
        op.create_index("idx_edge_events_type", "edge_events",
                        ["event_type", "ts"])


def downgrade() -> None:
    for tbl in (
        "edge_events",
        "edge_policies",
        "edge_model_assignments",
        "edge_models",
        "edge_telemetry",
        "edge_tasks",
        "edge_devices",
    ):
        if _has_table(tbl):
            op.drop_table(tbl)
