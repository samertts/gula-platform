"""Explicit, auditable payment and refund state transitions."""
from __future__ import annotations

from app.domain.exceptions import ConflictError

PAYMENT_INTENT_TRANSITIONS: dict[str, frozenset[str]] = {
    "CREATED": frozenset({"PENDING", "CANCELLED", "EXPIRED"}),
    "PENDING": frozenset({"PROCESSING", "CANCELLED", "EXPIRED", "UNKNOWN"}),
    "AUTHORIZED": frozenset({"PROCESSING", "CANCELLED", "EXPIRED", "UNKNOWN"}),
    "PROCESSING": frozenset({"SUCCEEDED", "FAILED", "UNKNOWN", "CANCELLED"}),
    "UNKNOWN": frozenset({"PROCESSING", "SUCCEEDED", "FAILED", "CANCELLED", "EXPIRED"}),
    "SUCCEEDED": frozenset({"SETTLED", "REFUND_PENDING", "DISPUTED", "REVERSED"}),
    "REFUND_PENDING": frozenset({"SUCCEEDED", "REVERSED"}),
    "SETTLED": frozenset({"REFUND_PENDING", "DISPUTED", "REVERSED"}),
    "FAILED": frozenset(),
    "EXPIRED": frozenset(),
    "CANCELLED": frozenset(),
    "REVERSED": frozenset(),
    "DISPUTED": frozenset({"SETTLED", "REVERSED"}),
}

REFUND_TRANSITIONS: dict[str, frozenset[str]] = {
    "REQUESTED": frozenset({"APPROVED", "REJECTED"}),
    "APPROVED": frozenset({"PROCESSING", "REJECTED"}),
    "PROCESSING": frozenset({"SUCCEEDED", "FAILED"}),
    "SUCCEEDED": frozenset(),
    "FAILED": frozenset({"PROCESSING"}),
    "REJECTED": frozenset(),
}


def assert_transition(current: str, target: str, transitions: dict[str, frozenset[str]], entity: str) -> None:
    if target not in transitions.get(current, frozenset()):
        raise ConflictError(f"Illegal {entity} state transition: {current} -> {target}")


def transition_payment(intent, target: str) -> None:
    assert_transition(intent.status, target, PAYMENT_INTENT_TRANSITIONS, "payment intent")
    intent.status = target


def transition_refund(refund, target: str) -> None:
    assert_transition(refund.status, target, REFUND_TRANSITIONS, "refund")
    refund.status = target
