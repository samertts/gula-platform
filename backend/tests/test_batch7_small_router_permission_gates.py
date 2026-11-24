"""Batch 7 regression: device_results/critical_alerts/batch permission gates.

Same systemic shape found repeatedly across this program: a mutation or a
PII-bearing read depended only on Depends(get_current_user) (proves
authentication, not authorization) with no require_permission(...) check,
while tenant isolation was already correct. Confirmed via git-stash negative
proof: reverting the route files reproduces a 200/201 for every case below;
with the fix applied, each returns 403.
"""

from tests.conftest import auth_headers


def _lab_with_patient(db, make_lab, make_lab_user):
    from app.models.patient import Patient

    lab = make_lab()
    admin = make_lab_user(lab_id=lab.id, role="admin")
    patient = Patient(
        lab_id=lab.id,
        full_name="Test Patient",
        phone="07701234567",
        health_id="HID-BATCH7-2",
    )
    db.add(patient)
    db.flush()
    return lab, admin, patient


class TestDeviceResultsPermissionGate:
    def test_submit_without_results_write_is_forbidden(self, client, db, make_lab, make_lab_user):
        lab, _admin, _patient = _lab_with_patient(db, make_lab, make_lab_user)
        db.commit()
        citizen = make_lab_user(lab_id=lab.id, role="citizen")
        db.commit()

        resp = client.post(
            "/device/results",
            json={"barcode": "NOPE", "results": [{"test_name": "Glucose", "value": 90}]},
            headers=auth_headers(citizen.id, lab.id, "citizen"),
        )
        assert resp.status_code == 403

    def test_submit_with_results_write_reaches_business_logic(
        self, client, db, make_lab, make_lab_user,
    ):
        lab, admin, _patient = _lab_with_patient(db, make_lab, make_lab_user)
        db.commit()

        resp = client.post(
            "/device/results",
            json={"barcode": "NOPE", "results": [{"test_name": "Glucose", "value": 90}]},
            headers=auth_headers(admin.id, lab.id, "admin"),
        )
        # Permission gate passed; 404 is the expected business-logic outcome
        # for a barcode that doesn't exist (proves the gate isn't just always-403).
        assert resp.status_code == 404


class TestCriticalAlertsPermissionGate:
    def test_alerts_without_results_read_is_forbidden(self, client, db, make_lab, make_lab_user):
        lab, _admin, _patient = _lab_with_patient(db, make_lab, make_lab_user)
        db.commit()
        cashier = make_lab_user(lab_id=lab.id, role="cashier")
        db.commit()

        resp = client.get("/alerts", headers=auth_headers(cashier.id, lab.id, "cashier"))
        assert resp.status_code == 403

    def test_alerts_with_results_read_is_allowed(self, client, db, make_lab, make_lab_user):
        lab, _admin, _patient = _lab_with_patient(db, make_lab, make_lab_user)
        db.commit()
        doctor = make_lab_user(lab_id=lab.id, role="doctor")
        db.commit()

        resp = client.get("/alerts", headers=auth_headers(doctor.id, lab.id, "doctor"))
        assert resp.status_code == 200

    def test_stats_without_results_read_is_forbidden(self, client, db, make_lab, make_lab_user):
        lab, _admin, _patient = _lab_with_patient(db, make_lab, make_lab_user)
        db.commit()
        reconciler = make_lab_user(lab_id=lab.id, role="reconciler")
        db.commit()

        resp = client.get("/alerts/stats", headers=auth_headers(reconciler.id, lab.id, "reconciler"))
        assert resp.status_code == 403


class TestBatchOrdersPermissionGate:
    def test_create_without_orders_write_is_forbidden(self, client, db, make_lab, make_lab_user):
        lab, _admin, patient = _lab_with_patient(db, make_lab, make_lab_user)
        db.commit()
        finance = make_lab_user(lab_id=lab.id, role="finance_operator")
        db.commit()

        resp = client.post(
            "/batch/orders",
            json={"orders": [{"patient_id": patient.id, "results": []}]},
            headers=auth_headers(finance.id, lab.id, "finance_operator"),
        )
        assert resp.status_code == 403

    def test_create_with_orders_write_is_allowed(self, client, db, make_lab, make_lab_user):
        lab, admin, patient = _lab_with_patient(db, make_lab, make_lab_user)
        db.commit()

        resp = client.post(
            "/batch/orders",
            json={"orders": [{"patient_id": patient.id, "results": []}]},
            headers=auth_headers(admin.id, lab.id, "admin"),
        )
        assert resp.status_code == 201
