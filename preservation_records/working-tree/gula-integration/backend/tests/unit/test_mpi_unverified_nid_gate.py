"""AUD-MPI-001 regression — unverified NIDs must never auto-claim an identity.

Synthetic-only tests. The MPI previously treated hash equality of a submitted
(raw, lab-supplied) national ID as authoritative even though every MPI write
path stores ``nid_verified=False``. A wrong or stale NID could therefore bind a
patient to another person's canonical record with match_score 1.0.

These tests pin the fail-closed gate:
* unverified NID + conflicting demographics => pending_review, no auto-claim;
* verified NID => nid_exact still works (no regression to AUD-04 idempotency);
* the genesis record is created with nid_verified=False.
"""

from __future__ import annotations

import pytest
from app.models.lab import Lab
from app.services.mpi import resolver

LAB_ID = 909500
NID = "synthetic-unverified-nid-0001"


@pytest.fixture()
def mpi_lab(db):
    lab = db.query(Lab).filter(Lab.id == LAB_ID).first()
    if lab is None:
        lab = Lab(id=LAB_ID, name="Synthetic MPI Gate Lab", license_number="SYN-MPIGATE-001")
        db.add(lab)
        db.flush()
    return lab


def _resolve(db, lab_id, local_id, name, *, phone, birth, gender):
    return resolver.resolve_identity(
        db,
        lab_id=lab_id,
        local_patient_id=local_id,
        name=name,
        phone=phone,
        birth_year=birth[0],
        birth_month=birth[1],
        birth_day=birth[2],
        gender=gender,
        national_id=NID,
    )


def test_genesis_citizen_has_unverified_nid(mpi_lab, db):
    outcome = _resolve(
        db, mpi_lab.id, 1, "Synthetic Person Alpha",
        phone="+964700000001", birth=(1990, 1, 1), gender="M",
    )
    assert outcome.created is True
    assert outcome.citizen.nid_verified is False
    assert outcome.citizen.nid_hash is not None


def test_unverified_nid_conflicting_demographics_forces_review(mpi_lab, db):
    first = _resolve(
        db, mpi_lab.id, 1, "Synthetic Person Alpha",
        phone="+964700000001", birth=(1990, 1, 1), gender="M",
    )
    assert first.citizen.nid_verified is False

    second = _resolve(
        db, mpi_lab.id, 2, "Completely Different Person Beta",
        phone="+964700009999", birth=(1975, 12, 31), gender="F",
    )

    # Same unverified NID, totally different demographics: reuse the existing
    # row (no duplicate NID) but NEVER auto-claim it.
    assert second.created is False
    assert second.citizen.id == first.citizen.id
    assert second.match_method == "pending_review"
    assert second.match_score is not None
    assert second.match_score < 0.90
    assert second.features.get("nid_hash") is True
    assert second.features.get("nid_verified") is False
    assert second.features.get("nid_not_authoritative") is True


def test_unverified_nid_same_demographics_does_not_use_nid_shortcut(mpi_lab, db):
    first = _resolve(
        db, mpi_lab.id, 1, "Synthetic Person Alpha",
        phone="+964700000001", birth=(1990, 1, 1), gender="M",
    )
    assert first.citizen.nid_verified is False

    second = _resolve(
        db, mpi_lab.id, 2, "Synthetic Person Alpha",
        phone="+964700000001", birth=(1990, 1, 1), gender="M",
    )

    # Demographic agreement yields a probabilistic score (0.85 with these
    # weights) that stays below the auto-match threshold — no nid_exact claim.
    assert second.match_method != "nid_exact"
    assert second.match_score is not None
    assert second.match_score < 1.0


def test_verified_nid_still_auto_claims(mpi_lab, db):
    first = _resolve(
        db, mpi_lab.id, 1, "Synthetic Person Alpha",
        phone="+964700000001", birth=(1990, 1, 1), gender="M",
    )
    first.citizen.nid_verified = True
    db.flush()

    second = _resolve(
        db, mpi_lab.id, 2, "Completely Different Person Beta",
        phone="+964700009999", birth=(1975, 12, 31), gender="F",
    )

    assert second.created is False
    assert second.citizen.id == first.citizen.id
    assert second.match_method == "nid_exact"
    assert second.match_score == 1.0
    assert second.features.get("nid_verified") is True
