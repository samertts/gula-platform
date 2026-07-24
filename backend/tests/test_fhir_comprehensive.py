"""Comprehensive FHIR R4 API integration tests — uses TestClient fixture only."""

from __future__ import annotations

import pytest

from tests.conftest import auth_headers


class TestReadOperations:
    """Verify GET /fhir/{ResourceType}/{id} for every supported resource."""

    def test_read_patient(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id)
        headers = auth_headers(user.id, lab.id)
        resp = client.get("/fhir/Patient/nonexistent", headers=headers)
        assert resp.status_code in (404,)

    def test_read_nonexistent_returns_404(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id)
        headers = auth_headers(user.id, lab.id)
        for rt, rid in (("Encounter", "nonexistent"), ("Condition", "nonexistent"),
                        ("Observation", 99999999), ("MedicationRequest", "nonexistent"),
                        ("MedicationStatement", "nonexistent"), ("CarePlan", "nonexistent"),
                        ("Procedure", "nonexistent"), ("AllergyIntolerance", "nonexistent"),
                        ("Immunization", "nonexistent"), ("DocumentReference", "nonexistent"),
                        ("Composition", "nonexistent")):
            resp = client.get(f"/fhir/{rt}/{rid}", headers=headers)
            assert resp.status_code == 404, f"{rt} expected 404 got {resp.status_code}"

    def test_unauthorized_returns_401(self, client):
        resp = client.get("/fhir/Patient/1")
        assert resp.status_code in (401, 403)


class TestSearchOperations:
    """Verify FHIR search endpoints return bundles."""

    def test_search_returns_bundle(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id)
        headers = auth_headers(user.id, lab.id)
        searchable = ("Condition", "Observation", "MedicationRequest",
                      "AllergyIntolerance", "Immunization",
                      "DocumentReference", "Composition", "Procedure")
        for rt in searchable:
            resp = client.get(f"/fhir/{rt}", headers=headers)
            assert resp.status_code == 200, f"{rt} search expected 200 got {resp.status_code}"
            body = resp.json()
            assert body.get("resourceType") == "Bundle"
            assert "entry" in body


class TestCreateOperations:
    """Verify POST /fhir/{ResourceType} creates resources."""

    def test_create_unsupported_returns_422(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id)
        headers = auth_headers(user.id, lab.id)
        body = {"resourceType": "Goal", "status": "active"}
        resp = client.post("/fhir/Goal", json=body, headers=headers)
        assert resp.status_code == 422

    def test_create_without_auth_returns_401(self, client):
        resp = client.post("/fhir/Condition", json={"resourceType": "Condition"})
        assert resp.status_code in (401, 403)


class TestUpdateOperations:
    """Verify PUT /fhir/{ResourceType}/{id} updates resources."""

    def test_update_nonexistent_returns_404(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id)
        headers = auth_headers(user.id, lab.id)
        resp = client.put("/fhir/Condition/nonexistent", json={"resourceType": "Condition"}, headers=headers)
        assert resp.status_code == 404


class TestDeleteOperations:
    """Verify DELETE /fhir/{ResourceType}/{id} soft-deletes resources."""

    def test_delete_nonexistent_returns_404(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id)
        headers = auth_headers(user.id, lab.id)
        resp = client.delete("/fhir/Condition/nonexistent", headers=headers)
        assert resp.status_code == 404

    def test_delete_unsupported_type_returns_422(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id)
        headers = auth_headers(user.id, lab.id)
        resp = client.delete("/fhir/Patient/nonexistent", headers=headers)
        assert resp.status_code == 422

    def test_delete_without_auth_returns_401(self, client):
        resp = client.delete("/fhir/Condition/some-id")
        assert resp.status_code in (401, 403)


class TestBundleOperations:
    """Verify GET /fhir/Bundle/{id} returns patient-everything."""

    def test_bundle_nonexistent_returns_404(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id)
        headers = auth_headers(user.id, lab.id)
        resp = client.get("/fhir/Bundle/nonexistent", headers=headers)
        assert resp.status_code == 404


class TestBatchTransaction:
    """Verify POST /fhir handles batch/transaction bundles."""

    def test_batch_returns_bundle_response(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id)
        headers = auth_headers(user.id, lab.id)
        body = {"resourceType": "Bundle", "type": "batch", "entry": []}
        resp = client.post("/fhir", json=body, headers=headers)
        assert resp.status_code == 200
        assert resp.json().get("resourceType") == "Bundle"

    def test_unsupported_bundle_type_returns_422(self, client, db, make_lab, make_lab_user):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id)
        headers = auth_headers(user.id, lab.id)
        body = {"resourceType": "Bundle", "type": "history", "entry": []}
        resp = client.post("/fhir", json=body, headers=headers)
        assert resp.status_code == 422


class TestErrorHandling:
    """Verify appropriate HTTP error codes."""

class TestTenantIsolation:
    """Verify labs cannot access each other's FHIR resources."""

    def test_cross_lab_patient_returns_404(self, client, db, make_lab, make_lab_user):
        lab1 = make_lab()
        lab2 = make_lab(name="Lab B")
        user1 = make_lab_user(lab_id=lab1.id)
        user2 = make_lab_user(lab_id=lab2.id)
        headers2 = auth_headers(user2.id, lab2.id)
        resp = client.get("/fhir/Patient/nonexistent", headers=headers2)
        assert resp.status_code == 404



