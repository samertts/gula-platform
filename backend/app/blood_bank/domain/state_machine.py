"""Explicit Blood Bank lifecycle transitions.

This module is pure domain logic: persistence and authorization remain in the
application layer, while every state change is checked against one canonical
transition map.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.blood_bank.exceptions import BloodBankWorkflowError


class BloodBankState(StrEnum):
    RECEIVED = "received"
    TESTING = "testing"
    QUARANTINED = "quarantined"
    RELEASED = "released"
    RESERVED = "reserved"
    ISSUED = "issued"
    RECEIVED_AT_BEDSIDE = "received_at_bedside"
    TRANSFUSED = "transfused"
    RETURNED = "returned"
    DISCARDED = "discarded"
    EXPIRED = "expired"
    DRAFT = "draft"
    REQUESTED = "requested"
    REVIEWED = "reviewed"
    COMPATIBILITY_PENDING = "compatibility_pending"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    COLLECTED = "collected"
    IDENTIFIED = "identified"
    VALIDATED = "validated"
    SAMPLE_EXPIRED = "sample_expired"
    SAMPLE_REJECTED = "sample_rejected"
    CROSSMATCH_REQUESTED = "crossmatch_requested"
    SAMPLE_REQUIRED = "sample_required"
    SAMPLE_RECEIVED = "sample_received"
    CROSSMATCH_TESTING = "crossmatch_testing"
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    VERIFICATION = "verification"
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    REACTION_SUSPECTED = "reaction_suspected"
    TRANSFUSION_STOPPED = "transfusion_stopped"
    CLINICAL_ASSESSMENT = "clinical_assessment"
    INVESTIGATION = "investigation"
    CLASSIFICATION = "classification"
    RESOLUTION = "resolution"


_TRANSITIONS: dict[str, set[str]] = {
    "received": {"testing", "quarantined"},
    "testing": {"quarantined", "released", "rejected"},
    "quarantined": {"testing", "released", "discarded"},
    "released": {"reserved", "issued", "expired", "discarded", "quarantined"},
    "available": {"reserved", "issued", "expired", "discarded", "quarantined"},
    # This table is shared by every Blood Bank entity, so a state name may only
    # appear once: a repeated key silently shadows the earlier entry.  "reserved"
    # is reached by both a blood unit and an order, so both sets are merged here.
    "reserved": {"released", "available", "issued", "expired", "discarded", "cancelled"},
    "issued": {"received_at_bedside", "returned", "transfused", "discarded", "quarantined"},
    "received_at_bedside": {"verification", "returned"},
    "transfused": {"discarded", "quarantined"},
    "returned": {"released", "discarded"},
    "expired": {"discarded"},
    "draft": {"requested", "cancelled"},
    "requested": {"reviewed", "rejected", "cancelled", "expired"},
    "reviewed": {"compatibility_pending", "ready", "rejected", "cancelled"},
    "compatibility_pending": {"ready", "rejected", "cancelled"},
    "ready": {"reserved", "cancelled", "expired"},
    "issued_order": {"completed", "cancelled"},
    "collected": {"identified", "rejected"},
    "identified": {"received", "rejected"},
    "received_sample": {"testing", "rejected", "sample_expired"},
    "validated": {"sample_expired"},
    "crossmatch_requested": {"sample_required", "sample_received"},
    "sample_required": {"sample_received", "incompatible"},
    "sample_received": {"testing", "incompatible"},
    "testing_crossmatch": {"compatible", "incompatible"},
    "compatible": {"validated", "incompatible"},
    "incompatible": set(),
    "ordered_transfusion": {"verification", "cancelled"},
    "verification": {"started", "returned", "reaction_suspected"},
    "started": {"in_progress", "reaction_suspected"},
    # The transfusion entity's own vocabulary is TransfusionStatus, and its
    # lifecycle is ordered -> verified -> in_progress -> completed.
    # "verified" was missing, so start_transfusion_safely could never succeed:
    # it requires status == VERIFIED and then asks this table to validate
    # verified -> in_progress. "in_progress" -> "completed" below is already
    # keyed on the real status values, which is what makes the omission a gap
    # rather than a different naming scheme. Same defect class as NR-004, where
    # a blood-unit state was likewise absent from this shared table.
    # "verification"/"started" above are written by no code path.
    "verified": {"in_progress"},
    "in_progress": {"completed", "reaction_suspected"},
    "completed": set(),
    "reaction_suspected": {"transfusion_stopped"},
    "transfusion_stopped": {"clinical_assessment"},
    "clinical_assessment": {"investigation", "resolution"},
    "investigation": {"classification", "resolution"},
    "classification": {"resolution"},
    "resolution": set(),
}


def transition(current: str, target: str, *, entity: str = "blood_bank_resource") -> str:
    """Validate and return the target state, failing closed on unknown states."""
    allowed = _TRANSITIONS.get(current)
    if allowed is None or target not in allowed:
        raise BloodBankWorkflowError(f"Invalid {entity} transition: {current} -> {target}")
    return target


@dataclass(frozen=True)
class Transition:
    entity: str
    before: str
    after: str

    def validate(self) -> "Transition":
        transition(self.before, self.after, entity=self.entity)
        return self
