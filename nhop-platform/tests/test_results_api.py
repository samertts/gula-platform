"""Tests for the test-results API (``/v1/test-results``).

This surface previously had zero test coverage even though it carries lab
values, critical-alert notifications, and the citizen timeline used by the
doctor overview. These tests lock in the documented behavior (see the
module docstring in ``app/api/v1/test_results.py``).

Every call sends admin_headers (X-Role: ADMIN) — these routes now require
one of LAB/DOCTOR/ADMIN(/MINISTRY for reads).
"""
from __future__ import annotations


def test_validate_payload_only_checks_plausibility(app_client, admin_headers):
    client, _ = app_client

    resp = client.post(
        "/v1/test-results/validate",
        json={"test_code": "hgb", "test_name": "Hemoglobin", "value_numeric": 14.0},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_valid"] is True
    assert body["is_critical"] is False


def test_create_result_requires_a_role(app_client, make_lab):
    """No identifying header at all -> 503 (no trusted caller identity can be
    established), not a silent pass-through. See app/core/trusted_context.py:
    a missing identity fails closed, it is never treated as anonymous/401."""
    client, Session = app_client
    with Session() as s:
        lab = make_lab(s)
        lab_id = str(lab.id)

    resp = client.post(
        "/v1/test-results/",
        json={
            "health_id": "HID-MISSING",
            "lab_id": lab_id,
            "test_code": "HGB",
            "test_name": "Hemoglobin",
            "value_numeric": 14.0,
        },
    )
    assert resp.status_code == 503


def test_create_result_rejects_doctor_role(app_client, make_lab):
    """Only LAB/ADMIN may create results — DOCTOR orders/verifies, doesn't
    author them. Note core.rbac.require_roles reads X-Role, a distinct
    header/scheme from doctor.py's own X-Actor-Role."""
    client, Session = app_client
    with Session() as s:
        lab = make_lab(s)
        lab_id = str(lab.id)

    resp = client.post(
        "/v1/test-results/",
        json={
            "health_id": "HID-MISSING",
            "lab_id": lab_id,
            "test_code": "HGB",
            "test_name": "Hemoglobin",
            "value_numeric": 14.0,
        },
        headers={"X-Role": "DOCTOR"},
    )
    assert resp.status_code == 403


def test_create_result_requires_known_citizen(app_client, make_lab, admin_headers):
    client, Session = app_client
    with Session() as s:
        lab = make_lab(s)
        lab_id = str(lab.id)

    resp = client.post(
        "/v1/test-results/",
        json={
            "health_id": "HID-MISSING",
            "lab_id": lab_id,
            "test_code": "HGB",
            "test_name": "Hemoglobin",
            "value_numeric": 14.0,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 404


def test_create_result_requires_active_lab(app_client, make_citizen, make_lab, admin_headers):
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(s, health_id="HID-R1")
        lab = make_lab(s, is_active=False)
        citizen_hid = citizen.health_id
        lab_id = str(lab.id)

    resp = client.post(
        "/v1/test-results/",
        json={
            "health_id": citizen_hid,
            "lab_id": lab_id,
            "test_code": "HGB",
            "test_name": "Hemoglobin",
            "value_numeric": 14.0,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 400


def test_create_result_success_and_read_back(app_client, make_citizen, make_lab, admin_headers):
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(s, health_id="HID-R2")
        lab = make_lab(s)
        citizen_hid = citizen.health_id
        lab_id = str(lab.id)

    resp = client.post(
        "/v1/test-results/",
        json={
            "health_id": citizen_hid,
            "lab_id": lab_id,
            "test_code": "hgb",
            "test_name": "Hemoglobin",
            "value_numeric": 14.0,
            "unit": "g/dL",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["test_code"] == "HGB"  # normalized upper-case
    assert body["sample_barcode"]

    get_resp = client.get(f"/v1/test-results/{body['id']}", headers=admin_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == body["id"]


def test_create_result_rejects_implausible_value(app_client, make_citizen, make_lab, admin_headers):
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(s, health_id="HID-R3")
        lab = make_lab(s)
        citizen_hid = citizen.health_id
        lab_id = str(lab.id)

    resp = client.post(
        "/v1/test-results/",
        json={
            "health_id": citizen_hid,
            "lab_id": lab_id,
            "test_code": "HGB",
            "test_name": "Hemoglobin",
            "value_numeric": -999.0,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"] == "implausible_value"


def test_get_unknown_result_is_404(app_client, admin_headers):
    import uuid

    client, _ = app_client
    resp = client.get(f"/v1/test-results/{uuid.uuid4()}", headers=admin_headers)
    assert resp.status_code == 404


def test_verify_result_transitions_status_once(
    app_client, make_citizen, make_lab, make_result
):
    """verified_by is server-derived from the trusted context (the actor id),
    not a client-supplied field — the body carries nothing."""
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(s, health_id="HID-R4")
        lab = make_lab(s)
        row = make_result(s, citizen_id=citizen.id, lab_id=lab.id)
        result_id = str(row.id)

    verifier_headers = {"X-Role": "ADMIN", "X-Actor-Id": "dr-001"}
    resp = client.put(
        f"/v1/test-results/{result_id}/verify",
        json={},
        headers=verifier_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "verified"
    assert body["verified_by"] == "dr-001"

    again = client.put(
        f"/v1/test-results/{result_id}/verify",
        json={},
        headers={"X-Role": "ADMIN", "X-Actor-Id": "dr-002"},
    )
    assert again.status_code == 409


def test_list_citizen_results_filters_by_abnormal(
    app_client, make_citizen, make_lab, make_result, admin_headers
):
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(s, health_id="HID-R5")
        lab = make_lab(s)
        make_result(s, citizen_id=citizen.id, lab_id=lab.id, test_code="HGB", is_abnormal=False)
        make_result(s, citizen_id=citizen.id, lab_id=lab.id, test_code="GLU", is_abnormal=True)
        citizen_hid = citizen.health_id

    resp = client.get(
        f"/v1/test-results/citizen/{citizen_hid}",
        params={"is_abnormal": True},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["test_code"] == "GLU"


def test_citizen_timeline_groups_by_test_code(
    app_client, make_citizen, make_lab, make_result, admin_headers
):
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(s, health_id="HID-R6")
        lab = make_lab(s)
        from datetime import datetime, timedelta as _td

        from backend.app._compat import UTC

        for idx, days_ago in enumerate([20, 10, 1]):
            make_result(
                s, citizen_id=citizen.id, lab_id=lab.id,
                test_code="HBA1C", test_name="HbA1c",
                value_numeric=6.0 + idx,
                performed_at=datetime.now(UTC) - _td(days=days_ago),
            )
        citizen_hid = citizen.health_id

    resp = client.get(
        f"/v1/test-results/citizen/{citizen_hid}/timeline", headers=admin_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["health_id"] == citizen_hid
    assert len(body["series"]) == 1
    assert body["series"][0]["test_code"] == "HBA1C"
    assert len(body["series"][0]["points"]) == 3
