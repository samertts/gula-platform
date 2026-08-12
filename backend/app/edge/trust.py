"""Device trust scoring (Section 35).

Trust is a moving 0–100 score per device. New devices start at 50 (configurable).
The scheduler refuses to dispatch high-privacy tasks to low-trust devices.

Score deltas (small, additive — clamped to [0, 100]):
  +1   per successful task completion (capped at +20 per day)
  -3   per task failure
  -5   per dispatch timeout
  -25  per signature failure (cryptographic misbehavior)
  -50  per attestation failure
  +0.5 per successful heartbeat (slow recovery)

Below EDGE_TRUST_QUARANTINE_BELOW (default 20), the device is auto-quarantined
and the next heartbeat receives a signal to halt and await operator review.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app._compat import UTC

from ..models.edge import EdgeDevice, EdgeEvent
from .config import EDGE_TRUST_MAX, EDGE_TRUST_MIN, EDGE_TRUST_QUARANTINE_BELOW

# Per-event trust deltas (single source of truth — keep tightly bounded).
DELTAS = {
    "task_completed": +1.0,
    "task_failed": -3.0,
    "task_timeout": -5.0,
    "signature_failure": -25.0,
    "attestation_failure": -50.0,
    "heartbeat_ok": +0.5,
    "policy_violation": -10.0,
    "manual_promote": +10.0,
    "manual_demote": -10.0,
}


def adjust(
    db: Session,
    device: EdgeDevice,
    *,
    reason: str,
    actor_user_id: int | None = None,
) -> float:
    """Apply a delta to the device's trust score and persist an EdgeEvent.

    Returns the new score. Auto-quarantines below the floor.

    Caller is responsible for committing the transaction.
    """
    delta = DELTAS.get(reason)
    if delta is None:
        # Unknown reason → no-op, but log so we can detect typos in callers
        db.add(
            EdgeEvent(
                lab_id=device.lab_id,
                device_id=device.device_id,
                event_type="trust_unknown_reason",
                severity="warning",
                actor_user_id=actor_user_id,
                details={"reason": reason},
            ),
        )
        return device.trust_score

    new_score = max(EDGE_TRUST_MIN, min(EDGE_TRUST_MAX, device.trust_score + delta))
    if new_score == device.trust_score:
        return new_score

    device.trust_score = new_score

    # Auto-quarantine on hard floor
    if new_score < EDGE_TRUST_QUARANTINE_BELOW and device.status == "active":
        device.status = "quarantined"
        device.quarantined_at = datetime.now(UTC)
        db.add(
            EdgeEvent(
                lab_id=device.lab_id,
                device_id=device.device_id,
                event_type="device_quarantined",
                severity="critical",
                actor_user_id=actor_user_id,
                details={"trust_score": new_score, "trigger": reason},
            ),
        )

    db.add(
        EdgeEvent(
            lab_id=device.lab_id,
            device_id=device.device_id,
            event_type="trust_changed",
            severity="info",
            actor_user_id=actor_user_id,
            details={"reason": reason, "delta": delta, "new": new_score},
        ),
    )
    return new_score


def passes_for_privacy(trust_score: float, privacy_level: str) -> bool:
    """Return True if a device with this trust score may receive a task at the
    given privacy level. Wired through to scheduler.
    """
    from .config import PRIVACY_MIN_TRUST

    floor = PRIVACY_MIN_TRUST.get(privacy_level, 100.0)
    return trust_score >= floor
