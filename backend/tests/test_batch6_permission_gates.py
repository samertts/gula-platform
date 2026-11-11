"""Batch 6 regression: identity/patients/test_results/compliance permission gates.

Each of these routes previously depended only on ``get_current_user`` (proves
authentication) with no ``require_permission`` check (proves authorization).
A role that authenticates successfully but lacks the relevant RBAC permission
could read or write patient/result data outside its intended scope. Confirmed
via git-stash negative proof: reverting these route files reproduces a 200/201
for every case below; with the fix applied, each returns 403.
"""

from tests.conftest import auth_headers


def _patient(db, make_lab, make_lab_user):
    from app.models.patient import Patient

    lab = make_lab()
    user = make_lab_user(lab_id=lab.id, role="admin")
    patient = Patient(
        lab_id=lab.id,
        full_name="Test Patient",
        phone="07701234567",
        health_id="HID-BATCH6-1",
    )
    db.add(patient)
    db.flush()
    return lab, user, patient


class TestIdentityLinkPermissionGate:
    def test_role_without_patients_write_is_forbidden(self, client, db, make_lab, make_lab_user):
        lab, _admin, patient = _patient(db, make_lab, make_lab_user)
        db.commit()
        technician = make_lab_user(lab_id=lab.id, role="technician")
        db.commit()

        resp = client.post(
            "/identity/link",
            json={"patient_id": patient.id, "national_id": "123456789012"},
            headers=auth_headers(technician.id, lab.id, "technician"),
        )
        assert resp.status_code == 403

    def test_role_with_patients_write_is_allowed(self, client, db, make_lab, make_lab_user):
        lab, admin, patient = _patient(db, make_lab, make_lab_user)
        db.commit()

        resp = client.post(
            "/identity/link",
            json={"patient_id": patient.id, "national_id": "123456789013"},
            headers=auth_headers(admin.id, lab.id, "admin"),
        )
        assert resp.status_code == 200


class TestPatientsRoutesPermissionGate:
    def test_list_without_patients_read_is_forbidden(self, client, db, make_lab, make_lab_user):
        lab, _admin, _pt = _patient(db, make_lab, make_lab_user)
        db.commit()
        cashier = make_lab_user(lab_id=lab.id, role="cashier")
        db.commit()

        resp = client.get("/patients", headers=auth_headers(cashier.id, lab.id, "cashier"))
        assert resp.status_code == 403

    def test_create_without_patients_write_is_forbidden(self, client, db, make_lab, make_lab_user):
        lab, _admin, _pt = _patient(db, make_lab, make_lab_user)
        db.commit()
        finance = make_lab_user(lab_id=lab.id, role="finance_auditor")
        db.commit()

        resp = client.post(
            "/patients",
            json={"full_name": "New Patient", "phone": "07701234599"},
            headers=auth_headers(finance.id, lab.id, "finance_auditor"),
        )
        assert resp.status_code == 403

    def test_get_single_without_patients_read_is_forbidden(
        self, client, db, make_lab, make_lab_user,
    ):
        lab, _admin, patient = _patient(db, make_lab, make_lab_user)
        db.commit()
        reconciler = make_lab_user(lab_id=lab.id, role="reconciler")
        db.commit()

        resp = client.get(
            f"/patients/{patient.id}",
            headers=auth_headers(reconciler.id, lab.id, "reconciler"),
        )
        assert resp.status_code == 403

    def test_update_without_patients_write_is_forbidden(self, client, db, make_lab, make_lab_user):
        lab, _admin, patient = _patient(db, make_lab, make_lab_user)
        db.commit()
        doctor = make_lab_user(lab_id=lab.id, role="doctor")
        db.commit()

        resp = client.put(
            f"/patients/{patient.id}",
            json={"full_name": "Renamed"},
            headers=auth_headers(doctor.id, lab.id, "doctor"),
        )
        assert resp.status_code == 403

    def test_admin_role_still_allowed(self, client, db, make_lab, make_lab_user):
        lab, admin, _pt = _patient(db, make_lab, make_lab_user)
        db.commit()

        resp = client.get("/patients", headers=auth_headers(admin.id, lab.id, "admin"))
        assert resp.status_code == 200


class TestResultsWritePermissionGate:
    def test_create_test_result_without_results_write_is_forbidden(
        self, client, db, make_lab, make_lab_user,
    ):
        lab, _admin, patient = _patient(db, make_lab, make_lab_user)
        db.commit()
        cashier = make_lab_user(lab_id=lab.id, role="cashier")
        db.commit()

        resp = client.post(
            "/test-results/",
            json={"health_id": patient.health_id, "test_name": "Glucose", "value": 90},
            headers=auth_headers(cashier.id, lab.id, "cashier"),
        )
        assert resp.status_code == 403


class TestComplianceFhirPermissionGate:
    def test_fhir_patient_without_patients_read_is_forbidden(
        self, client, db, make_lab, make_lab_user,
    ):
        lab, _admin, patient = _patient(db, make_lab, make_lab_user)
        db.commit()
        citizen = make_lab_user(lab_id=lab.id, role="citizen")
        db.commit()

        resp = client.get(
            f"/compliance/fhir/patient/{patient.id}",
            headers=auth_headers(citizen.id, lab.id, "citizen"),
        )
        assert resp.status_code == 403

    def test_fhir_patient_with_patients_read_is_allowed(
        self, client, db, make_lab, make_lab_user,
    ):
        lab, _admin, patient = _patient(db, make_lab, make_lab_user)
        db.commit()
        doctor = make_lab_user(lab_id=lab.id, role="doctor")
        db.commit()

        resp = client.get(
            f"/compliance/fhir/patient/{patient.id}",
            headers=auth_headers(doctor.id, lab.id, "doctor"),
        )
        assert resp.status_code == 200
