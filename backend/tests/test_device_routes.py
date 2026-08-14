from __future__ import annotations

from tests.conftest import auth_headers


def _device_payload(uid: str, *, category: str = "laboratory_analyzer", protocol: str = "HL7v2_MLLP", transport: str = "MLLP"):
    return {
        "device_uid": uid,
        "display_name": f"Synthetic {uid}",
        "category": category,
        "vendor": "GULA Synthetic",
        "model": "SIM-1",
        "serial_number": f"S-{uid}",
        "protocol": protocol,
        "transport": transport,
        "endpoint": "sim://local-only",
        "capabilities": {"synthetic": True},
    }


def test_device_catalog_is_tenant_scoped_and_registers(client, make_lab, make_lab_user):
    lab_a = make_lab("Device Lab A")
    lab_b = make_lab("Device Lab B")
    user_a = make_lab_user(lab_a.id, role="admin")
    user_b = make_lab_user(lab_b.id, role="admin")
    headers_a = auth_headers(user_a.id, lab_a.id, "admin")
    headers_b = auth_headers(user_b.id, lab_b.id, "admin")

    response = client.post("/device-integration/devices", json=_device_payload("HL7-A-001"), headers=headers_a)
    assert response.status_code == 201
    assert response.json()["simulation_only"] is True
    assert response.json()["status"] == "pending"

    own_devices = client.get("/device-integration/devices", headers=headers_a)
    assert own_devices.status_code == 200
    assert own_devices.json()["total"] == 1
    assert own_devices.json()["devices"][0]["device_uid"] == "HL7-A-001"

    other_devices = client.get("/device-integration/devices", headers=headers_b)
    assert other_devices.status_code == 200
    assert other_devices.json()["total"] == 0

    summary = client.get("/device-integration/summary", headers=headers_a)
    assert summary.status_code == 200
    assert summary.json()["total"] == 1
    assert summary.json()["simulation_only"] == 1


def test_probe_events_and_printer_jobs_are_explicitly_simulated(client, make_lab, make_lab_user):
    lab = make_lab("Simulation Lab")
    user = make_lab_user(lab.id, role="lab_admin")
    headers = auth_headers(user.id, lab.id, "lab_admin")

    register = client.post(
        "/device-integration/devices",
        json=_device_payload("ZEBRA-001", category="printer", protocol="ZPL", transport="TCP"),
        headers=headers,
    )
    assert register.status_code == 201

    probe = client.post("/device-integration/devices/ZEBRA-001/probe", headers=headers)
    assert probe.status_code == 200
    assert probe.json()["status"] == "connected"
    assert probe.json()["last_seen_at"] is not None

    job = client.post(
        "/device-integration/printer-jobs",
        json={
            "device_uid": "ZEBRA-001",
            "document_type": "specimen_label",
            "printer_language": "ZPL",
            "label_count": 2,
            "template_key": "synthetic-label",
        },
        headers=headers,
    )
    assert job.status_code == 201
    assert job.json()["status"] == "simulated_success"
    assert job.json()["simulation_only"] is True

    events = client.get("/device-integration/events", headers=headers)
    assert events.status_code == 200
    assert events.json()["total"] >= 3
    assert all("raw_payload" not in event for event in events.json()["events"])
    assert any(event["event_type"] == "print_job_simulated" for event in events.json()["events"])

    jobs = client.get("/device-integration/printer-jobs", headers=headers)
    assert jobs.status_code == 200
    assert jobs.json()["total"] == 1
    assert jobs.json()["jobs"][0]["device_uid"] == "ZEBRA-001"


def test_lab_staff_can_read_but_cannot_mutate_device_catalog(client, make_lab, make_lab_user):
    lab = make_lab("Read Only Lab")
    user = make_lab_user(lab.id, role="lab_staff")
    headers = auth_headers(user.id, lab.id, "lab_staff")

    read = client.get("/device-integration/protocols", headers=headers)
    assert read.status_code == 200
    assert any(item["key"] == "ASTM" for item in read.json())

    write = client.post("/device-integration/devices", json=_device_payload("DENIED-001"), headers=headers)
    assert write.status_code == 403


def test_device_uid_duplicate_is_rejected(client, make_lab, make_lab_user):
    lab = make_lab("Duplicate Lab")
    user = make_lab_user(lab.id, role="admin")
    headers = auth_headers(user.id, lab.id, "admin")
    payload = _device_payload("DUPLICATE-001")

    assert client.post("/device-integration/devices", json=payload, headers=headers).status_code == 201
    duplicate = client.post("/device-integration/devices", json=payload, headers=headers)
    assert duplicate.status_code == 400
    assert "already exists" in duplicate.json()["detail"]
