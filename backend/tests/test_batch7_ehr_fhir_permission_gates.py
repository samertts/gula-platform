"""Batch 7 regression: ehr_fhir.py Observation/Provenance permission gates.

fhir_read_observation, fhir_search_observation, and fhir_search_provenance
project the legacy LabResult/LabOrder/AuditLog canonical resources (already
permission-gated elsewhere in the codebase via results:read/audit:read) but
previously depended only on Depends(get_current_user) -- no permission check.
Confirmed via git-stash negative proof: reverting the route file reproduces
a 200 for every case below; with the fix applied, each returns 403.
"""

from tests.conftest import auth_headers


def _order_with_result(db, make_lab, make_lab_user):
    from app.models.lab_order import LabOrder
    from app.models.lab_result import LabResult
    from app.models.patient import Patient

    lab = make_lab()
    admin = make_lab_user(lab_id=lab.id, role="admin")
    patient = Patient(
        lab_id=lab.id,
        full_name="Test Patient",
        phone="07701234567",
        health_id="HID-BATCH7-1",
    )
    db.add(patient)
    db.flush()
    order = LabOrder(patient_id=patient.id, lab_id=lab.id, status="completed")
    db.add(order)
    db.flush()
    result = LabResult(order_id=order.id, test_name="Glucose", value=95, unit="mg/dL")
    db.add(result)
    db.flush()
    return lab, admin, order, result


class TestFhirObservationPermissionGate:
    def test_read_without_results_read_is_forbidden(self, client, db, make_lab, make_lab_user):
        lab, _admin, _order, result = _order_with_result(db, make_lab, make_lab_user)
        db.commit()
        cashier = make_lab_user(lab_id=lab.id, role="cashier")
        db.commit()

        resp = client.get(
            f"/fhir/Observation/{result.id}",
            headers=auth_headers(cashier.id, lab.id, "cashier"),
        )
        assert resp.status_code == 403

    def test_read_with_results_read_is_allowed(self, client, db, make_lab, make_lab_user):
        lab, _admin, _order, result = _order_with_result(db, make_lab, make_lab_user)
        db.commit()
        doctor = make_lab_user(lab_id=lab.id, role="doctor")
        db.commit()

        resp = client.get(
            f"/fhir/Observation/{result.id}",
            headers=auth_headers(doctor.id, lab.id, "doctor"),
        )
        assert resp.status_code == 200

    def test_search_without_results_read_is_forbidden(self, client, db, make_lab, make_lab_user):
        lab, _admin, _order, _result = _order_with_result(db, make_lab, make_lab_user)
        db.commit()
        finance = make_lab_user(lab_id=lab.id, role="finance_auditor")
        db.commit()

        resp = client.get(
            "/fhir/Observation",
            headers=auth_headers(finance.id, lab.id, "finance_auditor"),
        )
        assert resp.status_code == 403


class TestFhirProvenancePermissionGate:
    def test_search_without_audit_read_is_forbidden(self, client, db, make_lab, make_lab_user):
        lab, _admin, order, _result = _order_with_result(db, make_lab, make_lab_user)
        db.commit()
        technician = make_lab_user(lab_id=lab.id, role="technician")
        db.commit()

        resp = client.get(
            f"/fhir/Provenance?target=LabOrder/{order.id}",
            headers=auth_headers(technician.id, lab.id, "technician"),
        )
        assert resp.status_code == 403

    def test_search_with_audit_read_is_allowed(self, client, db, make_lab, make_lab_user):
        lab, admin, order, _result = _order_with_result(db, make_lab, make_lab_user)
        db.commit()

        resp = client.get(
            f"/fhir/Provenance?target=LabOrder/{order.id}",
            headers=auth_headers(admin.id, lab.id, "admin"),
        )
        assert resp.status_code == 200
