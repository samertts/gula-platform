"""Wave 05.3 patient identity safety helpers.

These helpers reuse the canonical MPI NID classifier and Wave 05.2 linkage
guard. They never merge records automatically and never read raw national
numbers. Cross-facility linkage is a review decision, not a probabilistic
merge. All rollback operations append a new decision; they never delete or
rewrite an earlier one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.national.services.identity_governance import (
    LinkageCandidate,
    LinkageDecision,
    LinkageReviewer,
    append_linkage_rollback,
    assert_linkage_allowed,
)
from app.national.services.identity_persistence import (
    RegistrationRecord,
    assert_single_completed_registration,
)
from app.services.mpi.identity_safety import (
    DETERMINISTIC_HIGH,
    NID_CONFLICT,
    classify_nid_match,
    secondary_corroboration,
)


class PatientSafetyAction(StrEnum):
    PENDING_REVIEW = "PENDING_REVIEW"
    KEEP_SEPARATE = "KEEP_SEPARATE"
    LINK_APPROVED = "LINK_APPROVED"
    BLOCKED = "BLOCKED"


AUTO_MERGE_PROHIBITED = True


@dataclass(frozen=True)
class FacilityIdentityRecord:
    """Protected cross-facility view; no raw NID, name, or document image."""

    facility_id: str
    local_patient_id: str
    gula_citizen_identifier: str
    status: str = "active"
    nid_hash: str | None = None
    nid_verified: bool = False
    birth_year: int | None = None
    birth_month: int | None = None
    birth_day: int | None = None
    phone_last10: str | None = None
    family_id_hash: str | None = None
    name_similarity: float | None = None
    mother_name_similarity: float | None = None
    dob_match: bool | None = None
    old_medical_record_reference: str | None = None
    correction_count: int = 0

    def __post_init__(self) -> None:
        if not self.facility_id.strip() or not self.local_patient_id.strip():
            raise ValueError("facility and local patient reference are required")
        if not self.gula_citizen_identifier.strip():
            raise ValueError("GULA Citizen Identifier reference is required")
        for label, value in (
            ("name_similarity", self.name_similarity),
            ("mother_name_similarity", self.mother_name_similarity),
        ):
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{label} must be between 0 and 1")
        if self.correction_count < 0:
            raise ValueError("correction_count cannot be negative")

    def as_linkage_candidate(self) -> LinkageCandidate:
        return LinkageCandidate(
            id=self.gula_citizen_identifier,
            status=self.status,
            nid_hash=self.nid_hash,
            nid_verified=self.nid_verified,
            birth_year=self.birth_year,
            birth_month=self.birth_month,
            birth_day=self.birth_day,
            phone_last10=self.phone_last10,
            family_id_hash=self.family_id_hash,
        )


@dataclass(frozen=True)
class PatientSafetyDecision:
    action: PatientSafetyAction
    primary_identifier: str
    secondary_identifier: str
    reasons: tuple[str, ...]
    reviewer: str
    evidence_reference: str
    decided_at: datetime
    audit_metadata: dict[str, object]
    merged: bool = False

    def __post_init__(self) -> None:
        if self.merged:
            raise ValueError("automatic merge is prohibited")
        if not self.primary_identifier or not self.secondary_identifier:
            raise ValueError("both identity references are required")
        if not self.reviewer.strip() or not self.evidence_reference.strip():
            raise ValueError("reviewer and evidence reference are required")


def _metadata(
    primary: FacilityIdentityRecord,
    secondary: FacilityIdentityRecord,
    *,
    reasons: tuple[str, ...],
    decision: str,
    reviewer: LinkageReviewer,
    evidence_reference: str,
    nid_disposition: str,
) -> dict[str, object]:
    return {
        "primary_gula_identifier": primary.gula_citizen_identifier,
        "secondary_gula_identifier": secondary.gula_citizen_identifier,
        "primary_facility": primary.facility_id,
        "secondary_facility": secondary.facility_id,
        "nid_disposition": nid_disposition,
        "similarity_only": primary.name_similarity is not None
        or primary.mother_name_similarity is not None
        or primary.dob_match is not None,
        "reasons": list(reasons),
        "decision": decision,
        "reviewer": reviewer.name,
        "evidence_reference": evidence_reference,
        "old_medical_record_references": tuple(
            value
            for value in (primary.old_medical_record_reference, secondary.old_medical_record_reference)
            if value is not None
        ),
        "correction_counts": {
            "primary": primary.correction_count,
            "secondary": secondary.correction_count,
        },
        "automatic_merge": False,
    }


def cross_facility_linkage_decision(
    primary: FacilityIdentityRecord,
    secondary: FacilityIdentityRecord,
    *,
    decision: str,
    reviewer: LinkageReviewer,
    reason: str,
    evidence_reference: str,
    decided_at: datetime,
) -> PatientSafetyDecision:
    """Decide whether to link two facility records without auto-merging them."""
    if decision not in {"APPROVED", "REJECTED", "PENDING"}:
        raise ValueError("decision must be APPROVED, REJECTED, or PENDING")

    primary_candidate = primary.as_linkage_candidate()
    secondary_candidate = secondary.as_linkage_candidate()
    classification = classify_nid_match(
        profile_hash=primary.nid_hash,
        candidate_hash=secondary.nid_hash,
        candidate_verified=secondary.nid_verified,
        corroborated=secondary_corroboration(primary_candidate, secondary_candidate),
    )
    reasons: list[str] = []

    if primary.nid_hash is None or secondary.nid_hash is None:
        reasons.append("NID hash is missing for at least one record")
    if primary.gula_citizen_identifier == secondary.gula_citizen_identifier:
        reasons.append("records share the same GULA Citizen Identifier")
    if primary.correction_count or secondary.correction_count:
        reasons.append("correction history is present and must be preserved")
    if (
        primary.name_similarity is not None
        or primary.mother_name_similarity is not None
        or primary.dob_match is not None
    ) and classification.disposition != DETERMINISTIC_HIGH:
        reasons.append("name/mother-name/DOB similarity alone is not authority to merge")
    if classification.disposition == NID_CONFLICT:
        reasons.append("conflicting NID hashes block linkage")

    if classification.disposition == NID_CONFLICT:
        action = PatientSafetyAction.BLOCKED
    elif decision == "REJECTED":
        action = PatientSafetyAction.KEEP_SEPARATE
        reasons.append("reviewer rejected linkage")
    elif (
        primary.nid_hash is None
        or secondary.nid_hash is None
        or decision == "PENDING"
        or not reason.strip()
        or not evidence_reference.strip()
        or classification.disposition != DETERMINISTIC_HIGH
    ):
        action = PatientSafetyAction.PENDING_REVIEW
        reasons.append("linkage requires complete protected NID evidence and explicit approval")
    else:
        assert_linkage_allowed(
            primary_candidate,
            secondary_candidate,
            decision=decision,
            reviewer=reviewer,
            reason=reason,
            evidence_reference=evidence_reference,
        )
        action = PatientSafetyAction.LINK_APPROVED
        reasons.append("explicit reviewer-approved link; records remain separate")

    return PatientSafetyDecision(
        action=action,
        primary_identifier=primary.gula_citizen_identifier,
        secondary_identifier=secondary.gula_citizen_identifier,
        reasons=tuple(reasons),
        reviewer=reviewer.name,
        evidence_reference=evidence_reference or "MISSING-EVIDENCE",
        decided_at=decided_at,
        audit_metadata=_metadata(
            primary,
            secondary,
            reasons=tuple(reasons),
            decision=decision,
            reviewer=reviewer,
            evidence_reference=evidence_reference or "MISSING-EVIDENCE",
            nid_disposition=str(classification.disposition),
        ),
        merged=False,
    )


def assert_no_duplicate_registration(
    records: list[RegistrationRecord] | tuple[RegistrationRecord, ...],
    *,
    subject_reference: str,
) -> RegistrationRecord:
    """Reject duplicate completed citizen files for one subject reference."""
    return assert_single_completed_registration(records, subject_reference)


@dataclass(frozen=True)
class LinkageRollbackOutcome:
    decision: LinkageDecision
    original_decision_retained: bool
    audit_metadata: dict[str, object]


def build_linkage_decision(
    *,
    primary_identifier: str,
    secondary_identifier: str,
    reviewer: LinkageReviewer,
    reason: str,
    evidence_reference: str,
    decided_at: datetime,
) -> LinkageDecision:
    """Create a canonical Wave 05.2 linkage decision record."""
    return LinkageDecision(
        primary_identifier=primary_identifier,
        secondary_identifier=secondary_identifier,
        reviewer=reviewer,
        reason=reason,
        evidence_reference=evidence_reference,
        decided_at=decided_at,
        active=True,
    )


def rollback_patient_linkage(
    decision: LinkageDecision,
    *,
    reviewer: LinkageReviewer,
    reason: str,
    rolled_back_at: datetime,
    original_decision_retained: bool = True,
) -> LinkageRollbackOutcome:
    """Append a rollback while preserving the original decision."""
    if not original_decision_retained:
        raise ValueError("original linkage decision must be retained")
    updated = append_linkage_rollback(
        decision,
        reviewer=reviewer,
        reason=reason,
        rolled_back_at=rolled_back_at,
    )
    return LinkageRollbackOutcome(
        decision=updated,
        original_decision_retained=True,
        audit_metadata={
            "primary_identifier": updated.primary_identifier,
            "secondary_identifier": updated.secondary_identifier,
            "original_decided_at": decision.decided_at.isoformat(),
            "rolled_back_at": rolled_back_at.isoformat(),
            "reviewer": reviewer.name,
            "reason": reason,
            "original_decision_retained": True,
            "automatic_merge": False,
        },
    )


__all__ = [
    "AUTO_MERGE_PROHIBITED",
    "FacilityIdentityRecord",
    "LinkageRollbackOutcome",
    "PatientSafetyAction",
    "PatientSafetyDecision",
    "assert_no_duplicate_registration",
    "build_linkage_decision",
    "cross_facility_linkage_decision",
    "rollback_patient_linkage",
]
