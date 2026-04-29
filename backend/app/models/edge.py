"""Edge AI Platform — SQLAlchemy ORM models.

These power the Managed Distributed Edge AI Platform: a control plane that
turns user devices into trusted, sandboxed nodes for local AI inference and
distributed processing.

Tenant isolation: every row is scoped by `lab_id`. Per the platform's
security invariants, all queries must filter on `lab_id == current_user.lab_id`
unless the actor is master_admin / ministry_admin.

See migration 20260428_0001_edge_platform.py for the schema.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Index, Integer,
    JSON, String, Text, UniqueConstraint,
)

from ..database import Base


# ── Status & enum-like constants ──────────────────────────────────────────────

DEVICE_STATUS = ("pending", "active", "quarantined", "revoked", "offline")
DEVICE_ROLE_MODES = ("personal", "clinic", "enterprise")
TASK_STATUS = ("pending", "dispatched", "running", "completed", "failed",
               "cancelled", "expired")
TASK_PRIVACY = ("standard", "sensitive", "phi")
MODEL_STATUS = ("draft", "canary", "active", "retired", "blocked")


class EdgeDevice(Base):
    __tablename__ = "edge_devices"
    __table_args__ = (
        UniqueConstraint("cert_fingerprint", name="uq_edge_devices_cert_fp"),
        Index("idx_edge_devices_lab", "lab_id", "status"),
        Index("idx_edge_devices_seen", "last_seen_at"),
    )

    id                = Column(Integer, primary_key=True, index=True)
    device_id         = Column(String(64), nullable=False, unique=True, index=True)
    lab_id            = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"),
                               nullable=False)
    owner_user_id     = Column(Integer, ForeignKey("lab_users.id", ondelete="SET NULL"),
                               nullable=True)
    display_name      = Column(String(200), nullable=True)
    role_mode         = Column(String(32),  nullable=False, default="personal")
    status            = Column(String(32),  nullable=False, default="pending")
    trust_score       = Column(Float,       nullable=False, default=50.0)
    public_key_pem    = Column(Text,        nullable=True)
    cert_fingerprint  = Column(String(128), nullable=True)
    attestation_blob  = Column(Text,        nullable=True)
    agent_version     = Column(String(32),  nullable=True)
    os_platform       = Column(String(64),  nullable=True)
    capabilities      = Column(JSON,        nullable=True)
    last_seen_at      = Column(DateTime(timezone=True), nullable=True)
    registered_at     = Column(DateTime(timezone=True),
                               default=lambda: datetime.now(timezone.utc),
                               nullable=False)
    revoked_at        = Column(DateTime(timezone=True), nullable=True)
    quarantined_at    = Column(DateTime(timezone=True), nullable=True)
    kill_switched     = Column(Boolean, nullable=False, default=False)
    notes             = Column(Text, nullable=True)

    def is_eligible(self) -> bool:
        """Quick check used by the scheduler before dispatching a task."""
        return (self.status == "active"
                and not self.kill_switched
                and self.revoked_at is None
                and self.quarantined_at is None)


class EdgeTask(Base):
    __tablename__ = "edge_tasks"
    __table_args__ = (
        Index("idx_edge_tasks_dispatch", "status", "priority", "created_at"),
        Index("idx_edge_tasks_device",   "device_id", "status"),
        Index("idx_edge_tasks_lab_status", "lab_id", "status", "created_at"),
        Index("idx_edge_tasks_idem",     "lab_id", "idempotency_key"),
    )

    id                  = Column(BigInteger, primary_key=True)
    task_uid            = Column(String(36), nullable=False, unique=True, index=True)
    idempotency_key     = Column(String(80), nullable=True)
    lab_id              = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"),
                                 nullable=False)
    device_id           = Column(String(64), nullable=True)
    kind                = Column(String(64), nullable=False)
    priority            = Column(Integer,    nullable=False, default=5)
    status              = Column(String(24), nullable=False, default="pending")
    privacy_level       = Column(String(16), nullable=False, default="standard")
    payload             = Column(JSON,       nullable=True)
    payload_sig         = Column(String(256), nullable=True)
    required_caps       = Column(JSON,       nullable=True)
    min_trust           = Column(Float,      nullable=False, default=0.0)
    attempts            = Column(Integer,    nullable=False, default=0)
    max_attempts        = Column(Integer,    nullable=False, default=3)
    timeout_s           = Column(Integer,    nullable=False, default=60)
    created_at          = Column(DateTime(timezone=True),
                                 default=lambda: datetime.now(timezone.utc),
                                 nullable=False)
    dispatched_at       = Column(DateTime(timezone=True), nullable=True)
    completed_at        = Column(DateTime(timezone=True), nullable=True)
    expires_at          = Column(DateTime(timezone=True), nullable=True)
    result              = Column(JSON,       nullable=True)
    error               = Column(Text,       nullable=True)
    submitted_by_user_id = Column(Integer,
                                  ForeignKey("lab_users.id", ondelete="SET NULL"),
                                  nullable=True)


class EdgeTelemetry(Base):
    __tablename__ = "edge_telemetry"
    __table_args__ = (
        Index("idx_edge_telemetry_device_ts", "device_id", "ts"),
        Index("idx_edge_telemetry_ts", "ts"),
    )

    id          = Column(BigInteger, primary_key=True)
    device_id   = Column(String(64), nullable=False)
    lab_id      = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"),
                         nullable=False)
    ts          = Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc),
                         nullable=False)
    cpu_pct          = Column(Float, nullable=True)
    mem_mb           = Column(Float, nullable=True)
    mem_total_mb     = Column(Float, nullable=True)
    gpu_pct          = Column(Float, nullable=True)
    battery_pct      = Column(Float, nullable=True)
    on_battery       = Column(Boolean, nullable=True)
    idle_s           = Column(Integer, nullable=True)
    net_up_kbps      = Column(Float, nullable=True)
    net_down_kbps    = Column(Float, nullable=True)
    loaded_models    = Column(JSON, nullable=True)
    queue_depth      = Column(Integer, nullable=True)
    agent_uptime_s   = Column(Integer, nullable=True)
    task_completed_total = Column(Integer, nullable=True)
    task_failed_total    = Column(Integer, nullable=True)


class EdgeModel(Base):
    __tablename__ = "edge_models"
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_edge_models_name_version"),
        Index("idx_edge_models_status", "status", "rollout_pct"),
    )

    id            = Column(Integer, primary_key=True)
    model_uid     = Column(String(80), nullable=False, unique=True, index=True)
    name          = Column(String(120), nullable=False)
    version       = Column(String(40),  nullable=False)
    runtime       = Column(String(32),  nullable=False, default="ollama")
    format        = Column(String(32),  nullable=False, default="gguf")
    quantization  = Column(String(32),  nullable=True)
    size_mb       = Column(Float,       nullable=True)
    min_ram_mb    = Column(Float,       nullable=True)
    min_vram_mb   = Column(Float,       nullable=True)
    sha256        = Column(String(80),  nullable=True)
    source_url    = Column(String(500), nullable=True)
    status        = Column(String(24),  nullable=False, default="draft")
    rollout_pct   = Column(Float,       nullable=False, default=0.0)
    created_at    = Column(DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           nullable=False)
    retired_at    = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JSON, nullable=True)


class EdgeModelAssignment(Base):
    __tablename__ = "edge_model_assignments"
    __table_args__ = (
        Index("idx_edge_assignments_lookup", "lab_id", "device_id", "active"),
    )

    id          = Column(Integer, primary_key=True)
    model_uid   = Column(String(80), nullable=False)
    lab_id      = Column(Integer, ForeignKey("labs.id", ondelete="CASCADE"),
                         nullable=True)
    device_id   = Column(String(64), nullable=True)
    active      = Column(Boolean, nullable=False, default=True)
    assigned_at = Column(DateTime(timezone=True),
                         default=lambda: datetime.now(timezone.utc),
                         nullable=False)
    retired_at  = Column(DateTime(timezone=True), nullable=True)


class EdgePolicy(Base):
    """Per-tenant edge policy. lab_id NULL means the global default."""
    __tablename__ = "edge_policies"

    id                       = Column(Integer, primary_key=True)
    lab_id                   = Column(Integer,
                                      ForeignKey("labs.id", ondelete="CASCADE"),
                                      nullable=True, unique=True)
    max_concurrent_per_device = Column(Integer, nullable=False, default=2)
    max_devices_per_lab      = Column(Integer, nullable=False, default=50)
    idle_only                = Column(Boolean, nullable=False, default=True)
    battery_floor_pct        = Column(Integer, nullable=False, default=30)
    cpu_cap_pct              = Column(Integer, nullable=False, default=60)
    ram_cap_mb               = Column(Integer, nullable=False, default=2048)
    allow_kinds              = Column(JSON, nullable=True)
    deny_kinds               = Column(JSON, nullable=True)
    min_trust_score          = Column(Float, nullable=False, default=50.0)
    offline_queue_max        = Column(Integer, nullable=False, default=500)
    kill_switch              = Column(Boolean, nullable=False, default=False)
    updated_at               = Column(DateTime(timezone=True),
                                      default=lambda: datetime.now(timezone.utc),
                                      nullable=False)
    updated_by_user_id       = Column(Integer,
                                      ForeignKey("lab_users.id", ondelete="SET NULL"),
                                      nullable=True)


class EdgeEvent(Base):
    """Edge-plane lifecycle / security events.

    Separate from `audit_logs` (which is hash-chained for clinical actions).
    Things that go here: registrations, attestation failures, trust changes,
    quarantines, kill-switch toggles, policy updates, model rollouts.
    """
    __tablename__ = "edge_events"
    __table_args__ = (
        Index("idx_edge_events_ts",     "ts"),
        Index("idx_edge_events_device", "device_id", "ts"),
        Index("idx_edge_events_type",   "event_type", "ts"),
    )

    id            = Column(BigInteger, primary_key=True)
    ts            = Column(DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           nullable=False)
    lab_id        = Column(Integer, nullable=True)
    device_id     = Column(String(64), nullable=True)
    event_type    = Column(String(64), nullable=False)
    severity      = Column(String(16), nullable=False, default="info")
    actor_user_id = Column(Integer, nullable=True)
    details       = Column(JSON, nullable=True)
