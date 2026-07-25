"""Device registry — register, heartbeat, lookup, lifecycle transitions.

This is the gateway every edge node must pass through. The HTTP layer in
`routes/edge.py` should never write `edge_devices` directly — it must call
into here so audit-event writes and policy enforcement stay centralized.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app._compat import UTC

from ..models.edge import EdgeDevice, EdgeEvent
from . import identity
from . import policy as policy_mod
from .config import EDGE_TRUST_INITIAL

# ── Errors ────────────────────────────────────────────────────────────────────


class RegistryError(ValueError):
    """Raised when registration / lifecycle transitions fail validation."""


# ── Registration ──────────────────────────────────────────────────────────────


def register_device(
    db: Session,
    *,
    lab_id: int,
    owner_user_id: int | None,
    public_key_pem: str,
    role_mode: str = "personal",
    display_name: str | None = None,
    agent_version: str | None = None,
    os_platform: str | None = None,
    capabilities: dict | None = None,
    attestation_blob: str | None = None,
) -> EdgeDevice:
    """Enroll a new device. Caller commits.

    Enforces the per-lab device cap from the resolved policy.
    """
    if role_mode not in ("personal", "clinic", "enterprise"):
        raise RegistryError(f"invalid role_mode: {role_mode}")

    pol = policy_mod.get_policy(db, lab_id)
    if pol.kill_switch:
        raise RegistryError("edge platform is currently disabled by kill switch")

    current = (
        db.query(EdgeDevice)
        .filter(
            EdgeDevice.lab_id == lab_id,
            EdgeDevice.status.in_(("active", "pending", "quarantined")),
        )
        .count()
    )
    if current >= pol.max_devices_per_lab:
        raise RegistryError(f"lab device cap reached ({pol.max_devices_per_lab})")

    fp = identity.fingerprint_pem(public_key_pem)
    existing_fp = db.query(EdgeDevice).filter(EdgeDevice.cert_fingerprint == fp).first()
    if existing_fp is not None:
        raise RegistryError("public key already registered for another device")

    device = EdgeDevice(
        device_id=identity.new_device_id(),
        lab_id=lab_id,
        owner_user_id=owner_user_id,
        display_name=display_name,
        role_mode=role_mode,
        status="pending",
        trust_score=EDGE_TRUST_INITIAL,
        public_key_pem=public_key_pem,
        cert_fingerprint=fp,
        attestation_blob=attestation_blob,
        agent_version=agent_version,
        os_platform=os_platform,
        capabilities=capabilities or {},
        registered_at=datetime.now(UTC),
    )
    db.add(device)
    db.flush()  # assign id

    db.add(
        EdgeEvent(
            lab_id=lab_id,
            device_id=device.device_id,
            event_type="device_registered",
            severity="info",
            actor_user_id=owner_user_id,
            details={
                "role_mode": role_mode,
                "agent_version": agent_version,
                "fingerprint": fp,
            },
        ),
    )
    return device


# ── Heartbeat ─────────────────────────────────────────────────────────────────


def heartbeat(
    db: Session,
    *,
    device_id: str,
    agent_version: str | None = None,
    capabilities: dict | None = None,
) -> EdgeDevice:
    """Refresh last_seen_at and metadata. Returns the (mutated) row.

    A `pending` device is auto-activated on its first heartbeat — this is the
    simplest "ack of registration" handshake. Production deployments may want
    to require explicit operator approval; gate that with a feature flag if so.
    """
    device = db.query(EdgeDevice).filter(EdgeDevice.device_id == device_id).first()
    if device is None:
        raise RegistryError("device not registered")
    if device.revoked_at is not None:
        raise RegistryError("device revoked")
    if device.kill_switched:
        raise RegistryError("device killed by operator")

    now = datetime.now(UTC)
    device.last_seen_at = now
    if agent_version:
        device.agent_version = agent_version
    if capabilities:
        device.capabilities = capabilities

    if device.status == "pending":
        device.status = "active"
        db.add(
            EdgeEvent(
                lab_id=device.lab_id,
                device_id=device.device_id,
                event_type="device_activated",
                severity="info",
                details={"agent_version": agent_version},
            ),
        )
    return device


# ── Lifecycle ─────────────────────────────────────────────────────────────────


def quarantine(db: Session, device: EdgeDevice, *, reason: str, actor_user_id: int | None) -> None:
    device.status = "quarantined"
    device.quarantined_at = datetime.now(UTC)
    db.add(
        EdgeEvent(
            lab_id=device.lab_id,
            device_id=device.device_id,
            event_type="device_quarantined",
            severity="warning",
            actor_user_id=actor_user_id,
            details={"reason": reason},
        ),
    )


def revoke(db: Session, device: EdgeDevice, *, reason: str, actor_user_id: int | None) -> None:
    device.status = "revoked"
    device.revoked_at = datetime.now(UTC)
    db.add(
        EdgeEvent(
            lab_id=device.lab_id,
            device_id=device.device_id,
            event_type="device_revoked",
            severity="critical",
            actor_user_id=actor_user_id,
            details={"reason": reason},
        ),
    )


def reinstate(db: Session, device: EdgeDevice, *, actor_user_id: int | None) -> None:
    """Take a quarantined device back to active. Cannot reinstate a revoked one."""
    if device.status == "revoked":
        raise RegistryError("revoked devices cannot be reinstated; re-register")
    device.status = "active"
    device.quarantined_at = None
    db.add(
        EdgeEvent(
            lab_id=device.lab_id,
            device_id=device.device_id,
            event_type="device_reinstated",
            severity="info",
            actor_user_id=actor_user_id,
        ),
    )


def kill_switch_set(
    db: Session,
    device: EdgeDevice,
    on: bool,
    *,
    actor_user_id: int | None,
) -> None:
    device.kill_switched = on
    db.add(
        EdgeEvent(
            lab_id=device.lab_id,
            device_id=device.device_id,
            event_type="device_kill_switch",
            severity="critical" if on else "info",
            actor_user_id=actor_user_id,
            details={"on": on},
        ),
    )


# ── Read ──────────────────────────────────────────────────────────────────────


def get_device_for_lab(
    db: Session,
    *,
    device_id: str,
    lab_id: int,
) -> EdgeDevice | None:
    """Tenant-isolated lookup. Returns None if not found OR not in this lab."""
    return (
        db.query(EdgeDevice)
        .filter(EdgeDevice.device_id == device_id, EdgeDevice.lab_id == lab_id)
        .first()
    )
