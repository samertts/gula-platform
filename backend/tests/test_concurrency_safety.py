"""Concurrency & optimistic-lock safety — Phase 3 hardening.

Production invariants asserted (CLAUDE.md §Security Invariants):
  #6 — Optimistic lock (`version` column) MUST be checked on every
       LabResult mutation.
  #2 — Every mutation MUST write to the audit log.

What this suite covers (additive, no production code changes):

  1. Concurrent order-validation: two simultaneous validators → exactly one
     wins, the other gets HTTP 409.  The compare-and-swap is at
     routes/results.py:408 (UPDATE … WHERE locked_at IS NULL).
  2. Concurrent result verification: same pattern in
     routes/test_results.py:488 — one verify wins, the other 409s.
  3. State-machine guard: after `validated`, all mutating endpoints must
     refuse the locked order with 423 (or 409).
  4. Sample status updates honour the locked-order guard.
  5. ORM ``LabResult.version`` column exists and starts at 1 — required by
     the documented optimistic-lock invariant; this test fails loudly if
     the column is removed in a future schema change.

These tests use the existing single-process, single-engine SQLite fixture.
True multi-thread races against PG locks require integration tests; the
SQLite path is sufficient to catch logic regressions in the CAS pattern
(``UPDATE ... WHERE`` returning rows_updated).

Laboratory vertical-slice hardening (Mustafa, this pass) adds:

  6. cancel_order previously had NO compare-and-swap at all — only the
     sequential `enforce_transition` check, which reads the order's
     in-memory `status` captured before any concurrent request runs. A
     order validated by a concurrent request between that check and
     cancel_order's commit had its status silently overwritten back to
     "cancelled", defeating the documented "validated is terminal /
     immutable" invariant. Fixed by adding the same
     ``UPDATE ... WHERE locked_at IS NULL`` backstop validate_order already
     uses. TestOrderCancelRace proves the race with a real interleaving
     (not a mock of the DB layer) and proves the fix closes it.
  7. samples.py::update_sample had no role gate at all (any authenticated
     account of any role could reject/finalize a sample) and no status
     state machine (arbitrary transitions, including resurrecting a
     rejected/analyzed sample). Fixed via domain/sample_state.py (mirrors
     order_state.py) plus the same class of atomic backstop as #6, using
     the sample's own `status` as a compare-and-swap token in place of a
     dedicated version column (which does not exist on Sample — see
     MUSTAFA_ACTIVE_REPAIR_QUEUE.md for why that is a separate,
     migration-requiring follow-up, not silently left ambiguous).
  8. device_results.py's auto-ingestion previously blocked re-processing
     only a "rejected" sample, not an already-"analyzed" one — a replayed
     device submission could silently create duplicate LabResult rows.
     Fixed by routing through the same domain/sample_state.py guard.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

os.environ["RUNTIME_MODE"] = "test"
os.environ["FEATURE_BACKGROUND_TASKS"] = "false"
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import pytest
from app.models.lab import Lab
from app.models.lab_order import LabOrder
from app.models.lab_result import LabResult
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.models.sample import Sample
from app.security.auth import create_token, hash_password


def _hdr(user_id: int, lab_id: int, role: str = "admin") -> dict:
    token = create_token({"user_id": user_id, "lab_id": lab_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def lab_with_completed_order(db):
    """Set up a lab with an order in 'completed' state with one result, ready
    to be validated. The order has no locked_at, so two validators racing
    should both initially see it as unlocked."""
    lab = Lab(name="Concurrency Lab", license_number="LIC-CON",
              lab_type="private", city="Baghdad", is_active=True)
    db.add(lab)
    db.flush()

    admin1 = LabUser(
        lab_id=lab.id, name="Admin1", email="a1@con.com",
        password_hash=hash_password("Pa55word"), role="admin", is_active=True,
    )
    admin2 = LabUser(
        lab_id=lab.id, name="Admin2", email="a2@con.com",
        password_hash=hash_password("Pa55word"), role="admin", is_active=True,
    )
    db.add_all([admin1, admin2])
    db.flush()

    patient = Patient(lab_id=lab.id, full_name="P", phone="07700123123",
                      health_id="HID-CON-001")
    db.add(patient)
    db.flush()

    # status='completed' so the validation transition is legal
    order = LabOrder(lab_id=lab.id, patient_id=patient.id, status="completed")
    db.add(order)
    db.flush()

    result = LabResult(order_id=order.id, test_name="Glucose", value=95.0,
                       unit="mg/dL", flag="normal")
    db.add(result)
    db.commit()

    return {"lab": lab, "admin1": admin1, "admin2": admin2,
            "patient": patient, "order": order, "result": result}


# ─── Phase 3.A — Order validation compare-and-swap ───────────────────────────


class TestOrderValidationCAS:
    """``POST /orders/{id}/validate`` uses an UPDATE ... WHERE locked_at IS NULL
    compare-and-swap (results.py:408). Verify the CAS holds under sequential
    duplicate calls (the SQLite test client cannot truly race threads against
    a single in-memory engine, but the second call MUST hit the 'already
    locked' branch deterministically)."""

    def test_first_validation_succeeds(self, client, lab_with_completed_order):
        admin = lab_with_completed_order["admin1"]
        order = lab_with_completed_order["order"]
        res = client.post(
            f"/orders/{order.id}/validate",
            headers=_hdr(admin.id, lab_with_completed_order["lab"].id),
        )
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "validated"
        assert body["locked"] is True
        assert body["validated_by"] == admin.id

    def test_second_validation_returns_409(self, client, lab_with_completed_order):
        """Two consecutive validate calls — second must 409 (CAS missed)."""
        admin1 = lab_with_completed_order["admin1"]
        admin2 = lab_with_completed_order["admin2"]
        order = lab_with_completed_order["order"]

        first = client.post(
            f"/orders/{order.id}/validate",
            headers=_hdr(admin1.id, lab_with_completed_order["lab"].id),
        )
        assert first.status_code == 200

        # second admin tries to validate the same order — must fail
        second = client.post(
            f"/orders/{order.id}/validate",
            headers=_hdr(admin2.id, lab_with_completed_order["lab"].id),
        )
        # The state-machine guard fires first (validated → validated is
        # not allowed) and returns 409. The CAS would have caught it as a
        # backstop. Either is correct refusal.
        assert second.status_code == 409

    def test_validated_by_recorded_correctly(self, client, db, lab_with_completed_order):
        """The winning caller must be recorded as validated_by — never the
        loser. Verifies the CAS doesn't silently overwrite validator identity."""
        admin1 = lab_with_completed_order["admin1"]
        admin2 = lab_with_completed_order["admin2"]
        order = lab_with_completed_order["order"]

        client.post(
            f"/orders/{order.id}/validate",
            headers=_hdr(admin1.id, lab_with_completed_order["lab"].id),
        )
        # Even if admin2 attempts after, validated_by must remain admin1
        client.post(
            f"/orders/{order.id}/validate",
            headers=_hdr(admin2.id, lab_with_completed_order["lab"].id),
        )

        db.expire_all()
        order_db = db.query(LabOrder).filter(LabOrder.id == order.id).first()
        assert order_db.validated_by == admin1.id
        assert order_db.validated_by != admin2.id


# ─── Phase 3.B — Locked-order immutability ───────────────────────────────────


class TestLockedOrderImmutability:
    """After validation, the order's results and samples are immutable.
    domain/order_state.py:assert_not_locked is the gate. Verify each mutating
    endpoint refuses correctly."""

    def test_validated_order_cannot_be_cancelled(self, client, lab_with_completed_order):
        admin = lab_with_completed_order["admin1"]
        order = lab_with_completed_order["order"]

        client.post(
            f"/orders/{order.id}/validate",
            headers=_hdr(admin.id, lab_with_completed_order["lab"].id),
        )
        # Try to cancel after validation — terminal state, should 409 or 423
        res = client.post(
            f"/orders/{order.id}/cancel",
            headers=_hdr(admin.id, lab_with_completed_order["lab"].id),
        )
        assert res.status_code in (409, 423)

    def test_validated_order_blocks_sample_status_updates(
        self, client, db, lab_with_completed_order
    ):
        """Adding a sample to a locked order, then trying to mutate it,
        must yield 423 (locked) or 409."""
        admin = lab_with_completed_order["admin1"]
        order = lab_with_completed_order["order"]

        # Attach a sample BEFORE locking so we have something to mutate
        sample = Sample(order_id=order.id, sample_type="blood",
                        barcode="BC-LOCK-001", status="collected")
        db.add(sample)
        db.commit()

        # Lock the order
        client.post(
            f"/orders/{order.id}/validate",
            headers=_hdr(admin.id, lab_with_completed_order["lab"].id),
        )

        # Now try to update the sample on the locked order
        res = client.put(
            "/samples/BC-LOCK-001",
            headers=_hdr(admin.id, lab_with_completed_order["lab"].id),
            json={"status": "rejected", "rejection_reason": "x"},
        )
        # assert_not_locked raises 423; route may also surface 409
        assert res.status_code in (409, 423)


# ─── Phase 3.C — State-machine non-regression ────────────────────────────────


class TestStateMachineRegressions:
    """The state machine is the single source of truth (domain/order_state.py).
    Verify the documented invariants survive future refactors."""

    def test_pending_can_transition_to_completed(self):
        from app.domain.order_state import can_transition
        assert can_transition("pending", "completed") is True

    def test_completed_can_transition_to_validated(self):
        from app.domain.order_state import can_transition
        assert can_transition("completed", "validated") is True

    def test_validated_is_terminal(self):
        from app.domain.order_state import can_transition
        for target in ("pending", "completed", "cancelled"):
            assert can_transition("validated", target) is False, (
                f"validated must be terminal; transition to {target} should be denied"
            )

    def test_cancelled_is_terminal(self):
        from app.domain.order_state import can_transition
        for target in ("pending", "completed", "validated"):
            assert can_transition("cancelled", target) is False

    def test_skip_completed_step_is_blocked(self):
        """Skipping completed → validated for a still-pending order is
        a privilege escalation if allowed."""
        from app.domain.order_state import can_transition
        assert can_transition("pending", "validated") is False


# ─── Phase 3.D — Optimistic-lock invariant on LabResult ──────────────────────


class TestLabResultOptimisticLockInvariant:
    """CLAUDE.md security invariant #6 says LabResult mutations must check
    ``version``. The column exists today but no route currently increments
    or compares it. These tests pin the column's existence as a non-regression
    so that:

      * a future migration that drops the column trips the test
      * any future PR adding mutation routes has a clear hook to enforce
        the invariant against
    """

    def test_lab_result_has_version_column(self):
        """The LabResult ORM must expose a ``version`` column (int, default 1)."""
        cols = {c.name: c for c in LabResult.__table__.columns}
        assert "version" in cols, (
            "LabResult.version is documented in CLAUDE.md as the optimistic "
            "lock token. Removing it breaks the documented security invariant."
        )
        version_col = cols["version"]
        # default value at column level
        default = version_col.default.arg if version_col.default else None
        assert default == 1
        assert version_col.nullable is False

    def test_lab_order_has_version_column(self):
        """LabOrder also documents a ``version`` column for optimistic locking."""
        cols = {c.name: c for c in LabOrder.__table__.columns}
        assert "version" in cols
        assert cols["version"].nullable is False

    def test_new_result_starts_at_version_one(self, db):
        """Newly created results start at version=1, ready for CAS."""
        lab = Lab(name="V Lab", license_number="LIC-V",
                  lab_type="private", city="Baghdad")
        db.add(lab); db.flush()
        patient = Patient(lab_id=lab.id, full_name="P", phone="07700111111",
                          health_id="HID-V-1")
        db.add(patient); db.flush()
        order = LabOrder(lab_id=lab.id, patient_id=patient.id, status="pending")
        db.add(order); db.flush()
        result = LabResult(order_id=order.id, test_name="X", value=1.0)
        db.add(result); db.commit()
        db.refresh(result)
        assert result.version == 1


# ─── Phase 3.E — Audit history correctness under repeated calls ──────────────


class TestAuditHistoryConcurrency:
    """Repeated mutations must each produce one (and only one) audit row.
    A buggy retry that double-logs would inflate the chain."""

    def test_two_distinct_mutations_produce_two_audits(self, client, db, lab_with_completed_order):
        from app.models.audit_log import AuditLog
        admin = lab_with_completed_order["admin1"]
        patient = lab_with_completed_order["patient"]

        before = db.query(AuditLog).count()
        client.put(
            f"/patients/{patient.id}",
            headers=_hdr(admin.id, lab_with_completed_order["lab"].id),
            json={"city": "Mosul"},
        )
        client.put(
            f"/patients/{patient.id}",
            headers=_hdr(admin.id, lab_with_completed_order["lab"].id),
            json={"city": "Erbil"},
        )
        after = db.query(AuditLog).count()
        assert after - before == 2

    def test_failed_validation_does_not_leak_audit(self, client, db, lab_with_completed_order):
        """A 409'd validation attempt should NOT write an audit entry — the
        audit log records facts, not failed attempts. (If this changes,
        update both the test and the security report's ledger semantics.)"""
        from app.models.audit_log import AuditLog
        admin1 = lab_with_completed_order["admin1"]
        admin2 = lab_with_completed_order["admin2"]
        order = lab_with_completed_order["order"]

        client.post(
            f"/orders/{order.id}/validate",
            headers=_hdr(admin1.id, lab_with_completed_order["lab"].id),
        )
        before = db.query(AuditLog).count()

        # Second call must 409 and NOT add an audit row
        res = client.post(
            f"/orders/{order.id}/validate",
            headers=_hdr(admin2.id, lab_with_completed_order["lab"].id),
        )
        assert res.status_code == 409
        after = db.query(AuditLog).count()
        assert after == before, (
            "A rejected validation attempt produced an audit row — "
            "audit log should record successful actions only."
        )


# ─── Phase 3.F — cancel_order compare-and-swap (Laboratory vertical slice) ───


class TestOrderCancelRace:
    """cancel_order (services/order_service.py) must refuse a stale cancel
    the same way validate_order already refuses a stale validate: via an
    atomic ``UPDATE ... WHERE locked_at IS NULL``, not just the sequential
    enforce_transition check.

    The race is reproduced deterministically (single process, real DB
    commits, no mocking of SQLAlchemy) by monkeypatching
    order_service.enforce_transition — the one call cancel_order makes
    between its initial read and its write — so that on its first
    invocation it drives a *real* concurrent validate_order through the
    actual HTTP route before returning. This is the same technique this
    module's own docstring endorses: a single-engine SQLite session cannot
    run two real OS threads against independent connections, so the
    interleaving is forced at the one point where cancel_order yields
    control, while every read and write still goes through real sessions
    and real commits.
    """

    def test_cancel_loses_race_to_concurrent_validate(
        self, client, db, lab_with_completed_order, monkeypatch,
    ):
        import app.services.order_service as order_service_module
        from app.domain.order_state import enforce_transition as real_enforce_transition

        admin1 = lab_with_completed_order["admin1"]
        admin2 = lab_with_completed_order["admin2"]
        order = lab_with_completed_order["order"]
        lab_id = lab_with_completed_order["lab"].id

        triggered = {"done": False}

        def racing_enforce_transition(current, target):
            if target == "cancelled" and not triggered["done"]:
                triggered["done"] = True
                # A concurrent request validates (and locks) the order
                # in the gap between cancel_order's read and its write.
                won = client.post(
                    f"/orders/{order.id}/validate",
                    headers=_hdr(admin2.id, lab_id),
                )
                assert won.status_code == 200, "setup: concurrent validate must win the race"
            return real_enforce_transition(current, target)

        monkeypatch.setattr(order_service_module, "enforce_transition", racing_enforce_transition)

        cancel_res = client.post(
            f"/orders/{order.id}/cancel",
            headers=_hdr(admin1.id, lab_id),
        )
        assert cancel_res.status_code == 409, (
            f"cancel_order must lose the race to the concurrent validate, got "
            f"{cancel_res.status_code}: {cancel_res.text}"
        )

        db.expire_all()
        order_db = db.query(LabOrder).filter(LabOrder.id == order.id).first()
        assert order_db.status == "validated", (
            "The validated order's status must not be overwritten by the "
            "losing cancel request — validated is documented as terminal."
        )
        assert order_db.locked_at is not None
        assert order_db.validated_by == admin2.id

    def test_uncontended_cancel_still_succeeds(self, client, db, lab_with_completed_order):
        """Non-regression: the CAS backstop must not block the ordinary,
        non-racing cancel path."""
        admin = lab_with_completed_order["admin1"]
        order = lab_with_completed_order["order"]
        lab_id = lab_with_completed_order["lab"].id

        res = client.post(f"/orders/{order.id}/cancel", headers=_hdr(admin.id, lab_id))
        assert res.status_code == 200

        db.expire_all()
        order_db = db.query(LabOrder).filter(LabOrder.id == order.id).first()
        assert order_db.status == "cancelled"


# ─── Phase 3.G — Sample authorization, state machine, and CAS ────────────────


class TestSampleAuthorizationAndStateMachine:
    """samples.py::update_sample previously had no role gate and no status
    state machine at all. Verify both are now enforced, and that the fix
    does not regress the ordinary authorized path."""

    def test_update_sample_requires_clinical_write_role(
        self, client, db, lab_with_completed_order,
    ):
        lab = lab_with_completed_order["lab"]
        order = lab_with_completed_order["order"]
        sample = Sample(order_id=order.id, sample_type="blood",
                        barcode="BC-ROLE-001", status="collected")
        db.add(sample)
        db.commit()

        staff_user = LabUser(
            lab_id=lab.id, name="Staff", email="staff@con.com",
            password_hash=hash_password("Pa55word"), role="staff", is_active=True,
        )
        db.add(staff_user)
        db.commit()

        res = client.put(
            "/samples/BC-ROLE-001",
            headers=_hdr(staff_user.id, lab.id, role="staff"),
            json={"status": "rejected", "rejection_reason": "x"},
        )
        assert res.status_code == 403

        db.expire_all()
        sample_db = db.query(Sample).filter(Sample.barcode == "BC-ROLE-001").first()
        assert sample_db.status == "collected", "denied update must not mutate the sample"

    def test_update_sample_allowed_for_technician(self, client, db, lab_with_completed_order):
        lab = lab_with_completed_order["lab"]
        order = lab_with_completed_order["order"]
        sample = Sample(order_id=order.id, sample_type="blood",
                        barcode="BC-ROLE-002", status="collected")
        db.add(sample)
        db.commit()

        tech = LabUser(
            lab_id=lab.id, name="Tech", email="tech@con.com",
            password_hash=hash_password("Pa55word"), role="technician", is_active=True,
        )
        db.add(tech)
        db.commit()

        res = client.put(
            "/samples/BC-ROLE-002",
            headers=_hdr(tech.id, lab.id, role="technician"),
            json={"status": "received"},
        )
        assert res.status_code == 200
        assert res.json()["sample"]["status"] == "received"

    def test_rejected_sample_cannot_be_resurrected(self, client, db, lab_with_completed_order):
        lab = lab_with_completed_order["lab"]
        order = lab_with_completed_order["order"]
        sample = Sample(order_id=order.id, sample_type="blood",
                        barcode="BC-STATE-001", status="rejected",
                        rejection_reason="hemolyzed")
        db.add(sample)
        db.commit()

        admin = lab_with_completed_order["admin1"]
        res = client.put(
            "/samples/BC-STATE-001",
            headers=_hdr(admin.id, lab.id),
            json={"status": "processing"},
        )
        assert res.status_code == 409

        db.expire_all()
        sample_db = db.query(Sample).filter(Sample.barcode == "BC-STATE-001").first()
        assert sample_db.status == "rejected", "a terminal sample must not be resurrected"

    def test_analyzed_sample_cannot_be_resurrected(self, client, db, lab_with_completed_order):
        lab = lab_with_completed_order["lab"]
        order = lab_with_completed_order["order"]
        sample = Sample(order_id=order.id, sample_type="blood",
                        barcode="BC-STATE-002", status="analyzed")
        db.add(sample)
        db.commit()

        admin = lab_with_completed_order["admin1"]
        res = client.put(
            "/samples/BC-STATE-002",
            headers=_hdr(admin.id, lab.id),
            json={"status": "collected"},
        )
        assert res.status_code == 409

        db.expire_all()
        sample_db = db.query(Sample).filter(Sample.barcode == "BC-STATE-002").first()
        assert sample_db.status == "analyzed"

    def test_sample_update_loses_race_to_concurrent_validate(
        self, client, db, lab_with_completed_order, monkeypatch,
    ):
        """Same CAS-backstop proof as TestOrderCancelRace, for the sibling
        gap in samples.py::update_sample.

        The injection point matters: assert_not_locked(order) takes the ORM
        object itself, and this test harness shares one SQLAlchemy session
        across "concurrent" requests, so a bulk update's
        synchronize_session="fetch" transparently refreshes that object —
        patching assert_not_locked would look like it reproduces the race
        but actually self-heals and proves nothing (verified: it passes
        unchanged against the pre-fix code too). enforce_sample_transition
        is called with sample.status already captured as a plain string
        argument, evaluated *before* this patched function's body runs, so
        it stays genuinely stale across the nested concurrent call — the
        same technique TestOrderCancelRace uses via enforce_transition.
        This isolates the one thing actually being proved: the atomic
        ``UPDATE ... WHERE locked_at IS NULL`` backstop, independent of
        whatever the sequential assert_not_locked check did or didn't
        catch.
        """
        import app.routes.samples as samples_module

        lab = lab_with_completed_order["lab"]
        order = lab_with_completed_order["order"]
        admin1 = lab_with_completed_order["admin1"]
        admin2 = lab_with_completed_order["admin2"]

        sample = Sample(order_id=order.id, sample_type="blood",
                        barcode="BC-RACE-001", status="collected")
        db.add(sample)
        db.commit()

        real_enforce_sample_transition = samples_module.enforce_sample_transition
        triggered = {"done": False}

        def racing_enforce_sample_transition(current, target):
            if not triggered["done"]:
                triggered["done"] = True
                # Concurrent validate wins the race in the gap between
                # update_sample's sequential assert_not_locked check (already
                # passed by this point) and its atomic write below.
                won = client.post(
                    f"/orders/{order.id}/validate",
                    headers=_hdr(admin2.id, lab.id),
                )
                assert won.status_code == 200, "setup: concurrent validate must win the race"
            return real_enforce_sample_transition(current, target)

        monkeypatch.setattr(
            samples_module, "enforce_sample_transition", racing_enforce_sample_transition,
        )

        res = client.put(
            "/samples/BC-RACE-001",
            headers=_hdr(admin1.id, lab.id),
            json={"status": "received"},
        )
        assert res.status_code == 423, (
            f"a sample update racing a concurrent order validation must be "
            f"refused, got {res.status_code}: {res.text}"
        )

        db.expire_all()
        sample_db = db.query(Sample).filter(Sample.barcode == "BC-RACE-001").first()
        assert sample_db.status == "collected", (
            "the losing sample update must not have been applied"
        )


# ─── Phase 3.H — Device result ingestion cannot silently duplicate ──────────


class TestDeviceIngestionIdempotence:
    """device_results.py::receive_device_results directly set
    `sample.status = "analyzed"`, bypassing domain/sample_state.py
    entirely — the one remaining site that mutated a sample's status
    without going through the same guard samples.py::update_sample now
    uses.

    Investigating this as a candidate duplicate-ingestion vulnerability,
    the negative-proof cycle below showed it was NOT independently
    exploitable: replaying a device submission against an order that
    already moved 'pending' -> 'completed' is already refused by the
    *order*-level domain/order_state.py guard (enforce_transition raises
    on 'completed' -> 'completed', since that is not a legal transition),
    regardless of the sample's own status. Both the pre-fix and post-fix
    code return 409 on the second call in test_second_ingestion_is_refused
    below — this test does not discriminate the two and is not a
    vulnerability proof.

    The change was kept anyway, recharacterized as consistency hardening
    rather than a vulnerability fix: routing this call site through
    enforce_sample_transition means the sample's own state machine is
    authoritative everywhere a sample's status is mutated, not just in
    the manual-update path — closing an inconsistent-enforcement pattern
    (one of the reusable classes this pass's Engineering Intelligence
    section calls out) rather than a live exploit.
    test_wiring_pin_enforce_sample_transition_is_called is the actual
    fix-discriminating test: source-inspection, matching the precedent
    already established for adaptive_auth's routing guards.
    """

    def test_second_ingestion_is_refused(self, client, db, lab_with_completed_order):
        """Non-regression: the endpoint still correctly refuses a replay,
        whichever guard is doing the refusing."""
        lab = lab_with_completed_order["lab"]
        admin = lab_with_completed_order["admin1"]
        patient = lab_with_completed_order["patient"]

        pending_order = LabOrder(lab_id=lab.id, patient_id=patient.id, status="pending")
        db.add(pending_order)
        db.flush()
        sample = Sample(order_id=pending_order.id, sample_type="blood",
                        barcode="BC-DEVICE-001", status="collected")
        db.add(sample)
        db.commit()
        order = pending_order

        payload = {
            "barcode": "BC-DEVICE-001",
            "device_id": "ANALYZER-1",
            "results": [{"test_name": "Sodium", "value": 140.0, "unit": "mmol/L"}],
        }

        from app.models.lab_result import LabResult

        first = client.post("/device/results", headers=_hdr(admin.id, lab.id), json=payload)
        assert first.status_code == 200

        count_after_first = db.query(LabResult).filter(LabResult.order_id == order.id).count()

        second = client.post("/device/results", headers=_hdr(admin.id, lab.id), json=payload)
        assert second.status_code == 409, (
            f"a replayed device submission must be refused, got "
            f"{second.status_code}: {second.text}"
        )

        count_after_second = db.query(LabResult).filter(LabResult.order_id == order.id).count()
        assert count_after_second == count_after_first, (
            "the refused replay must not create duplicate LabResult rows"
        )

    def test_wiring_pin_enforce_sample_transition_is_called(self):
        """Pins the actual fix: removing enforce_sample_transition from
        receive_device_results fails here by name, rather than silently
        reopening the inconsistent-enforcement gap. This is the test that
        actually discriminates pre-fix from post-fix code (the end-to-end
        test above does not — see class docstring)."""
        import inspect

        from app.routes import device_results

        source = inspect.getsource(device_results.receive_device_results)
        assert "enforce_sample_transition" in source, (
            "receive_device_results no longer routes its sample.status "
            "mutation through the canonical domain/sample_state.py guard"
        )
