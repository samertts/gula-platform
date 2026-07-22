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

from __future__ import annotations

from app._compat import StrEnum
from app.domain.exceptions import OrderStateError


class OrderStatus(StrEnum):
    """Canonical status values for a LabOrder.

    Values match DB column strings for backward compatibility.
    """

    PENDING = "pending"
    COMPLETED = "completed"
    VALIDATED = "validated"
    CANCELLED = "cancelled"


# Canonical transition map.  Keys are current states; values are reachable targets.
# Accepts both OrderStatus enum members and raw strings for flexibility.
_TRANSITIONS: dict[str, list[str]] = {
    OrderStatus.PENDING.value: [OrderStatus.COMPLETED.value, OrderStatus.CANCELLED.value],
    OrderStatus.COMPLETED.value: [OrderStatus.VALIDATED.value, OrderStatus.CANCELLED.value],
    OrderStatus.VALIDATED.value: [],
    OrderStatus.CANCELLED.value: [],
}


def can_transition(current: str, target: str) -> bool:
    """Return True if moving from *current* to *target* is a legal transition."""
    return target in _TRANSITIONS.get(current, [])


def enforce_transition(current: str, target: str) -> None:
    """Raise OrderStateError if the transition is not allowed.

    Using 409 Conflict (not 400 Bad Request) because the input is structurally
    valid — the issue is a state conflict, which is exactly what 409 models.
    """
    if not can_transition(current, target):
        allowed = _TRANSITIONS.get(current, [])
        detail = (
            f"Cannot move order from '{current}' to '{target}'. "
            f"Allowed transitions: {allowed or 'none (terminal state)'}."
        )
        raise OrderStateError(message=detail, status_code=409)


def assert_not_locked(order) -> None:
    """Raise OrderStateError(423) if the order has been validated and locked.

    Call this before any mutation that touches an order's results or samples
    (create result, delete result, update sample status, etc.).
    HTTP 423 is the semantically correct status for a locked resource.
    """
    if order.locked_at is not None:
        raise OrderStateError(
            message=(
                f"Order #{order.id} is locked (validated at "
                f"{order.locked_at.isoformat()}). "
                "Validated orders are immutable."
            ),
            status_code=423,
        )


def assert_not_cancelled(order) -> None:
    """Raise OrderStateError(409) if the order is already cancelled."""
    if order.status == "cancelled":
        raise OrderStateError(
            message=f"Order #{order.id} is cancelled and cannot be modified.",
            status_code=409,
        )
