"""MPI hash-chain and lock-ordering regressions (synthetic fixtures only).

Pins the defects where the timestamp fed into ``entry_hash`` was not the
timestamp persisted on the row (so no stored entry could reproduce its own
hash), where no verifier existed to detect tampering or a forked chain, and
where the two citizen row locks were taken in argument order (A→B / B→A
deadlock window).

All tests run on the SQLite test fixture. SQLite emits no ``FOR UPDATE``, so
lock-ordering evidence here is source-level plus behaviour-level only; no
PostgreSQL concurrency claim is made.
"""

from __future__ import annotations

import hashlib
import inspect
from datetime import datetime

import pytest
from app._compat import UTC
from app.models.lab import Lab
from app.models.patient import Patient
from app.services.mpi import resolver
from app.services.mpi.models import Citizen, IdentityClaim, MergeAudit


def _citizen(db, suffix: str, *, status: str = "active", merged_into_id=None) -> Citizen:
    c = Citizen(
        citizen_ulid=f"01CHAIN{suffix}0000000000000"[:26],
        name_canonical=f"synthetic chain person {suffix}",
        name_blocking_key=f"ch{suffix}"[:20],
        status=status,
        merged_into_id=merged_into_id,
    )
    db.add(c)
    db.flush()
    return c


@pytest.fixture()
def chain_fixture(db):
    lab = Lab(id=909011, name="Chain Test Lab", license_number="CHAIN-TEST-001")
    db.add(lab)
    db.flush()
    patients = []
    for i in range(2):
        p = Patient(
            lab_id=lab.id,
            full_name=f"Chain Patient {i}",
            phone=f"+964711111110{i}",
        )
        db.add(p)
        patients.append(p)
    db.flush()
    primary = _citizen(db, "PRIM")
    secondary = _citizen(db, "SECD")
    for p in patients:
        db.add(
            IdentityClaim(
                citizen_id=secondary.id,
                lab_id=lab.id,
                local_patient_id=p.id,
                match_method="probabilistic",
                match_features={"source": "synthetic"},
            )
        )
    db.flush()
    return primary, secondary


def _merge(db, primary: Citizen, secondary: Citizen, reason: str = "synthetic chain verification"):
    return resolver.merge_citizens(
        db,
        primary_ulid=primary.citizen_ulid,
        secondary_ulid=secondary.citizen_ulid,
        reason=reason,
        decided_by_user_id=42,
    )


def test_hashed_timestamp_equals_persisted_timestamp(chain_fixture, db):
    """F1: a stored audit row must reproduce its own entry_hash after expiry."""
    primary, secondary = chain_fixture
    audit = _merge(db, primary, secondary)
    db.flush()
    db.expire_all()

    fresh = db.query(MergeAudit).filter(MergeAudit.id == audit.id).one()
    row_dict = {
        "event_type": fresh.event_type,
        "primary_citizen_id": fresh.primary_citizen_id,
        "secondary_citizen_id": fresh.secondary_citizen_id,
        "match_score": None,
        "match_features": fresh.match_features,
        "decision_reason": fresh.decision_reason,
        "decided_by_user_id": fresh.decided_by_user_id,
        "occurred_at": resolver._occurred_at_iso(fresh.occurred_at),
        "prev_hash": fresh.prev_hash,
    }
    recomputed = hashlib.sha256(
        (fresh.prev_hash + resolver._canonical_json(row_dict)).encode()
    ).hexdigest()
    assert recomputed == fresh.entry_hash


def test_chain_verifier_accepts_a_clean_chain(chain_fixture, db):
    primary, secondary = chain_fixture
    _merge(db, primary, secondary)
    db.flush()
    db.expire_all()

    result = resolver.verify_merge_audit_chain(db)
    assert result.valid is True
    assert result.checked == 1
    assert result.errors == ()


def test_two_sequential_merges_form_a_linear_chain(db):
    a, b = _citizen(db, "LNA"), _citizen(db, "LNB")
    c, d = _citizen(db, "LNC"), _citizen(db, "LND")
    _merge(db, a, b, "synthetic first merge")
    db.flush()
    _merge(db, c, d, "synthetic second merge")
    db.flush()
    db.expire_all()

    rows = db.query(MergeAudit).order_by(MergeAudit.id.asc()).all()
    assert len(rows) == 2
    assert rows[0].prev_hash == "0" * 64
    assert rows[1].prev_hash == rows[0].entry_hash
    result = resolver.verify_merge_audit_chain(db)
    assert result.valid is True
    assert result.checked == 2


def test_verifier_detects_entry_hash_tampering(chain_fixture, db):
    primary, secondary = chain_fixture
    audit = _merge(db, primary, secondary)
    db.flush()

    # Bulk update simulates an out-of-band rewrite that bypasses application
    # guardrails; the application layer itself never updates an audit row.
    db.query(MergeAudit).filter(MergeAudit.id == audit.id).update(
        {MergeAudit.decision_reason: "tampered synthetic reason"},
        synchronize_session=False,
    )
    db.flush()
    db.expire_all()

    result = resolver.verify_merge_audit_chain(db)
    assert result.valid is False
    assert any("entry_hash" in error for error in result.errors)


def test_verifier_detects_forked_prev_hash(chain_fixture, db):
    primary, secondary = chain_fixture
    _merge(db, primary, secondary)
    db.flush()

    # Forge a second append that points at genesis instead of the real tail.
    genesis = "0" * 64
    occurred_at = datetime.now(UTC)
    forged_dict = {
        "event_type": "manual_merge",
        "primary_citizen_id": primary.id,
        "secondary_citizen_id": secondary.id,
        "match_score": None,
        "match_features": {},
        "decision_reason": "synthetic forked entry",
        "decided_by_user_id": 42,
        "occurred_at": resolver._occurred_at_iso(occurred_at),
        "prev_hash": genesis,
    }
    forged_hash = hashlib.sha256(
        (genesis + resolver._canonical_json(forged_dict)).encode()
    ).hexdigest()
    db.add(
        MergeAudit(
            event_type="manual_merge",
            primary_citizen_id=primary.id,
            secondary_citizen_id=secondary.id,
            match_score=None,
            match_features={},
            decision_reason="synthetic forked entry",
            decided_by_user_id=42,
            occurred_at=occurred_at,
            prev_hash=genesis,
            entry_hash=forged_hash,
        )
    )
    db.flush()
    db.expire_all()

    result = resolver.verify_merge_audit_chain(db)
    assert result.valid is False
    assert any("prev_hash" in error for error in result.errors)


def test_retry_after_failed_merge_succeeds_and_audits_once(chain_fixture, db, monkeypatch):
    primary, secondary = chain_fixture
    original = resolver._write_audit

    def _boom(*_args, **_kwargs):
        raise RuntimeError("synthetic transient audit failure")

    monkeypatch.setattr(resolver, "_write_audit", _boom)
    with pytest.raises(RuntimeError, match="transient"):
        _merge(db, primary, secondary, "synthetic retry after failure")
    db.expire_all()
    assert db.query(MergeAudit).filter(MergeAudit.event_type == "manual_merge").count() == 0

    monkeypatch.setattr(resolver, "_write_audit", original)
    audit = _merge(db, primary, secondary, "synthetic retry after failure")
    db.flush()
    db.expire_all()
    assert db.query(MergeAudit).filter(MergeAudit.event_type == "manual_merge").count() == 1
    assert resolver.verify_merge_audit_chain(db).valid is True
    assert audit.id is not None


def test_merge_rejects_missing_citizen(chain_fixture, db):
    primary, _secondary = chain_fixture
    with pytest.raises(ValueError, match="citizen not found"):
        resolver.merge_citizens(
            db,
            primary_ulid=primary.citizen_ulid,
            secondary_ulid="01MISSING0000000000000000"[:26],
            reason="synthetic missing citizen",
            decided_by_user_id=42,
        )


def test_merge_rejects_ineligible_primary(chain_fixture, db):
    primary, secondary = chain_fixture
    primary.status = "deceased"
    db.flush()
    with pytest.raises(ValueError, match="primary is not active"):
        _merge(db, primary, secondary)


def test_merge_rejects_secondary_with_existing_link(chain_fixture, db):
    primary, secondary = chain_fixture
    other = _citizen(db, "OTHR")
    db.flush()
    secondary.merged_into_id = other.id
    db.flush()
    with pytest.raises(ValueError, match="not a valid merge source"):
        _merge(db, primary, secondary)


def test_merge_succeeds_with_either_lock_argument_order(db):
    """Both call orders must complete; lock acquisition is key-sorted in source."""
    a, b = _citizen(db, "ORA"), _citizen(db, "ORB")
    _merge(db, a, b, "synthetic ascending ids")
    db.flush()
    assert db.query(Citizen).filter(Citizen.citizen_ulid == b.citizen_ulid).one().merged_into_id == a.id

    c, d = _citizen(db, "ORC"), _citizen(db, "ORD")
    _merge(db, d, c, "synthetic descending ids")
    db.flush()
    assert db.query(Citizen).filter(Citizen.citizen_ulid == c.citizen_ulid).one().merged_into_id == d.id

    db.expire_all()
    result = resolver.verify_merge_audit_chain(db)
    assert result.valid is True
    assert result.checked == 2


def test_citizen_locks_are_taken_in_one_key_ordered_statement():
    """Source invariant: a single ordered SELECT FOR UPDATE, no argument-order locks."""
    source = inspect.getsource(resolver.merge_citizens)
    assert source.count("with_for_update()") == 1
    start = source.index("locked = (")
    end = source.index("by_ulid =", start)
    lock_block = source[start:end]
    assert "Citizen.citizen_ulid.in_" in lock_block
    assert ".order_by(Citizen.id.asc())" in lock_block
    assert ".with_for_update()" in lock_block
