"""Model governance — register, version, roll out, retire AI models.

Lifecycle:
    draft → canary (rollout_pct < 100) → active (rollout_pct == 100) → retired
                                                                    ↘ blocked

A device asks `pick_models_for(device)` to learn which models it should keep
warm. The answer is the intersection of:
  1. lab-scoped assignments (edge_model_assignments where lab_id == device.lab_id)
  2. global assignments (lab_id IS NULL)
  3. device-scoped assignments (device_id == this device)

… filtered to models where status in ('canary', 'active') and the device's
trust score yields a hash bucket within rollout_pct (canary deterministic
sampling per Section 19 — Update Mechanism).
"""

from __future__ import annotations

import hashlib
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app._compat import UTC

from ..models.edge import EdgeDevice, EdgeEvent, EdgeModel, EdgeModelAssignment


class GovernanceError(ValueError):
    pass


# ── Model CRUD ────────────────────────────────────────────────────────────────


def register_model(
    db: Session,
    *,
    name: str,
    version: str,
    runtime: str = "ollama",
    fmt: str = "gguf",
    quantization: str | None = None,
    size_mb: float | None = None,
    min_ram_mb: float | None = None,
    min_vram_mb: float | None = None,
    sha256: str | None = None,
    source_url: str | None = None,
    metadata_json: dict | None = None,
    actor_user_id: int | None = None,
) -> EdgeModel:
    """Register a new model version. Caller commits."""
    if runtime not in ("ollama", "llamacpp", "onnx", "custom"):
        raise GovernanceError(f"unknown runtime: {runtime}")
    existing = (
        db.query(EdgeModel).filter(EdgeModel.name == name, EdgeModel.version == version).first()
    )
    if existing is not None:
        raise GovernanceError(f"{name}@{version} already registered")

    uid = f"{name}-{version}".lower().replace("/", "-")[:80]
    model = EdgeModel(
        model_uid=uid,
        name=name,
        version=version,
        runtime=runtime,
        format=fmt,
        quantization=quantization,
        size_mb=size_mb,
        min_ram_mb=min_ram_mb,
        min_vram_mb=min_vram_mb,
        sha256=sha256,
        source_url=source_url,
        status="draft",
        rollout_pct=0.0,
        metadata_json=metadata_json or {},
    )
    db.add(model)
    # Flush so subsequent set_model_status / assign_model in the same
    # transaction can find this row under autoflush=False sessions.
    db.flush()

    db.add(
        EdgeEvent(
            event_type="model_registered",
            severity="info",
            actor_user_id=actor_user_id,
            details={"model_uid": uid, "size_mb": size_mb},
        ),
    )
    return model


def set_model_status(
    db: Session,
    *,
    model_uid: str,
    status: str,
    rollout_pct: float | None = None,
    actor_user_id: int | None = None,
) -> EdgeModel:
    if status not in ("draft", "canary", "active", "retired", "blocked"):
        raise GovernanceError(f"invalid status: {status}")
    model = db.query(EdgeModel).filter(EdgeModel.model_uid == model_uid).first()
    if model is None:
        raise GovernanceError(f"model not found: {model_uid}")
    model.status = status
    if rollout_pct is not None:
        model.rollout_pct = max(0.0, min(100.0, rollout_pct))
    if status == "retired":
        model.retired_at = datetime.now(UTC)

    db.add(
        EdgeEvent(
            event_type="model_status_changed",
            severity="info",
            actor_user_id=actor_user_id,
            details={"model_uid": model_uid, "status": status, "rollout_pct": model.rollout_pct},
        ),
    )
    return model


def assign_model(
    db: Session,
    *,
    model_uid: str,
    lab_id: int | None = None,
    device_id: str | None = None,
    actor_user_id: int | None = None,
) -> EdgeModelAssignment:
    """Pin a model to a lab or specific device. lab_id NULL = global.

    Caller commits.
    """
    model = db.query(EdgeModel).filter(EdgeModel.model_uid == model_uid).first()
    if model is None:
        raise GovernanceError(f"model not found: {model_uid}")
    a = EdgeModelAssignment(
        model_uid=model_uid,
        lab_id=lab_id,
        device_id=device_id,
        active=True,
    )
    db.add(a)
    db.add(
        EdgeEvent(
            lab_id=lab_id,
            device_id=device_id,
            event_type="model_assigned",
            severity="info",
            actor_user_id=actor_user_id,
            details={"model_uid": model_uid},
        ),
    )
    return a


# ── Rollout selection ─────────────────────────────────────────────────────────


def _bucket_pct(device_id: str, model_uid: str) -> float:
    """Deterministic 0–100 bucket for canary sampling.

    Uses SHA-256 over (model_uid + device_id) so a given device either is or
    is not in a model's canary, consistently across heartbeats.
    """
    h = hashlib.sha256(f"{model_uid}|{device_id}".encode()).hexdigest()
    # take 8 hex chars → 32-bit int → 0–100
    return (int(h[:8], 16) % 10_000) / 100.0


def pick_models_for(db: Session, device: EdgeDevice) -> list[dict]:
    """Return the set of models this device should have warm.

    Result shape: [{"model_uid", "version", "runtime", "format", "size_mb",
                    "sha256", "source_url"}]
    """
    assignments = (
        db.query(EdgeModelAssignment)
        .filter(EdgeModelAssignment.active.is_(True))
        .filter(
            or_(
                EdgeModelAssignment.lab_id == device.lab_id,
                EdgeModelAssignment.lab_id.is_(None),
                EdgeModelAssignment.device_id == device.device_id,
            ),
        )
        .all()
    )
    if not assignments:
        return []

    uids = {a.model_uid for a in assignments}
    models = (
        db.query(EdgeModel)
        .filter(EdgeModel.model_uid.in_(uids), EdgeModel.status.in_(("canary", "active")))
        .all()
    )
    out = []
    for m in models:
        if m.status == "active" and m.rollout_pct >= 100.0:
            include = True
        else:
            include = _bucket_pct(device.device_id, m.model_uid) < m.rollout_pct
        if not include:
            continue
        out.append(
            {
                "model_uid": m.model_uid,
                "name": m.name,
                "version": m.version,
                "runtime": m.runtime,
                "format": m.format,
                "size_mb": m.size_mb,
                "sha256": m.sha256,
                "source_url": m.source_url,
            },
        )
    return out
