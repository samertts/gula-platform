"""Tests for the doctor-portal endpoints (CMD-017)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone


def test_order_tests_requires_doctor_role(app_client, make_citizen):
    client, Session = app_client
    with Session() as s:
        make_citizen(s, health_id="HID-1")

    resp = client.post(
        "/v1/doctor/order-tests",
        json={
            "citizen_health_id": "HID-1",
            "tests": ["CBC"],
            "clinical_indication": "routine",
        },
    )
    assert resp.status_code == 403

    resp = client.post(
        "/v1/doctor/order-tests",
        json={
            "citizen_health_id": "HID-1",
            "tests": ["CBC"],
            "clinical_indication": "routine",
        },
        headers={"X-Actor-Role": "DOCTOR"},  # missing actor id
    )
    assert resp.status_code == 401


def test_order_tests_smart_suggestions_and_dispatch(
    app_client, make_citizen, make_lab, doctor_headers
):
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(s, health_id="HID-2")
        lab = make_lab(s)
        citizen_hid = citizen.health_id
        lab_id = str(lab.id)

    resp = client.post(
        "/v1/doctor/order-tests",
        json={
            "citizen_health_id": citizen_hid,
            "tests": ["CBC"],
            "clinical_indication": "اشتباه سكري",
            "preferred_lab_id": lab_id,
            "urgent": True,
        },
        headers=doctor_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "dispatched"
    assert body["urgent"] is True
    assert body["lab_id"] == lab_id
    assert "HBA1C" in body["tests"]
    assert "GLU" in body["tests"]
    assert "HBA1C" in body["suggested_additions"]
    assert body["duplicates_skipped"] == []


def test_order_tests_skips_tests_performed_in_last_7_days(
    app_client, make_citizen, make_lab, make_result, doctor_headers
):
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(s, health_id="HID-3")
        lab = make_lab(s)
        make_result(
            s,
            citizen_id=citizen.id,
            lab_id=lab.id,
            test_code="HGB",
            performed_at=datetime.now(UTC) - timedelta(days=2),
        )
        citizen_hid = citizen.health_id

    resp = client.post(
        "/v1/doctor/order-tests",
        json={
            "citizen_health_id": citizen_hid,
            "tests": ["HGB", "WBC"],
            "clinical_indication": "follow-up",
        },
        headers=doctor_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["tests"] == ["WBC"]
    codes_skipped = [d["test_code"] for d in body["duplicates_skipped"]]
    assert codes_skipped == ["HGB"]


def test_order_tests_all_duplicate_returns_409(
    app_client, make_citizen, make_lab, make_result, doctor_headers
):
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(s, health_id="HID-4")
        lab = make_lab(s)
        make_result(
            s,
            citizen_id=citizen.id,
            lab_id=lab.id,
            test_code="HGB",
            performed_at=datetime.now(UTC) - timedelta(days=1),
        )
        citizen_hid = citizen.health_id

    resp = client.post(
        "/v1/doctor/order-tests",
        json={
            "citizen_health_id": citizen_hid,
            "tests": ["HGB"],
            "clinical_indication": "follow-up",
        },
        headers=doctor_headers,
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"] == "all_tests_duplicate_within_7_days"


def test_order_tests_includes_test_older_than_7_days(
    app_client, make_citizen, make_lab, make_result, doctor_headers
):
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(s, health_id="HID-5")
        lab = make_lab(s)
        make_result(
            s,
            citizen_id=citizen.id,
            lab_id=lab.id,
            test_code="HGB",
            performed_at=datetime.now(UTC) - timedelta(days=15),
        )
        citizen_hid = citizen.health_id

    resp = client.post(
        "/v1/doctor/order-tests",
        json={
            "citizen_health_id": citizen_hid,
            "tests": ["HGB"],
            "clinical_indication": "follow-up",
        },
        headers=doctor_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["tests"] == ["HGB"]
    assert body["duplicates_skipped"] == []
    assert body["status"] == "pending"  # no preferred lab


def test_patient_overview_returns_summary_with_alerts(
    app_client, make_citizen, make_lab, make_result, doctor_headers
):
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(
            s,
            health_id="HID-6",
            full_name="علي محمد",
            chronic_diseases=["سكري"],
        )
        lab = make_lab(s)
        make_result(
            s, citizen_id=citizen.id, lab_id=lab.id,
            test_code="HGB", value_numeric=6.5, is_abnormal=True, is_critical=True,
            interpretation_ar="الهيموغلوبين منخفض",
        )
        make_result(
            s, citizen_id=citizen.id, lab_id=lab.id,
            test_code="GLU", value_numeric=180.0, is_abnormal=True, is_critical=False,
        )
        citizen_hid = citizen.health_id

    resp = client.get(
        f"/v1/doctor/patient/{citizen_hid}/overview",
        headers=doctor_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["citizen"]["full_name"] == "علي محمد"
    assert body["citizen"]["chronic_diseases"] == ["سكري"]
    assert len(body["recent_results"]) == 2
    severities = {a["severity"] for a in body["active_alerts"]}
    assert "critical" in severities
    assert 0 <= body["health_score"] <= 100
    # Penalties: 1 critical (12) + 1 abnormal (4) + 1 chronic (3) = 19
    assert body["health_score"] == 81


def test_patient_timeline_returns_ordered_points(
    app_client, make_citizen, make_lab, make_result, doctor_headers
):
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(s, health_id="HID-7")
        lab = make_lab(s)
        for idx, days in enumerate([30, 10, 1]):
            make_result(
                s, citizen_id=citizen.id, lab_id=lab.id,
                test_code="HBA1C", test_name="HbA1c",
                value_numeric=6.0 + idx, unit="%",
                performed_at=datetime.now(UTC) - timedelta(days=days),
            )
        citizen_hid = citizen.health_id

    resp = client.get(
        f"/v1/doctor/patient/{citizen_hid}/timeline/hba1c",
        headers=doctor_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["test_code"] == "HBA1C"
    values = [p["value_numeric"] for p in body["points"]]
    assert values == [6.0, 7.0, 8.0]


def test_refer_rejects_self_referral(
    app_client, make_citizen, doctor_headers
):
    client, Session = app_client
    with Session() as s:
        make_citizen(s, health_id="HID-8")

    resp = client.post(
        "/v1/doctor/refer",
        json={
            "citizen_health_id": "HID-8",
            "to_doctor_id": doctor_headers["X-Actor-Id"],
            "reason": "second opinion",
        },
        headers=doctor_headers,
    )
    assert resp.status_code == 400


def test_refer_returns_summary(
    app_client, make_citizen, make_lab, make_result, doctor_headers
):
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(
            s, health_id="HID-9",
            full_name="زينب حسين",
            chronic_diseases=["ضغط"],
            allergies=["بنسلين"],
        )
        lab = make_lab(s)
        make_result(
            s, citizen_id=citizen.id, lab_id=lab.id,
            test_code="HGB", value_numeric=11.0,
        )
        citizen_hid = citizen.health_id

    resp = client.post(
        "/v1/doctor/refer",
        json={
            "citizen_health_id": citizen_hid,
            "to_doctor_id": "dr-specialist",
            "reason": "cardiology consult",
            "include_recent_results": 3,
        },
        headers=doctor_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["from_doctor_id"] == doctor_headers["X-Actor-Id"]
    assert body["to_doctor_id"] == "dr-specialist"
    assert body["summary"]["citizen"]["chronic_diseases"] == ["ضغط"]
    assert body["summary"]["citizen"]["allergies"] == ["بنسلين"]
    assert len(body["summary"]["recent_results"]) == 1


def test_patient_overview_unknown_citizen_is_404(app_client, doctor_headers):
    client, _ = app_client
    resp = client.get(
        "/v1/doctor/patient/HID-MISSING/overview",
        headers=doctor_headers,
    )
    assert resp.status_code == 404
