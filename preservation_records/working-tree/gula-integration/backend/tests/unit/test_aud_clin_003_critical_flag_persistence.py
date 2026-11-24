"""AUD-CLIN-003 — manual auto-validate must PERSIST critical/abnormal flags.

The auditor found the auto-validate route committed only when
``auto_validated`` was true. A critical value is never auto-validated (workflow
skips auto-validation when flags exist), so the response carried
``critical_high`` while ``Result.is_critical`` stayed False. The downstream
``process_critical_result`` then returned "skipped" — silently dropping a
critical-result escalation.

Falsification axes:
1. After the route, the response reports critical_high (workflow still detects).
2. The persisted Result has is_critical / is_abnormal / flag / validation_status.
3. process_critical_result now reaches "notification_pending" (not "skipped").
4. Normal (non-critical) results are not spuriously marked critical.
"""
from __future__ import annotations

import pytest
from app.lims import models as lims_models
from app.lims.workflows import process_critical_result
from app.models.lab_order import LabOrder
from app.models.patient import Patient

RESULT_PATH = "/lims/workflows/auto-validate"


def _make_result(db, make_lab, *, value):
    lab = make_lab("Critical Flag Lab")
    patient = Patient(lab_id=lab.id, full_name="Synthetic Flag Patient", phone="07700000002")
    db.add(patient)
    db.flush()
    order = LabOrder(patient_id=patient.id, lab_id=lab.id, status="pending")
    db.add(order)
    db.flush()
    lims_order = lims_models.Order(order_id=order.id, lab_id=lab.id, accession_number="ACC-FLAG-001")
    db.add(lims_order)
    db.flush()
    specimen = lims_models.Specimen(
        lab_id=lab.id, order_id=order.id, barcode="SP-FLAG-001", specimen_type="blood",
    )
    db.add(specimen)
    db.flush()
    db.add(
        lims_models.ReferenceRangeDef(
            test_code="K", lab_id=lab.id, ref_range_low=3.5, ref_range_high=5.0,
            critical_high=6.5, is_active=True,
        )
    )
    result = lims_models.Result(
        lab_id=lab.id, specimen_id=specimen.id, order_id=order.id,
        test_code="K", test_name="Potassium", value_numeric=value, unit="mmol/L",
    )
    db.add(result)
    db.commit()
    return lab, result


class TestCriticalFlagPersistence:
    def test_critical_flag_is_persisted_and_alert_no_longer_skipped(
        self, client, db, make_lab, make_lab_user,
    ):
        lab, result = _make_result(db, make_lab, value=7.2)
        user = make_lab_user(lab.id, role="technician")
        token = client.post("/login", json={"email": user.email, "password": "Testpass1"}).json()["access_token"]

        resp = client.post(
            RESULT_PATH, params={"result_id": result.id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "critical_high" in body["flags"], body
        assert body["auto_validated"] is False, "critical value must not be auto-validated"

        db.expire_all()
        persisted = db.query(lims_models.Result).filter(lims_models.Result.id == result.id).one()
        assert persisted.is_critical is True, "critical flag was not persisted"
        assert persisted.is_abnormal is True, "abnormal flag was not persisted"
        assert persisted.flag is not None
        assert persisted.validation_status in ("flagged", "auto_validated")

        # The downstream escalation must now proceed instead of being skipped.
        outcome = process_critical_result(db, result.id, lab.id, user_id=user.id)
        assert outcome["status"] == "notification_pending", outcome

    def test_normal_result_not_spuriously_critical(self, client, db, make_lab, make_lab_user):
        lab, result = _make_result(db, make_lab, value=4.0)  # inside reference range
        user = make_lab_user(lab.id, role="technician")
        token = client.post("/login", json={"email": user.email, "password": "Testpass1"}).json()["access_token"]

        resp = client.post(
            RESULT_PATH, params={"result_id": result.id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        db.expire_all()
        persisted = db.query(lims_models.Result).filter(lims_models.Result.id == result.id).one()
        assert persisted.is_critical is False
        outcome = process_critical_result(db, result.id, lab.id, user_id=user.id)
        assert outcome["status"] == "skipped"

    def test_route_persists_flags_not_only_auto_validated(self):
        """Static guard: the route must persist flags outside the auto_validated branch."""
        import inspect

        from app.lims.routes import run_auto_validation

        src = inspect.getsource(run_auto_validation)
        assert "is_critical" in src
        assert "is_abnormal" in src
        assert 'validation["flags"]' in src

    def test_revalidation_clears_stale_critical_flags(self, client, db, make_lab, make_lab_user):
        """R-CLIN-003-A (Team C): a corrected value must clear stale critical flags.

        Re-running the manual workflow after an out-of-band critical→normal
        value correction recomputed flags=[] but left is_critical/is_abnormal/
        flag set, producing a false notification_pending downstream.
        """
        lab, result = _make_result(db, make_lab, value=7.2)  # critical-high
        user = make_lab_user(lab.id, role="technician")
        token = client.post("/login", json={"email": user.email, "password": "Testpass1"}).json()["access_token"]
        header = {"Authorization": f"Bearer {token}"}

        resp = client.post(RESULT_PATH, params={"result_id": result.id}, headers=header)
        assert resp.status_code == 200
        assert "critical_high" in resp.json()["flags"]
        db.expire_all()
        assert db.query(lims_models.Result).filter(lims_models.Result.id == result.id).one().is_critical is True

        # Out-of-band correction to a normal value, then re-validation.
        db.query(lims_models.Result).filter(lims_models.Result.id == result.id).update(
            {lims_models.Result.value_numeric: 4.0}
        )
        db.commit()
        resp = client.post(RESULT_PATH, params={"result_id": result.id}, headers=header)
        assert resp.status_code == 200
        assert resp.json()["flags"] == []

        db.expire_all()
        persisted = db.query(lims_models.Result).filter(lims_models.Result.id == result.id).one()
        assert persisted.is_critical is False, "stale critical flag survived re-validation"
        assert persisted.is_abnormal is False, "stale abnormal flag survived re-validation"
        assert persisted.flag is None, "stale flag string survived re-validation"
        outcome = process_critical_result(db, result.id, lab.id, user_id=user.id)
        assert outcome["status"] == "skipped", outcome
