"""Order State Machine — single source of truth for order lifecycle.

Valid transitions:
    pending   → completed  (results entered)
    pending   → cancelled  (before any results)
    completed → validated  (doctor/admin validates — becomes immutable)
    completed → cancelled  (before validation)
    validated → (terminal — no further transitions allowed)
    cancelled → (terminal)

Enforcement is done at the service layer (routes/results.py) so that
no endpoint can bypass the rules regardless of how it is called.
"""

from fastapi import HTTPException

# Canonical transition map.  Keys are current states; values are reachable targets.
_TRANSITIONS: dict[str, list[str]] = {
    "pending": ["completed", "cancelled"],
    "completed": ["validated", "cancelled"],
    "validated": [],
    "cancelled": [],
}


def can_transition(current: str, target: str) -> bool:
    """Return True if moving from *current* to *target* is a legal transition."""
    return target in _TRANSITIONS.get(current, [])


def enforce_transition(current: str, target: str) -> None:
    """Raise HTTP 409 if the transition is not allowed.

    Using 409 Conflict (not 400 Bad Request) because the input is structurally
    valid — the issue is a state conflict, which is exactly what 409 models.
    """
    if not can_transition(current, target):
        allowed = _TRANSITIONS.get(current, [])
        detail = (
            f"Cannot move order from '{current}' to '{target}'. "
            f"Allowed transitions: {allowed or 'none (terminal state)'}."
        )
        raise HTTPException(status_code=409, detail=detail)


def assert_not_locked(order) -> None:
    """Raise HTTP 423 Locked if the order has been validated and locked.

    Call this before any mutation that touches an order's results or samples
    (create result, delete result, update sample status, etc.).
    HTTP 423 is the semantically correct status for a locked resource.
    """
    if order.locked_at is not None:
        raise HTTPException(
            status_code=423,
            detail=(
                f"Order #{order.id} is locked (validated at "
                f"{order.locked_at.isoformat()}). "
                "Validated orders are immutable."
            ),
        )


def assert_not_cancelled(order) -> None:
    """Raise HTTP 409 if the order is already cancelled."""
    if order.status == "cancelled":
        raise HTTPException(
            status_code=409,
            detail=f"Order #{order.id} is cancelled and cannot be modified.",
        )
