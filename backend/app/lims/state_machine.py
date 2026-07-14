"""National LIMS State Machines — single source of truth for lifecycle transitions.

Specimen Lifecycle:
  ordered → registered → collected → transporting → received
  → accepted → aliquoted → processing → analyzing
  → analyzed → verified → validated → released → archived → disposed

  Rejection is possible at: received, accepted, and any pre-analysis step.
  At verification/validation, results may be flagged for repeat/review.

Order Lifecycle:
  pending → accessioned → collecting → collected → in_transport
  → received → in_progress → completed → validated → released
  → [cancelled at any pre-release step]
  → corrected (post-release, with original reference)
"""

from __future__ import annotations

from fastapi import HTTPException


# ===========================================================================
# Specimen State Machine
# ===========================================================================

_SPECIMEN_TRANSITIONS: dict[str, list[str]] = {
    "ordered": ["registered", "cancelled"],
    "registered": ["collected", "cancelled"],
    "collected": ["transporting", "received", "rejected", "cancelled"],
    "transporting": ["received", "rejected"],
    "received": ["accepted", "rejected"],
    "accepted": ["aliquoted", "processing", "analyzing", "rejected"],
    "rejected": [],
    "aliquoted": ["processing", "analyzing", "rejected"],
    "processing": ["analyzing", "rejected"],
    "analyzing": ["analyzed", "rejected"],
    "analyzed": ["verified"],
    "verified": ["validated"],
    "validated": ["released"],
    "released": ["archived"],
    "archived": ["disposed"],
    "cancelled": [],
    "disposed": [],
}

_SPECIMEN_REJECTABLE_STATES = {"received", "accepted", "aliquoted", "processing", "analyzing"}


def can_transition_specimen(current: str, target: str) -> bool:
    return target in _SPECIMEN_TRANSITIONS.get(current, [])


def enforce_specimen_transition(current: str, target: str) -> None:
    if not can_transition_specimen(current, target):
        allowed = _SPECIMEN_TRANSITIONS.get(current, [])
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot move specimen from '{current}' to '{target}'. "
                f"Allowed: {allowed or 'none (terminal)'}."
            ),
        )


def can_reject_specimen(current: str) -> bool:
    return current in _SPECIMEN_REJECTABLE_STATES


def enforce_can_reject(current: str) -> None:
    if not can_reject_specimen(current):
        raise HTTPException(
            status_code=409,
            detail=f"Specimen in state '{current}' cannot be rejected.",
        )


# ===========================================================================
# Order State Machine
# ===========================================================================

_ORDER_TRANSITIONS: dict[str, list[str]] = {
    "pending": ["accessioned", "cancelled"],
    "accessioned": ["collecting", "cancelled"],
    "collecting": ["collected", "cancelled"],
    "collected": ["in_transport", "received", "cancelled"],
    "in_transport": ["received", "cancelled"],
    "received": ["in_progress", "cancelled"],
    "in_progress": ["completed", "cancelled"],
    "completed": ["validated", "cancelled"],
    "validated": ["released"],
    "released": ["corrected"],
    "corrected": ["released"],
    "cancelled": [],
}


def can_transition_order(current: str, target: str) -> bool:
    return target in _ORDER_TRANSITIONS.get(current, [])


def enforce_order_transition(current: str, target: str) -> None:
    if not can_transition_order(current, target):
        allowed = _ORDER_TRANSITIONS.get(current, [])
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot move order from '{current}' to '{target}'. "
                f"Allowed: {allowed or 'none (terminal)'}."
            ),
        )
