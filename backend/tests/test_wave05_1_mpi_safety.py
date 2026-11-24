"""Wave 05.1 — deterministic MPI identity-safety guards.

Synthetic identities only. No Iraqi national ID format, checksum or registry
mapping is invented; raw values below are explicitly synthetic test inputs.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.identity import hash_national_id
from app.services.mpi.identity_safety import (
    DETERMINISTIC_HIGH,
    DETERMINISTIC_UNCERTAIN,
    NID_CONFLICT,
    assert_merge_allowed,
    classify_nid_match,
)
from app.services.mpi.models import Citizen
from app.services.mpi.resolver import merge_citizens, resolve_identity


def _profile(**overrides):
    values = {
        "birth_year": 1990,
        "birth_month": 5,
        "birth_day": 12,
        "phone_last10": "7901234567",
        "family_id_hash": "family-synthetic",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_nid_match_requires_verification_and_corroboration() -> None:
    h = "a" * 64
    assert classify_nid_match(
        profile_hash=h,
        candidate_hash=h,
        candidate_verified=False,
        corroborated=True,
    ).disposition == DETERMINISTIC_UNCERTAIN
    assert classify_nid_match(
        profile_hash=h,
        candidate_hash=h,
        candidate_verified=True,
        corroborated=False,
    ).disposition == DETERMINISTIC_UNCERTAIN
    assert classify_nid_match(
        profile_hash=h,
        candidate_hash=h,
        candidate_verified=True,
        corroborated=True,
    ).disposition == DETERMINISTIC_HIGH
    assert classify_nid_match(
        profile_hash=h,
        candidate_hash="b" * 64,
        candidate_verified=True,
        corroborated=True,
    ).disposition == NID_CONFLICT


def test_merge_guard_requires_reviewer_reason_and_consistent_nids() -> None:
    primary = SimpleNamespace(id=1, status="active", nid_hash="a" * 64)
    secondary = SimpleNamespace(id=2, status="active", nid_hash="a" * 64)
    assert_merge_allowed(primary, secondary, reason="synthetic review", decided_by_user_id=7)

    with pytest.raises(ValueError):
        assert_merge_allowed(
            primary,
            SimpleNamespace(id=2, status="active", nid_hash="b" * 64),
            reason="synthetic review",
            decided_by_user_id=7,
        )
    with pytest.raises(ValueError):
        assert_merge_allowed(primary, secondary, reason="synthetic review", decided_by_user_id=None)
    with pytest.raises(ValueError):
        assert_merge_allowed(primary, secondary, reason="", decided_by_user_id=7)


def _citizen(db, *, ulid: str, nid_hash: str | None, verified: bool, **kwargs) -> Citizen:
    values = {
        "citizen_ulid": ulid,
        "name_canonical": "synthetic person",
        "name_blocking_key": "synth",
        "phone_last10": "7901234567",
        "birth_year": 1990,
        "birth_month": 5,
        "birth_day": 12,
        "gender": "M",
        "family_id_hash": "family-synthetic",
        "nid_hash": nid_hash,
        "nid_verified": verified,
        "status": "active",
        "version": 1,
    }
    values.update(kwargs)
    citizen = Citizen(**values)
    db.add(citizen)
    db.flush()
    return citizen


def _resolve_kwargs(raw_nid: str) -> dict:
    return {
        "lab_id": 1,
        "local_patient_id": 1,
        "name": "Synthetic Person",
        "phone": "07901234567",
        "birth_year": 1990,
        "birth_month": 5,
        "birth_day": 12,
        "gender": "M",
        "national_id": raw_nid,
        "family_id": "family-synthetic",
        "claimed_by_user_id": 7,
    }


def test_unverified_nid_hit_is_pending_not_auto(db) -> None:
    raw = "0000000001"  # synthetic test value, not an Iraqi national ID
    candidate = _citizen(
        db,
        ulid="01MPISAFETYUNVERIFIED00000001"[:26],
        nid_hash=hash_national_id(raw),
        verified=False,
    )
    outcome = resolve_identity(db, **_resolve_kwargs(raw))
    assert outcome.created is False
    assert outcome.match_method == "pending_review"
    assert outcome.citizen.id == candidate.id
    assert outcome.features["nid_classification"] == DETERMINISTIC_UNCERTAIN


def test_verified_corroborated_nid_hit_is_deterministic(db) -> None:
    raw = "0000000002"  # synthetic test value, not an Iraqi national ID
    candidate = _citizen(
        db,
        ulid="01MPISAFETYVERIFIED0000000001"[:26],
        nid_hash=hash_national_id(raw),
        verified=True,
    )
    outcome = resolve_identity(db, **_resolve_kwargs(raw))
    assert outcome.match_method == "nid_exact"
    assert outcome.citizen.id == candidate.id
    assert outcome.features["nid_classification"] == DETERMINISTIC_HIGH


def test_conflicting_nid_vetoes_probabilistic_auto_claim(db) -> None:
    raw = "0000000003"  # synthetic test value, not an Iraqi national ID
    _citizen(
        db,
        ulid="01MPISAFETYCONFLICT0000000001"[:26],
        nid_hash=hash_national_id("0000000004"),  # synthetic, non-Iraqi value
        verified=True,
    )
    outcome = resolve_identity(db, **_resolve_kwargs(raw))
    assert outcome.created is True
    assert outcome.claim.match_method == "new"


def test_pending_claim_survives_replay_without_promotion(db) -> None:
    raw = "0000000005"  # synthetic test value, not an Iraqi national ID
    _citizen(
        db,
        ulid="01MPISAFETYREPLAY000000000001"[:26],
        nid_hash=hash_national_id(raw),
        verified=False,
    )
    first = resolve_identity(db, **_resolve_kwargs(raw))
    second = resolve_identity(db, **_resolve_kwargs(raw))
    assert first.match_method == second.match_method == "pending_review"
    assert first.claim.id == second.claim.id


def test_merge_guard_blocks_conflicting_nid_merge(db) -> None:
    primary = _citizen(
        db,
        ulid="01MPIMERGEPRIMARY000000000001"[:26],
        nid_hash=hash_national_id("0000000006"),  # synthetic, non-Iraqi value
        verified=True,
    )
    secondary = _citizen(
        db,
        ulid="01MPIMERGESECOND0000000000001"[:26],
        nid_hash=hash_national_id("0000000007"),  # synthetic, non-Iraqi value
        verified=True,
    )
    with pytest.raises(ValueError):
        merge_citizens(
            db,
            primary_ulid=primary.citizen_ulid,
            secondary_ulid=secondary.citizen_ulid,
            reason="synthetic unauthorized merge",
            decided_by_user_id=7,
        )
    db.expire_all()
    assert db.query(Citizen).filter(Citizen.id == secondary.id).one().status == "active"
