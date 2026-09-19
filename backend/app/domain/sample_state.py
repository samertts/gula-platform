"""Sample State Machine — single source of truth for specimen lifecycle.

Mirrors domain/order_state.py's pattern for the sibling Sample entity.

Valid transitions:
    collected  → received / processing / analyzed / rejected
    received   → processing / analyzed / rejected
    processing → analyzed / rejected
    analyzed   → (terminal — no further transitions allowed)
    rejected   → (terminal)

"Skip-ahead" transitions (e.g. collected → analyzed) are intentionally
permitted: device auto-ingestion (routes/device_results.py) legitimately
moves a sample straight to `analyzed` without an intermediate manual
`received`/`processing` step, and this module does not invent a stricter
ordering than what the rest of the codebase already relies on. What it
does close is *backward* movement out of a terminal state — a rejected or
already-analyzed sample can never be silently resurrected into an
in-progress state through a generic status-update endpoint.

Enforcement is done wherever a sample's status is mutated
(routes/samples.py, routes/device_results.py) so that no endpoint can
bypass the rules regardless of how it is called.
"""

from __future__ import annotations

from app._compat import StrEnum
from app.domain.exceptions import ConflictError


class SampleStatus(StrEnum):
    """Canonical status values for a Sample.

    Values match DB column strings for backward compatibility.
    """

    COLLECTED = "collected"
    RECEIVED = "received"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    REJECTED = "rejected"


_TRANSITIONS: dict[str, list[str]] = {
    SampleStatus.COLLECTED.value: [
        SampleStatus.RECEIVED.value,
        SampleStatus.PROCESSING.value,
        SampleStatus.ANALYZED.value,
        SampleStatus.REJECTED.value,
    ],
    SampleStatus.RECEIVED.value: [
        SampleStatus.PROCESSING.value,
        SampleStatus.ANALYZED.value,
        SampleStatus.REJECTED.value,
    ],
    SampleStatus.PROCESSING.value: [
        SampleStatus.ANALYZED.value,
        SampleStatus.REJECTED.value,
    ],
    SampleStatus.ANALYZED.value: [],
    SampleStatus.REJECTED.value: [],
}


def can_transition(current: str, target: str) -> bool:
    """Return True if moving from *current* to *target* is a legal transition."""
    return target in _TRANSITIONS.get(current, [])


def enforce_transition(current: str, target: str) -> None:
    """Raise ConflictError (409) if the transition is not allowed."""
    if not can_transition(current, target):
        allowed = _TRANSITIONS.get(current, [])
        raise ConflictError(
            f"Cannot move sample from '{current}' to '{target}'. "
            f"Allowed transitions: {allowed or 'none (terminal state)'}.",
        )
