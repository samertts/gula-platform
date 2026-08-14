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


def _connector_payload(uid: str, *, device_uid: str = "HL7-A-001", protocol: str = "HL7v2_MLLP", transport: str = "MLLP"):
    return {
        "connector_uid": uid,
        "display_name": f"Synthetic Connector {uid}",
        "device_uid": device_uid,
        "protocol": protocol,
        "transport": transport,
        "mode": "gateway_pending",
        "contract_version": "v1",
        "config_safe": {"ack_strategy": "simulated_ack", "timeout_seconds": 30},
        "capability_manifest": {"message_types": ["ORU^R01", "ACK"]},
    }


def test_connector_registry_and_profiles_are_lab_scoped(client, make_lab, make_lab_user):
    lab_a = make_lab("Adapter Lab A")
    lab_b = make_lab("Adapter Lab B")
    user_a = make_lab_user(lab_a.id, role="admin")
    user_b = make_lab_user(lab_b.id, role="admin")
    headers_a = auth_headers(user_a.id, lab_a.id, "admin")
    headers_b = auth_headers(user_b.id, lab_b.id, "admin")

    device = client.post("/device-integration/devices", json=_device_payload("HL7-A-001"), headers=headers_a)
    assert device.status_code == 201

    connector = client.post("/device-integration/connectors", json=_connector_payload("CONN-HL7-A-001"), headers=headers_a)
    assert connector.status_code == 201
    assert connector.json()["mode"] == "gateway_pending"
    assert connector.json()["simulation_only"] is True
    assert connector.json()["gateway_ref"].startswith("gateway://pending/")

    own_connectors = client.get("/device-integration/connectors", headers=headers_a)
    assert own_connectors.status_code == 200
    assert own_connectors.json()["total"] == 1
    assert own_connectors.json()["connectors"][0]["connector_uid"] == "CONN-HL7-A-001"

    other_connectors = client.get("/device-integration/connectors", headers=headers_b)
    assert other_connectors.status_code == 200
    assert other_connectors.json()["total"] == 0

    profile = client.post(
        "/device-integration/protocol-profiles",
        json={
            "profile_key": "hl7.oru.r01.v1",
            "protocol": "HL7v2_MLLP",
            "version": "v1",
            "message_type": "ORU^R01",
            "framing": "MLLP",
            "ack_strategy": "ACK/NAK",
            "simulator_key": "hl7v2.oru.r01",
            "status": "validated",
            "mapping_schema": {"value": "OBX-5"},
            "validation_rules": {"required_segments": ["MSH", "PID", "OBR", "OBX"]},
        },
        headers=headers_a,
    )
    assert profile.status_code == 201
    assert profile.json()["simulation_only"] is True


def test_connector_contract_rejects_secret_bearing_config(client, make_lab, make_lab_user):
    lab = make_lab("Secret Boundary Lab")
    user = make_lab_user(lab.id, role="admin")
    headers = auth_headers(user.id, lab.id, "admin")
    response = client.post(
        "/device-integration/connectors",
        json={**_connector_payload("CONN-SECRET-001"), "config_safe": {"api_token": "should-never-enter"}},
        headers=headers,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Request validation failed."


def test_simulator_lifecycle_updates_connector_and_event_without_raw_payload(client, make_lab, make_lab_user):
    lab = make_lab("Simulator Lab")
    user = make_lab_user(lab.id, role="admin")
    headers = auth_headers(user.id, lab.id, "admin")
    assert client.post("/device-integration/devices", json=_device_payload("HL7-SIM-001"), headers=headers).status_code == 201
    connector_payload = _connector_payload("CONN-HL7-SIM-001", device_uid="HL7-SIM-001")
    assert client.post("/device-integration/connectors", json=connector_payload, headers=headers).status_code == 201

    success = client.post(
        "/device-integration/connectors/CONN-HL7-SIM-001/simulate",
        json={"simulator_key": "hl7v2.oru.r01", "scenario": "success", "message_type": "ORU^R01", "item_count": 2},
        headers=headers,
    )
    assert success.status_code == 200
    assert success.json()["outcome"] == "accepted"
    assert success.json()["connector_status"] == "healthy"
    assert success.json()["simulation_only"] is True
    assert success.json()["event_id"] is not None

    failure = client.post(
        "/device-integration/connectors/CONN-HL7-SIM-001/simulate",
        json={"simulator_key": "hl7v2.oru.r01", "scenario": "malformed"},
        headers=headers,
    )
    assert failure.status_code == 200
    assert failure.json()["outcome"] == "rejected"
    assert failure.json()["connector_status"] == "error"

    events = client.get("/device-integration/events", headers=headers)
    assert events.status_code == 200
    assert any(event["event_type"] == "simulated_protocol_exchange" for event in events.json()["events"])
    assert all("raw_payload" not in event for event in events.json()["events"])


def test_lab_staff_cannot_register_connector_or_profile(client, make_lab, make_lab_user):
    lab = make_lab("Adapter Read Only Lab")
    user = make_lab_user(lab.id, role="lab_staff")
    headers = auth_headers(user.id, lab.id, "lab_staff")
    assert client.get("/device-integration/connectors", headers=headers).status_code == 200
    assert client.get("/device-integration/protocol-profiles", headers=headers).status_code == 200
    assert client.post("/device-integration/connectors", json=_connector_payload("DENIED-CONN-001"), headers=headers).status_code == 403
    assert client.post(
        "/device-integration/protocol-profiles",
        json={"profile_key": "denied.profile", "protocol": "ASTM"},
        headers=headers,
    ).status_code == 403
