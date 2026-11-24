"""Wave A evidence: generated capability CRUD routes are real and persistent."""

from __future__ import annotations

import pytest

from tests.conftest import auth_headers

CAPABILITIES = (
    ("document_management", "/document-management"),
    ("encounter_management", "/encounter-management"),
    ("storage_service", "/storage-service"),
    ("clinical_foundation", "/clinical-foundation"),
    ("workflow_engine", "/workflow-engine"),
    ("reporting_service", "/reporting-service"),
    ("provider_management", "/provider-management"),
    ("healthcare_consent", "/healthcare-consent"),
)


@pytest.fixture()
def crud_context(make_lab, make_lab_user):
    lab = make_lab()
    user = make_lab_user(lab.id, role="admin")
    return {
        "headers": auth_headers(user.id, lab.id, role="admin"),
        "lab_id": lab.id,
        "user_id": user.id,
    }


@pytest.fixture()
def headers(crud_context):
    return crud_context["headers"]


@pytest.mark.parametrize(("capability", "prefix"), CAPABILITIES)
def test_capability_crud_lifecycle(client, headers, crud_context, capability, prefix):
    created = client.post(
        f"{prefix}/",
        headers=headers,
        json={"name": f"{capability}-record", "status": "active"},
    )
    assert created.status_code == 200, created.text
    body = created.json()
    record_id = body["id"]
    assert record_id
    assert body["capability"] == capability
    assert body["lab_id"] == crud_context["lab_id"]
    assert body["owner_user_id"] == crud_context["user_id"]
    assert body["name"] == f"{capability}-record"

    listed = client.get(f"{prefix}/", headers=headers)
    assert listed.status_code == 200, listed.text
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == record_id

    fetched = client.get(f"{prefix}/{record_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "active"

    updated = client.put(
        f"{prefix}/{record_id}",
        headers=headers,
        json={"name": "updated", "status": "closed"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "updated"
    assert updated.json()["status"] == "closed"

    deleted = client.delete(f"{prefix}/{record_id}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json() == {"success": True, "id": record_id, "capability": capability}

    missing = client.get(f"{prefix}/{record_id}", headers=headers)
    assert missing.status_code == 404


def test_capability_records_are_namespaced(client, headers):
    first = client.post(
        "/document-management/",
        headers=headers,
        json={"name": "document-only"},
    ).json()
    assert first["id"]

    missing = client.get(f"/provider-management/{first['id']}", headers=headers)
    assert missing.status_code == 404

    provider_list = client.get("/provider-management/", headers=headers).json()
    assert provider_list["total"] == 0


def test_capability_crud_rejects_invalid_payloads(client, headers):
    assert client.post("/workflow-engine/", headers=headers, json={}).status_code == 422
    assert client.post(
        "/workflow-engine/",
        headers=headers,
        json={"id": "spoofed"},
    ).status_code == 422
    assert client.post(
        "/workflow-engine/",
        headers=headers,
        json=["not", "an", "object"],
    ).status_code == 422
    assert client.post(
        "/workflow-engine/",
        headers=headers,
        json={"lab_id": 999},
    ).status_code == 422
    assert client.post(
        "/workflow-engine/",
        headers=headers,
        json={"owner_user_id": 999},
    ).status_code == 422


def test_capability_crud_requires_authentication(client):
    response = client.post("/workflow-engine/", json={"name": "anonymous"})
    assert response.status_code == 401


def test_capability_crud_enforces_read_write_permissions(
    client, crud_context, make_lab_user
):
    readonly = make_lab_user(crud_context["lab_id"], role="ministry_admin")
    readonly_headers = auth_headers(readonly.id, crud_context["lab_id"], role="ministry_admin")

    assert client.get("/workflow-engine/", headers=readonly_headers).status_code == 200
    denied = client.post(
        "/workflow-engine/",
        headers=readonly_headers,
        json={"name": "denied"},
    )
    assert denied.status_code == 403


def test_capability_records_are_lab_scoped(client, crud_context, make_lab, make_lab_user):
    created = client.post(
        "/clinical-foundation/",
        headers=crud_context["headers"],
        json={"name": "lab-a-only"},
    ).json()
    record_id = created["id"]

    other_lab = make_lab()
    other_user = make_lab_user(other_lab.id, role="admin")
    other_headers = auth_headers(other_user.id, other_lab.id, role="admin")

    assert client.get(f"/clinical-foundation/{record_id}", headers=other_headers).status_code == 404
    assert client.get("/clinical-foundation/", headers=other_headers).json()["total"] == 0
    assert client.put(
        f"/clinical-foundation/{record_id}",
        headers=other_headers,
        json={"name": "tamper"},
    ).status_code == 404
    assert client.delete(
        f"/clinical-foundation/{record_id}", headers=other_headers
    ).status_code == 404


def test_capability_crud_writes_audit_events(client, crud_context, db):
    from app.models.audit_log import AuditLog

    created = client.post(
        "/reporting-service/",
        headers=crud_context["headers"],
        json={"name": "audited"},
    ).json()
    record_id = created["id"]
    client.put(
        f"/reporting-service/{record_id}",
        headers=crud_context["headers"],
        json={"name": "audited-updated"},
    )
    client.delete(f"/reporting-service/{record_id}", headers=crud_context["headers"])

    actions = [
        row.action
        for row in db.query(AuditLog)
        .filter(AuditLog.resource_type == "reporting_service")
        .order_by(AuditLog.id)
        .all()
    ]
    assert actions == [
        "capability_record.create",
        "capability_record.update",
        "capability_record.delete",
    ]
