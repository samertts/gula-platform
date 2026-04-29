"""Policy manager — load / save / evaluate per-tenant edge policies.

Policy precedence (most-specific wins):
  1. Per-device override (table TBD — for v1 we honor only lab + global)
  2. Per-lab row in edge_policies
  3. Global default row (lab_id IS NULL)
  4. Hard-coded defaults (this module)

When EDGE_KILL_SWITCH (env) is true the policy.kill_switch is forced to True
regardless of stored config.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from ..models.edge import EdgePolicy
from .config import EDGE_KILL_SWITCH


@dataclass(frozen=True)
class ResolvedPolicy:
    max_concurrent_per_device: int
    max_devices_per_lab:       int
    idle_only:                 bool
    battery_floor_pct:         int
    cpu_cap_pct:               int
    ram_cap_mb:                int
    allow_kinds:               Optional[list[str]]
    deny_kinds:                Optional[list[str]]
    min_trust_score:           float
    offline_queue_max:         int
    kill_switch:               bool

    def task_kind_allowed(self, kind: str) -> bool:
        if self.deny_kinds and kind in self.deny_kinds:
            return False
        if self.allow_kinds is None:
            return True
        return kind in self.allow_kinds


_DEFAULT = ResolvedPolicy(
    max_concurrent_per_device=2,
    max_devices_per_lab=50,
    idle_only=True,
    battery_floor_pct=30,
    cpu_cap_pct=60,
    ram_cap_mb=2048,
    allow_kinds=None,
    deny_kinds=None,
    min_trust_score=50.0,
    offline_queue_max=500,
    kill_switch=False,
)


def _row_to_resolved(row: EdgePolicy) -> ResolvedPolicy:
    return ResolvedPolicy(
        max_concurrent_per_device=row.max_concurrent_per_device,
        max_devices_per_lab=row.max_devices_per_lab,
        idle_only=row.idle_only,
        battery_floor_pct=row.battery_floor_pct,
        cpu_cap_pct=row.cpu_cap_pct,
        ram_cap_mb=row.ram_cap_mb,
        allow_kinds=list(row.allow_kinds) if row.allow_kinds else None,
        deny_kinds=list(row.deny_kinds) if row.deny_kinds else None,
        min_trust_score=row.min_trust_score,
        offline_queue_max=row.offline_queue_max,
        kill_switch=row.kill_switch,
    )


def get_policy(db: Session, lab_id: Optional[int]) -> ResolvedPolicy:
    """Return the resolved policy for `lab_id` (None → global default row)."""
    row = None
    if lab_id is not None:
        row = db.query(EdgePolicy).filter(EdgePolicy.lab_id == lab_id).first()
    if row is None:
        row = db.query(EdgePolicy).filter(EdgePolicy.lab_id.is_(None)).first()

    base = _row_to_resolved(row) if row else _DEFAULT

    # Global env kill switch always wins.
    if EDGE_KILL_SWITCH and not base.kill_switch:
        return ResolvedPolicy(**{**base.__dict__, "kill_switch": True})
    return base


def upsert_policy(
    db: Session,
    *,
    lab_id: Optional[int],
    actor_user_id: Optional[int],
    **fields,
) -> EdgePolicy:
    """Create or update a policy row. Caller commits.

    Unknown `fields` are silently ignored — only model attributes are written
    so a malformed admin payload can't poison the DB.
    """
    row = db.query(EdgePolicy).filter(EdgePolicy.lab_id == lab_id).first()
    if row is None:
        row = EdgePolicy(lab_id=lab_id)
        db.add(row)
    allowed = {
        "max_concurrent_per_device", "max_devices_per_lab", "idle_only",
        "battery_floor_pct", "cpu_cap_pct", "ram_cap_mb", "allow_kinds",
        "deny_kinds", "min_trust_score", "offline_queue_max", "kill_switch",
    }
    for k, v in fields.items():
        if k in allowed and v is not None:
            setattr(row, k, v)
    row.updated_by_user_id = actor_user_id
    return row
