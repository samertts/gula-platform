from datetime import UTC, datetime

from app.models.patient import Patient

from tests.conftest import auth_headers


def _patient(db, lab_id: int, name: str = "Wearable Patient") -> Patient:
    patient = Patient(lab_id=lab_id, full_name=name, phone="0770000011")
    db.add(patient)
    db.flush()
    return patient


def _payload(patient_id: int, event_id: str = "evt-001") -> dict:
    return {
        "patient_id": patient_id,
        "source": "synthetic-wearable",
        "metric_code": "heart_rate",
        "value": 72.0,
        "unit": "bpm",
        "measured_at": datetime.now(UTC).isoformat(),
        "source_event_id": event_id,
        "quality_score": 0.98,
        "quality_status": "good",
        "provenance": {"adapter": "synthetic", "schema_version": "1"},
        "simulation_only": True,
    }


def test_wearable_measurement_is_tenant_scoped_and_idempotent(client, db, make_lab, make_lab_user):
    lab = make_lab("Wearable Lab")
    other_lab = make_lab("Other Wearable Lab")
    user = make_lab_user(lab.id, role="admin")
    other_user = make_lab_user(other_lab.id, role="admin")
    patient = _patient(db, lab.id)
    other_patient = _patient(db, other_lab.id, "Other Patient")
    headers = auth_headers(user.id, lab.id, role="admin")

    first = client.post(
        "/device-integration/wearables/measurements",
        json=_payload(patient.id),
        headers=headers,
    )
    assert first.status_code == 201, first.text
    assert first.json()["duplicate"] is False

    second = client.post(
        "/device-integration/wearables/measurements",
        json=_payload(patient.id),
        headers=headers,
    )
    assert second.status_code == 201, second.text
    assert second.json()["duplicate"] is True
    assert second.json()["measurement"]["id"] == first.json()["measurement"]["id"]

    wrong_tenant = client.post(
        "/device-integration/wearables/measurements",
        json=_payload(other_patient.id, "evt-other"),
        headers=headers,
    )
    assert wrong_tenant.status_code == 404

    listed = client.get(
        f"/device-integration/wearables/measurements?patient_id={patient.id}",
        headers=headers,
    )
    assert listed.status_code == 200, listed.text
    assert listed.json()["total"] == 1

    other_listed = client.get(
        f"/device-integration/wearables/measurements?patient_id={patient.id}",
        headers=auth_headers(other_user.id, other_lab.id, role="admin"),
    )
    assert other_listed.status_code == 200
    assert other_listed.json()["total"] == 0


def test_wearable_measurement_rejects_invalid_unit_and_live_mode(client, db, make_lab, make_lab_user):
    lab = make_lab("Wearable Validation Lab")
    user = make_lab_user(lab.id, role="admin")
    patient = _patient(db, lab.id)
    headers = auth_headers(user.id, lab.id, role="admin")

    invalid_unit = _payload(patient.id, "evt-invalid")
    invalid_unit["unit"] = "mmHg"
    response = client.post(
        "/device-integration/wearables/measurements",
        json=invalid_unit,
        headers=headers,
    )
    assert response.status_code == 400

    live = _payload(patient.id, "evt-live")
    live["simulation_only"] = False
    response = client.post(
        "/device-integration/wearables/measurements",
        json=live,
        headers=headers,
    )
    assert response.status_code == 400


def test_wearable_measurement_rejects_non_finite_values(client, db, make_lab, make_lab_user):
    lab = make_lab("Wearable Finite Value Lab")
    user = make_lab_user(lab.id, role="admin")
    patient = _patient(db, lab.id)
    headers = auth_headers(user.id, lab.id, role="admin")

    for index, non_finite in enumerate(("NaN", "Infinity", "-Infinity"), start=1):
        payload = _payload(patient.id, f"evt-non-finite-{index}")
        payload["value"] = non_finite
        response = client.post(
            "/device-integration/wearables/measurements",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 422


def test_signed_wearable_webhook_is_verified_and_idempotent(client, db, make_lab, monkeypatch):
    import hashlib
    import hmac
    import json
    import time

    lab = make_lab("Webhook Lab")
    patient = _patient(db, lab.id, "Webhook Patient")
    secret = "webhook-test-secret"
    monkeypatch.setenv("GULA_WEARABLE_WEBHOOK_SECRET_FITBIT", secret)
    measurement = _payload(patient.id, "fitbit-event-001")
    measurement["source"] = "fitbit"
    envelope = {"lab_id": lab.id, "measurement": measurement}
    raw = json.dumps(envelope, separators=(",", ":")).encode("utf-8")
    timestamp = str(int(time.time()))
    signature = hmac.new(secret.encode(), f"{timestamp}.".encode() + raw, hashlib.sha256).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Timestamp": timestamp,
        "X-Signature-256": f"sha256={signature}",
    }

    first = client.post(
        "/device-integration/wearables/webhook/fitbit",
        content=raw,
        headers=headers,
    )
    assert first.status_code == 202, first.text
    assert first.json()["duplicate"] is False
    assert first.json()["simulation_only"] is True

    second = client.post(
        "/device-integration/wearables/webhook/fitbit",
        content=raw,
        headers=headers,
    )
    assert second.status_code == 202, second.text
    assert second.json()["duplicate"] is True
    assert second.json()["measurement_id"] == first.json()["measurement_id"]


def test_signed_wearable_webhook_rejects_invalid_signature(client, db, make_lab, monkeypatch):
    import json
    import time

    lab = make_lab("Invalid Webhook Lab")
    patient = _patient(db, lab.id, "Invalid Signature Patient")
    monkeypatch.setenv("GULA_WEARABLE_WEBHOOK_SECRET_FITBIT", "correct-secret")
    envelope = {"lab_id": lab.id, "measurement": {**_payload(patient.id), "source": "fitbit"}}
    raw = json.dumps(envelope, separators=(",", ":")).encode("utf-8")
    response = client.post(
        "/device-integration/wearables/webhook/fitbit",
        content=raw,
        headers={"X-Webhook-Timestamp": str(int(time.time())), "X-Signature-256": "sha256=invalid"},
    )
    assert response.status_code == 401
    assert "Invalid webhook signature" in response.text


def test_signed_wearable_webhook_rejects_live_mode(client, db, make_lab, monkeypatch):
    import hashlib
    import hmac
    import json
    import time

    lab = make_lab("Live Provider Lab")
    patient = _patient(db, lab.id, "Live Provider Patient")
    secret = "provider-secret"
    monkeypatch.setenv("GULA_WEARABLE_WEBHOOK_SECRET_FITBIT", secret)
    envelope = {"lab_id": lab.id, "measurement": {**_payload(patient.id, "live-event"), "source": "fitbit", "simulation_only": False}}
    raw = json.dumps(envelope, separators=(",", ":")).encode("utf-8")
    timestamp = str(int(time.time()))
    signature = hmac.new(secret.encode(), f"{timestamp}.".encode() + raw, hashlib.sha256).hexdigest()
    response = client.post(
        "/device-integration/wearables/webhook/fitbit",
        content=raw,
        headers={"X-Webhook-Timestamp": timestamp, "X-Signature-256": f"sha256={signature}"},
    )
    assert response.status_code == 409
    assert "clinical approval" in response.text


def test_signed_wearable_webhook_rejects_expired_timestamp(client, db, make_lab, monkeypatch):
    import hashlib
    import hmac
    import json
    import time

    lab = make_lab("Expired Webhook Lab")
    patient = _patient(db, lab.id, "Expired Patient")
    secret = "expired-secret"
    monkeypatch.setenv("GULA_WEARABLE_WEBHOOK_SECRET_FITBIT", secret)
    envelope = {"lab_id": lab.id, "measurement": {**_payload(patient.id, "expired-event"), "source": "fitbit"}}
    raw = json.dumps(envelope, separators=(",", ":")).encode("utf-8")
    timestamp = str(int(time.time()) - 301)
    signature = hmac.new(secret.encode(), f"{timestamp}.".encode() + raw, hashlib.sha256).hexdigest()
    response = client.post(
        "/device-integration/wearables/webhook/fitbit",
        content=raw,
        headers={"X-Webhook-Timestamp": timestamp, "X-Signature-256": f"sha256={signature}"},
    )
    assert response.status_code == 401
    assert "Expired webhook signature" in response.text


def test_wearable_baseline_summary_is_advisory_and_tenant_scoped(client, db, make_lab, make_lab_user):
    lab = make_lab("Baseline Lab")
    other_lab = make_lab("Other Baseline Lab")
    user = make_lab_user(lab.id, role="admin")
    other_user = make_lab_user(other_lab.id, role="admin")
    patient = _patient(db, lab.id, "Baseline Patient")
    headers = auth_headers(user.id, lab.id, role="admin")
    for index in range(7):
        payload = _payload(patient.id, f"baseline-{index}")
        payload["measured_at"] = datetime(2026, 8, 1 + index, tzinfo=UTC).isoformat()
        payload["value"] = 70 + index
        accepted = client.post("/device-integration/wearables/measurements", json=payload, headers=headers)
        assert accepted.status_code == 201, accepted.text

    response = client.get(
        f"/device-integration/wearables/baseline-summary?patient_id={patient.id}&metric_code=heart_rate",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["evaluation"]["advisory_only"] is True
    assert response.json()["patient_id"] == patient.id

    other_response = client.get(
        f"/device-integration/wearables/baseline-summary?patient_id={patient.id}&metric_code=heart_rate",
        headers=auth_headers(other_user.id, other_lab.id, role="admin"),
    )
    assert other_response.status_code == 404
