"""Task scheduler — submit, dispatch, complete, retry, sweep stale.

Routing rules (Section 8):
  - Tenant isolation:   task.lab_id == device.lab_id
  - Capability match:   required_caps ⊆ device.capabilities
  - Privacy gate:       device.trust_score ≥ PRIVACY_MIN_TRUST[task.privacy_level]
  - Trust gate:         device.trust_score ≥ task.min_trust AND policy.min_trust_score
  - Eligibility:        device.is_eligible() (active, not revoked/quarantined)
  - Concurrency:        active dispatched/running tasks < policy.max_concurrent_per_device
  - Kind allowlist:     kind in ALLOWED_TASK_KINDS AND policy.task_kind_allowed(kind)

The scheduler is pull-based: an agent calls `claim_next_task(device)` and we
return at most one task. This keeps the wire format simple and avoids any
push-from-server pattern that would require persistent server→agent sockets.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..models.edge import EdgeDevice, EdgeEvent, EdgeTask
from . import identity, policy as policy_mod, trust as trust_mod
from .config import (
    ALLOWED_TASK_KINDS, EDGE_DISPATCH_GRACE_S, PRIVACY_MIN_TRUST,
)


# ── Errors ────────────────────────────────────────────────────────────────────

class SchedulerError(ValueError):
    pass


# ── Submit ────────────────────────────────────────────────────────────────────

def submit_task(
    db: Session,
    *,
    lab_id: int,
    kind: str,
    payload: Optional[dict[str, Any]] = None,
    priority: int = 5,
    privacy_level: str = "standard",
    required_caps: Optional[list[str]] = None,
    min_trust: float = 0.0,
    timeout_s: int = 60,
    max_attempts: int = 3,
    idempotency_key: Optional[str] = None,
    expires_in_s: Optional[int] = None,
    submitted_by_user_id: Optional[int] = None,
) -> EdgeTask:
    """Enqueue a new edge task. Caller commits.

    Idempotency: if `idempotency_key` is already present for this lab in a
    non-final state, return the existing row instead of creating a duplicate.
    """
    if kind not in ALLOWED_TASK_KINDS:
        raise SchedulerError(f"task kind '{kind}' is not allowlisted")

    if privacy_level not in PRIVACY_MIN_TRUST:
        raise SchedulerError(f"unknown privacy_level: {privacy_level}")

    pol = policy_mod.get_policy(db, lab_id)
    if pol.kill_switch:
        raise SchedulerError("edge platform disabled by kill switch")
    if not pol.task_kind_allowed(kind):
        raise SchedulerError(f"kind '{kind}' is denied by policy")

    if idempotency_key:
        existing = (
            db.query(EdgeTask)
              .filter(EdgeTask.lab_id == lab_id,
                      EdgeTask.idempotency_key == idempotency_key,
                      EdgeTask.status.in_(("pending", "dispatched", "running",
                                           "completed")))
              .first()
        )
        if existing is not None:
            return existing

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=expires_in_s) if expires_in_s else None

    task = EdgeTask(
        task_uid=identity.new_task_uid(),
        idempotency_key=idempotency_key,
        lab_id=lab_id,
        kind=kind,
        priority=max(1, min(10, priority)),
        status="pending",
        privacy_level=privacy_level,
        payload=payload or {},
        required_caps=required_caps or [],
        min_trust=min_trust,
        timeout_s=max(5, min(600, timeout_s)),
        max_attempts=max(1, min(10, max_attempts)),
        expires_at=expires_at,
        submitted_by_user_id=submitted_by_user_id,
    )
    task.payload_sig = identity.sign_task(task.task_uid, task.kind, task.payload)
    db.add(task)
    # Flush so the row is visible to the next idempotency-key lookup even when
    # the session is configured with autoflush=False (the test fixture is).
    db.flush()

    db.add(EdgeEvent(
        lab_id=lab_id, event_type="task_submitted", severity="info",
        actor_user_id=submitted_by_user_id,
        details={"task_uid": task.task_uid, "kind": kind, "priority": priority},
    ))
    return task


# ── Routing checks ────────────────────────────────────────────────────────────

def _device_matches_task(device: EdgeDevice, task: EdgeTask,
                         pol: policy_mod.ResolvedPolicy) -> bool:
    if not device.is_eligible():
        return False
    if device.lab_id != task.lab_id:
        return False
    if device.trust_score < max(pol.min_trust_score, task.min_trust):
        return False
    if not trust_mod.passes_for_privacy(device.trust_score, task.privacy_level):
        return False
    if task.required_caps:
        caps = device.capabilities or {}
        device_caps = set(caps.get("kinds", []) if isinstance(caps, dict) else [])
        if not set(task.required_caps).issubset(device_caps):
            return False
    return True


def _device_concurrency(db: Session, device: EdgeDevice) -> int:
    return (
        db.query(EdgeTask)
          .filter(EdgeTask.device_id == device.device_id,
                  EdgeTask.status.in_(("dispatched", "running")))
          .count()
    )


# ── Claim (pull) ──────────────────────────────────────────────────────────────

def claim_next_task(db: Session, device: EdgeDevice) -> Optional[EdgeTask]:
    """Atomically pick and assign the next eligible task for `device`.

    Uses SELECT ... FOR UPDATE SKIP LOCKED on Postgres so concurrent agents
    don't fight for the same row. SQLite (test backend) silently no-ops the
    lock — concurrency is single-threaded there anyway. Caller commits.
    """
    pol = policy_mod.get_policy(db, device.lab_id)
    if pol.kill_switch:
        return None

    if _device_concurrency(db, device) >= pol.max_concurrent_per_device:
        return None

    now = datetime.now(timezone.utc)

    # Candidate tasks: pending, in this lab, not expired, ordered by priority.
    q = (
        db.query(EdgeTask)
          .filter(EdgeTask.lab_id == device.lab_id,
                  EdgeTask.status == "pending",
                  or_(EdgeTask.expires_at.is_(None), EdgeTask.expires_at > now))
          .order_by(EdgeTask.priority.asc(), EdgeTask.created_at.asc())
          .limit(20)
    )

    # Apply row locking only on dialects that support it. SQLAlchemy's SQLite
    # dialect generally drops FOR UPDATE silently, but we make it explicit so
    # any future dialect change can't surface a SQL syntax error in tests.
    bind = db.get_bind()
    dialect_name = getattr(getattr(bind, "dialect", None), "name", "") or ""
    if dialect_name in ("postgresql", "mysql", "mariadb"):
        q = q.with_for_update(skip_locked=True)

    for task in q:
        if not _device_matches_task(device, task, pol):
            continue
        # Reserve it.
        task.status = "dispatched"
        task.device_id = device.device_id
        task.dispatched_at = now
        task.attempts += 1
        return task
    return None


# ── Complete / fail ───────────────────────────────────────────────────────────

def complete_task(
    db: Session, task: EdgeTask, *, result: Optional[dict],
) -> None:
    task.status = "completed"
    task.completed_at = datetime.now(timezone.utc)
    task.result = result or {}
    task.error = None
    db.add(EdgeEvent(
        lab_id=task.lab_id, device_id=task.device_id,
        event_type="task_completed", severity="info",
        details={"task_uid": task.task_uid,
                 "duration_ms": _duration_ms(task)},
    ))


def fail_task(db: Session, task: EdgeTask, *, error: str) -> None:
    task.error = error[:1000]
    if task.attempts < task.max_attempts:
        # Re-queue.
        task.status = "pending"
        task.dispatched_at = None
        task.device_id = None
    else:
        task.status = "failed"
        task.completed_at = datetime.now(timezone.utc)
    db.add(EdgeEvent(
        lab_id=task.lab_id, device_id=task.device_id,
        event_type="task_failed", severity="warning",
        details={"task_uid": task.task_uid, "attempt": task.attempts,
                 "max_attempts": task.max_attempts, "error": error[:200]},
    ))


def cancel_task(db: Session, task: EdgeTask, *, reason: str,
                actor_user_id: Optional[int]) -> None:
    if task.status in ("completed", "failed", "cancelled", "expired"):
        return
    task.status = "cancelled"
    task.completed_at = datetime.now(timezone.utc)
    task.error = f"cancelled: {reason}"
    db.add(EdgeEvent(
        lab_id=task.lab_id, device_id=task.device_id,
        event_type="task_cancelled", severity="info",
        actor_user_id=actor_user_id,
        details={"task_uid": task.task_uid, "reason": reason},
    ))


# ── Reaper ────────────────────────────────────────────────────────────────────

def sweep_stale(db: Session) -> int:
    """Re-queue or fail tasks that were dispatched but never reported back.

    Called from a background loop. Returns count of tasks acted on.
    Caller commits.
    """
    now = datetime.now(timezone.utc)
    stale = (
        db.query(EdgeTask)
          .filter(EdgeTask.status.in_(("dispatched", "running")),
                  EdgeTask.dispatched_at.isnot(None))
          .all()
    )
    n = 0
    for t in stale:
        deadline = t.dispatched_at + timedelta(seconds=t.timeout_s + EDGE_DISPATCH_GRACE_S)
        if deadline < now:
            fail_task(db, t, error=f"dispatch_timeout after {t.timeout_s}s")
            n += 1
    # Expired tasks (TTL hit before pickup).
    expired = (
        db.query(EdgeTask)
          .filter(EdgeTask.status == "pending",
                  EdgeTask.expires_at.isnot(None),
                  EdgeTask.expires_at < now)
          .all()
    )
    for t in expired:
        t.status = "expired"
        t.completed_at = now
        n += 1
    return n


# ── Helpers ───────────────────────────────────────────────────────────────────

def _duration_ms(task: EdgeTask) -> Optional[int]:
    if task.dispatched_at is None or task.completed_at is None:
        return None
    return int((task.completed_at - task.dispatched_at).total_seconds() * 1000)
