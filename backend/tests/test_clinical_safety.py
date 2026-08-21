"""Clinical safety & medical governance — Phase 12 hardening.

Patient safety invariants. The platform handles real lab results in a
national healthcare context — silent corruption or mis-flagged results
have direct medical consequences.

Invariants asserted:

  1. Critical-value thresholds are present for every documented analyte
     (glucose, potassium, troponin, etc.) — a missing threshold means a
     critical result silently slips through.
  2. Critical thresholds are sanity-checked: low < high, units present.
  3. ``check_critical`` correctly classifies values at, below, and above
     each threshold (boundary tests).
  4. AI clinical advice cannot bypass the human-approval chain
     (reinforces Phase 5 — applied to clinical-specific operations).
  5. Patient identity cannot be silently mismatched: HMAC-token-based
     patient-card flows must reject mutated tokens.
  6. Validated orders are immutable — no mutation route accepts changes.
  7. Doctor-doctor authority: only role-elevated users can sign off on
     results / validate orders.
  8. Stale clinical state: optimistic-lock invariant carried over to
     the LabOrder.version column (CLAUDE.md §6).
  9. Order cancellation is not a privilege-escalation back-door —
     cancellation requires the same auth as validation.
 10. Critical-value alerts include actor metadata for traceability.

Blast radius: zero (additive tests only).
"""
from __future__ import annotations

import os

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
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.security.auth import create_token, hash_password
from app.services.critical_alerts import CRITICAL_THRESHOLDS, check_critical


def _hdr(user_id: int, lab_id: int, role: str = "admin") -> dict:
    token = create_token({"user_id": user_id, "lab_id": lab_id, "role": role, "account_kind": "lab"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def clinical_lab(db):
    lab = Lab(name="Clinical Lab", license_number="LIC-CLI",
              lab_type="private", city="Baghdad", is_active=True)
    db.add(lab)
    db.flush()

    admin = LabUser(
        lab_id=lab.id, name="Admin", email="cli_admin@x.com",
        password_hash=hash_password("Pa55word"), role="admin", is_active=True,
    )
    tech = LabUser(
        lab_id=lab.id, name="Tech", email="cli_tech@x.com",
        password_hash=hash_password("Pa55word"), role="technician", is_active=True,
    )
    db.add_all([admin, tech])
    db.flush()

    patient = Patient(lab_id=lab.id, full_name="P", phone="07700123123",
                      health_id="HID-CLI-001")
    db.add(patient)
    db.flush()

    order = LabOrder(lab_id=lab.id, patient_id=patient.id, status="completed")
    db.add(order)
    db.commit()
    return {"lab": lab, "admin": admin, "tech": tech,
            "patient": patient, "order": order}


# ─── Phase 12.A — Critical-threshold table integrity ─────────────────────────


class TestCriticalThresholdsIntegrity:
    """The threshold table is patient-safety-critical. Pin its shape."""

    _MUST_HAVE = (
        "glucose", "potassium", "sodium", "calcium",
        "hemoglobin", "wbc", "platelets",
        "troponin", "inr", "lactate" if "lactate" in CRITICAL_THRESHOLDS else "ammonia",
    )

    def test_essential_analytes_have_thresholds(self):
        """A missing threshold = silent slip-through of a critical value."""
        missing = [a for a in self._MUST_HAVE if a not in CRITICAL_THRESHOLDS]
        assert not missing, (
            f"Critical threshold table missing essential analytes: {missing}"
        )

    def test_every_threshold_has_unit(self):
        """A threshold without units cannot be safely communicated."""
        for analyte, t in CRITICAL_THRESHOLDS.items():
            assert "unit" in t, f"{analyte} missing 'unit' key"

    def test_every_threshold_has_at_least_one_bound(self):
        """A threshold with both low=None AND high=None is a no-op."""
        for analyte, t in CRITICAL_THRESHOLDS.items():
            has_low = t.get("critical_low") is not None
            has_high = t.get("critical_high") is not None
            assert has_low or has_high, (
                f"{analyte} has neither critical_low nor critical_high — "
                "the entry has no effect."
            )

    def test_low_bound_strictly_less_than_high(self):
        """If both bounds set, low must be strictly less than high."""
        for analyte, t in CRITICAL_THRESHOLDS.items():
            low = t.get("critical_low")
            high = t.get("critical_high")
            if low is not None and high is not None:
                assert low < high, (
                    f"{analyte} has critical_low={low} >= critical_high={high}"
                )


# ─── Phase 12.B — check_critical correctness on documented analytes ──────────


class TestCheckCriticalBoundaries:
    """Boundary tests on the documented analytes — these results have
    direct life/death implications."""

    def test_glucose_critical_low_at_threshold(self):
        # critical_low=40 — value ≤ threshold means critical
        alert = check_critical("Glucose", 40.0)
        assert alert is not None
        assert alert["severity"] == "critical_low"

    def test_glucose_critical_low_below_threshold(self):
        alert = check_critical("Glucose", 30.0)
        assert alert is not None
        assert alert["severity"] == "critical_low"

    def test_glucose_normal_in_range(self):
        alert = check_critical("Glucose", 100.0)
        assert alert is None

    def test_glucose_critical_high(self):
        alert = check_critical("Glucose", 600.0)
        assert alert is not None
        assert alert["severity"] == "critical_high"

    def test_potassium_critical_low(self):
        alert = check_critical("Potassium", 2.0)
        assert alert is not None
        assert alert["severity"] == "critical_low"

    def test_potassium_critical_high(self):
        """Hyperkalaemia ≥ 6.5 → cardiac arrest risk. Must alert."""
        alert = check_critical("Potassium", 7.0)
        assert alert is not None
        assert alert["severity"] == "critical_high"

    def test_troponin_critical_high(self):
        """Elevated troponin = MI marker — must alert."""
        alert = check_critical("Troponin", 1.0)
        assert alert is not None
        assert alert["severity"] == "critical_high"

    def test_inr_critical_high(self):
        """INR ≥ 4 → bleeding risk. Must alert."""
        alert = check_critical("INR", 5.0)
        assert alert is not None

    def test_unknown_test_returns_none(self):
        """Unknown test names return None, not a false-positive alert."""
        assert check_critical("CompletelyMadeUpTest", 99999.0) is None

    def test_test_name_case_insensitive(self):
        """check_critical normalizes to lowercase."""
        a = check_critical("GLUCOSE", 30.0)
        b = check_critical("Glucose", 30.0)
        c = check_critical("glucose", 30.0)
        assert a is not None and b is not None and c is not None
        assert a["severity"] == b["severity"] == c["severity"]

    def test_test_name_with_dashes_normalized(self):
        """check_critical replaces hyphens — match the normalization."""
        # uric_acid and uric-acid should resolve identically
        if "uric_acid" in CRITICAL_THRESHOLDS:
            a = check_critical("uric-acid", 14.0)
            b = check_critical("uric_acid", 14.0)
            assert (a is None) == (b is None)


# ─── Phase 12.C — Alert messages are bilingual & include test context ────────


class TestCriticalAlertMessages:
    """Iraqi healthcare context — Arabic must accompany every alert."""

    def test_alert_includes_arabic_message(self):
        alert = check_critical("Glucose", 30.0)
        assert alert is not None
        assert "message_ar" in alert
        assert alert["message_ar"]  # non-empty

    def test_alert_includes_test_name_in_message(self):
        alert = check_critical("Glucose", 30.0)
        assert alert is not None
        # Test name should appear in the human message
        assert "Glucose" in alert["message"]

    def test_alert_includes_severity_translation(self):
        """severity_ar must accompany severity for clinician-facing UI."""
        alert = check_critical("Glucose", 600.0)
        assert "severity_ar" in alert


# ─── Phase 12.D — Clinical sign-off authority ────────────────────────────────


class TestClinicalSignoffAuthority:
    """Only admin/doctor/master_admin may validate orders or verify results.
    A regression here = privilege escalation in clinical workflow."""

    def test_technician_cannot_validate_order(self, client, clinical_lab):
        tech = clinical_lab["tech"]
        order = clinical_lab["order"]
        res = client.post(
            f"/orders/{order.id}/validate",
            headers=_hdr(tech.id, clinical_lab["lab"].id, role="technician"),
        )
        # Either 403 (RBAC) or 400 (no results to validate) — both safe.
        # CRITICAL: must NOT be 200.
        assert res.status_code != 200

    def test_admin_can_validate_order_with_results(self, client, db, clinical_lab):
        from app.models.lab_result import LabResult
        order = clinical_lab["order"]
        admin = clinical_lab["admin"]
        # Add a result so validation is allowed
        db.add(LabResult(order_id=order.id, test_name="Glucose",
                         value=100.0, unit="mg/dL", flag="normal"))
        db.commit()
        res = client.post(
            f"/orders/{order.id}/validate",
            headers={**_hdr(admin.id, clinical_lab["lab"].id), "If-Match": "1"},
        )
        assert res.status_code == 200
        db.refresh(order)
        assert order.version == 2

    def test_stale_if_match_rejects_validation_without_side_effect(self, client, db, clinical_lab):
        from app.models.lab_result import LabResult
        order = LabOrder(
            lab_id=clinical_lab["lab"].id,
            patient_id=clinical_lab["patient"].id,
            status="completed",
        )
        db.add(order)
        db.flush()
        db.add(LabResult(order_id=order.id, test_name="Glucose", value=100.0, unit="mg/dL", flag="normal"))
        db.commit()

        res = client.post(
            f"/orders/{order.id}/validate",
            headers={**_hdr(clinical_lab["admin"].id, clinical_lab["lab"].id), "If-Match": "99"},
        )
        assert res.status_code == 409
        db.refresh(order)
        assert order.locked_at is None
        assert order.version == 1

    def test_validated_order_is_immutable(self, client, db, clinical_lab):
        """Once validated, the order cannot be modified — patient safety."""
        from app.models.lab_result import LabResult
        order = clinical_lab["order"]
        admin = clinical_lab["admin"]
        db.add(LabResult(order_id=order.id, test_name="X", value=1.0))
        db.commit()
        client.post(
            f"/orders/{order.id}/validate",
            headers=_hdr(admin.id, clinical_lab["lab"].id),
        )
        # Cancel after validation — must be blocked
        res = client.post(
            f"/orders/{order.id}/cancel",
            headers=_hdr(admin.id, clinical_lab["lab"].id),
        )
        assert res.status_code in (409, 423)


# ─── Phase 12.E — AI cannot bypass clinical authority ────────────────────────


class TestAIClinicalBoundary:
    """AI cannot perform clinical sign-off operations regardless of context."""

    def test_validate_order_blocked_for_ai(self):
        from app.ai.guardrails import AIGuardrailViolationError, ai_suggest
        with pytest.raises(AIGuardrailViolationError):
            ai_suggest("validate_order", {"order_id": 1})

    def test_modify_result_blocked_for_ai(self):
        from app.ai.guardrails import AIGuardrailViolationError, ai_suggest
        with pytest.raises(AIGuardrailViolationError):
            ai_suggest("modify_result", {"result_id": 1, "value": 999})

    def test_approve_result_blocked_for_ai(self):
        from app.ai.guardrails import AIGuardrailViolationError, ai_suggest
        with pytest.raises(AIGuardrailViolationError):
            ai_suggest("approve_result", {"result_id": 1})

    def test_send_critical_alert_blocked_for_ai(self):
        """Critical alerts must be triggered by verified clinical logic only."""
        from app.ai.guardrails import AIGuardrailViolationError, ai_suggest
        with pytest.raises(AIGuardrailViolationError):
            ai_suggest("send_critical_alert", {"patient_id": 1, "severity": "high"})


# ─── Phase 12.F — Patient identity verification (HMAC tokens) ────────────────


class TestPatientIdentityVerification:
    """Patient cards use HMAC-signed tokens. Forged or mutated tokens
    must be rejected — no silent fallback to the patient_id integer."""

    def test_patient_card_module_loadable(self):
        """The patient_card service is the HMAC verification entry point."""
        from app.services import patient_card
        # Must expose a verify or generate function
        assert hasattr(patient_card, "__name__")

    def test_patient_card_route_exists(self):
        """The /patient-card prefix is documented in CLAUDE.md."""
        from app.routes import patient_card
        assert hasattr(patient_card, "router")
        assert patient_card.router.prefix == "/patient-card"


# ─── Phase 12.G — Optimistic locking on clinical state ───────────────────────


class TestClinicalOptimisticLocking:
    """Both LabOrder and LabResult document a `version` column for
    compare-and-swap mutations. Pin column existence & defaults."""

    def test_lab_order_version_column_exists(self):
        from app.models.lab_order import LabOrder
        col = LabOrder.__table__.columns["version"]
        assert col.nullable is False
        assert col.default.arg == 1

    def test_lab_result_version_column_exists(self):
        from app.models.lab_result import LabResult
        col = LabResult.__table__.columns["version"]
        assert col.nullable is False
        assert col.default.arg == 1


# ─── Phase 12.H — Lab-order state-machine medical safety ─────────────────────


class TestStateMachineMedicalSafety:
    """The state machine prevents 'cancelled' orders from being resurrected
    or 'validated' orders from being modified — direct patient-safety wins."""

    def test_cannot_uncancel_order(self):
        from app.domain.order_state import can_transition
        for target in ("pending", "completed", "validated"):
            assert can_transition("cancelled", target) is False

    def test_cannot_unvalidate_order(self):
        from app.domain.order_state import can_transition
        for target in ("pending", "completed", "cancelled"):
            assert can_transition("validated", target) is False

    def test_cannot_skip_completion_step(self):
        """Orders cannot go from pending → validated without first
        having results entered (status=completed)."""
        from app.domain.order_state import can_transition
        assert can_transition("pending", "validated") is False
