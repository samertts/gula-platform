"""Conservative, pure-Python MPI identity-safety guards.

These helpers use only existing MPI fields. They do not invent Iraqi national
identifiers, set verification flags, create schema, or authorize merges. They
only fail closed when an existing record or caller input cannot support a
deterministic identity decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DETERMINISTIC_HIGH = "deterministic_high"
DETERMINISTIC_UNCERTAIN = "deterministic_uncertain"
NID_CONFLICT = "conflict"
NO_MATCH = "no_match"


@dataclass(frozen=True)
class NIDClassification:
    disposition: str
    reason: str


def classify_nid_match(
    *,
    profile_hash: str | None,
    candidate_hash: str | None,
    candidate_verified: bool,
    corroborated: bool,
) -> NIDClassification:
    """Classify an existing hashed NID comparison without assuming verification.

    The caller's raw NID is never trusted as verified here. An existing
    candidate's ``nid_verified`` flag must already be true, and independent
    secondary attributes must corroborate it, before an exact hash can be
    treated as deterministic.
    """
    if profile_hash and candidate_hash and profile_hash != candidate_hash:
        return NIDClassification(NID_CONFLICT, "conflicting NID hashes")
    if not profile_hash or not candidate_hash or profile_hash != candidate_hash:
        return NIDClassification(NO_MATCH, "no equal non-null NID hash")
    if not candidate_verified:
        return NIDClassification(
            DETERMINISTIC_UNCERTAIN, "candidate NID is not marked verified"
        )
    if not corroborated:
        return NIDClassification(
            DETERMINISTIC_UNCERTAIN, "no independent corroborating attributes"
        )
    return NIDClassification(DETERMINISTIC_HIGH, "verified and corroborated NID match")


def secondary_corroboration(profile: Any, candidate: Any) -> bool:
    """Require DOB agreement plus one independent strong attribute."""
    dob_match = (
        profile.birth_year is not None
        and profile.birth_year == getattr(candidate, "birth_year", None)
        and profile.birth_month == getattr(candidate, "birth_month", None)
        and profile.birth_day == getattr(candidate, "birth_day", None)
    )
    strong_match = (
        bool(profile.phone_last10)
        and profile.phone_last10 == getattr(candidate, "phone_last10", None)
    ) or (
        bool(profile.family_id_hash)
        and profile.family_id_hash == getattr(candidate, "family_id_hash", None)
    )
    return bool(dob_match and strong_match)


def assert_merge_allowed(
    primary: Any,
    secondary: Any,
    *,
    reason: str,
    decided_by_user_id: int | None,
) -> None:
    """Fail closed on merges that lack authority, safe state, or NID consistency."""
    if primary is None or secondary is None:
        raise ValueError("citizen not found")
    if getattr(primary, "id", None) == getattr(secondary, "id", None):
        raise ValueError("cannot merge a citizen with itself")
    if getattr(primary, "status", None) != "active":
        raise ValueError("primary is not active")
    if getattr(secondary, "status", None) == "merged":
        raise ValueError("secondary already merged")
    p_hash = getattr(primary, "nid_hash", None)
    s_hash = getattr(secondary, "nid_hash", None)
    if p_hash and s_hash and p_hash != s_hash:
        raise ValueError("refusing merge with conflicting NID hashes")
    if not reason or not reason.strip():
        raise ValueError("merge reason is required")
    if decided_by_user_id is None:
        raise ValueError("merge requires an authorized reviewer")
