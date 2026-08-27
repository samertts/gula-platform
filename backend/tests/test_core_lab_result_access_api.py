from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.clinical.laboratory.models import CoreClinicalCommandReceipt, CoreSpecimenEvent
from app.clinical.results.models import CoreClinicalNotification, CoreLabResult
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync
from app.identity.models import (
    Account,
    IdentityRecord,
    Membership,
    Permission,
    Person,
    RoleAssignment,
    RolePermission,
    UserSession,
    WorkspaceSessionContext,
)
from app.identity.models.audit import IdentityAuditEntry
from app.identity.models.membership import MembershipStatus
from app.main import app

from tests.test_core_appointment_api import appointment_context


@pytest.fixture()
def context(request):
    return request.getfixturevalue("appointment_context")


def _id(prefix: str) -> str:
    return (prefix + uuid4().hex.upper())[:26]


def _uuid() -> str:
    return str(uuid4())


LAB_PERMISSIONS = (
    "clinical.lab_order.create",
    "clinical.lab_order.read",
    "clinical.lab_order.verify",
    "clinical.specimen.manage",
    "clinical.result.write",
    "clinical.result.read",
    "clinical.result.validate_technical",
    "clinical.result.validate_clinical",
    "clinical.result.release",
    "clinical.result.amend",
    "clinical.critical.acknowledge",
)


def _grant_permissions(context, keys=LAB_PERMISSIONS):
    db = context["db"]
    account = context["account"]
    assignment = db.query(RoleAssignment).filter(RoleAssignment.account_id == account.id).one()
    for key in keys:
        permission = db.query(Permission).filter(Permission.permission_key == key).first()
        if permission is None:
            permission = Permission(
                id=_id("PERM"),
                uuid=_uuid(),
                permission_key=key,
                name=key,
                name_ar=key,
                resource=key.split(".")[1],
                action=key.rsplit(".", 1)[-1],
                sensitivity="high",
                status="active",
            )
            db.add(permission)
            db.flush()
        linked = db.query(RolePermission).filter(RolePermission.role_id == assignment.role_id, RolePermission.permission_id == permission.id).first()
        if linked is None:
            db.add(RolePermission(id=_id("ROLEPERM"), role_id=assignment.role_id, permission_id=permission.id, status="active"))
    db.flush()


def _provision_second_actor(context):
    db = context["db"]
    organization = context["organization"]
    facility = context["facility"]
    workspace = context["workspace"]
    role_assignment = db.query(RoleAssignment).filter(RoleAssignment.account_id == context["account"].id).one()
    person = Person(id=_id("PERSON"), uuid=_uuid(), given_name="Synthetic", family_name="Reviewer", full_name_ar="مراجع اصطناعي", is_active=True)
    identity = IdentityRecord(id=_id("IDENTITY"), uuid=_uuid(), person_id=person.id, identity_type="professional", status="active", issued_at=datetime.now(UTC), is_active=True)
    account = Account(id=_id("ACCOUNT"), uuid=_uuid(), identity_id=identity.id, status="active", is_active=True, is_locked=False, email=f"reviewer-{uuid4().hex}@example.test")
    session = UserSession(id=_id("SESSION"), uuid=_uuid(), account_id=account.id, token_jti=_id("JTI"), session_type="web", is_active=True, expires_at=datetime.now(UTC) + timedelta(hours=1))
    context_row = WorkspaceSessionContext(id=_id("CONTEXT"), session_id=session.id, account_id=account.id, identity_id=identity.id, workspace_id=workspace.id, is_active=True)
    membership = Membership(id=_id("MEMBERSHIP"), uuid=_uuid(), membership_key=_id("MEMKEY"), account_id=account.id, identity_id=identity.id, organization_id=organization.id, facility_id=facility.id, workspace_id=workspace.id, relationship_type="professional", scope_type="workspace", status=MembershipStatus.active.value, source="synthetic_test", is_active=True, activated_at=datetime.now(UTC))
    assignment = RoleAssignment(id=_id("ASSIGN"), uuid=_uuid(), assignment_key=_id("ASSIGNKEY"), account_id=account.id, membership_id=membership.id, role_id=role_assignment.role_id, organization_id=organization.id, facility_id=facility.id, workspace_id=workspace.id, scope_type="workspace", status="active", activated_at=datetime.now(UTC))
    db.add_all([person, identity, account, session, context_row, membership, assignment])
    db.flush()
    return account, session, person


def _set_actor(account, session):
    app.dependency_overrides[get_current_niam_actor_sync] = lambda: NiamActor(account=account, session=session)


def _create_visit(client, context):
    workspace = context["workspace"]
    account = context["account"]
    person = context["person"]
    slot = client.post(
        "/api/v1/appointments/slots",
        headers={"Idempotency-Key": "lab-slot-1"},
        json={"workspace_id": workspace.id, "provider_account_id": account.id, "service_code": "LAB-CONSULT", "starts_at": "2030-02-01T10:00:00Z", "ends_at": "2030-02-01T10:30:00Z"},
    )
    assert slot.status_code == 201, slot.text
    appointment = client.post(
        "/api/v1/appointments",
        headers={"Idempotency-Key": "lab-appointment-1"},
        json={"workspace_id": workspace.id, "patient_person_id": person.id, "slot_id": slot.json()["id"], "purpose": "TREATMENT"},
    )
    assert appointment.status_code == 201, appointment.text
    confirmed = client.post(
        f"/api/v1/appointments/{appointment.json()['id']}/confirm?workspace_id={workspace.id}",
        headers={"Idempotency-Key": "lab-confirm-1", "If-Match": '"1"'},
        json={"reason": "Synthetic laboratory visit"},
    )
    assert confirmed.status_code == 200, confirmed.text
    checkin = client.post(
        "/api/v1/encounters/check-in",
        headers={"Idempotency-Key": "lab-checkin-1"},
        json={"appointment_id": appointment.json()["id"], "workspace_id": workspace.id},
    )
    assert checkin.status_code == 201, checkin.text
    start = client.post(
        f"/api/v1/encounters/{checkin.json()['id']}/start",
        headers={"Idempotency-Key": "lab-start-1", "If-Match": '"1"'},
        json={"workspace_id": workspace.id},
    )
    assert start.status_code == 200, start.text
    return checkin.json()["id"]


def _create_order_and_specimen(client, context, encounter_id):
    workspace_id = context["workspace"].id
    order = client.post(
        "/api/v1/clinical/lab-orders",
        headers={"Idempotency-Key": "lab-order-create-1"},
        json={"encounter_id": encounter_id, "workspace_id": workspace_id, "priority": "ROUTINE", "items": [{"test_code": "CBC", "test_name": "Complete Blood Count", "specimen_type": "WHOLE_BLOOD"}]},
    )
    assert order.status_code == 201, order.text
    replay = client.post(
        "/api/v1/clinical/lab-orders",
        headers={"Idempotency-Key": "lab-order-create-1"},
        json={"encounter_id": encounter_id, "workspace_id": workspace_id, "priority": "ROUTINE", "items": [{"test_code": "CBC", "test_name": "Complete Blood Count", "specimen_type": "WHOLE_BLOOD"}]},
    )
    assert replay.status_code == 201 and replay.json()["id"] == order.json()["id"]
    detail = client.get(f"/api/v1/clinical/lab-orders/{order.json()['id']}?workspace_id={workspace_id}")
    assert detail.status_code == 200, detail.text
    item_id = detail.json()["items"][0]["id"]
    specimen = client.post(
        "/api/v1/clinical/specimens",
        headers={"Idempotency-Key": "specimen-create-1"},
        json={"workspace_id": workspace_id, "order_item_id": item_id},
    )
    assert specimen.status_code == 201, specimen.text
    return order.json(), specimen.json()


def _walk_specimen(client, context, specimen_id):
    workspace_id = context["workspace"].id
    version = 1
    for path, key in (("collect", "specimen-collect-1"), ("receive", "specimen-receive-1"), ("process", "specimen-process-1"), ("analyze", "specimen-analyze-1"), ("validate", "specimen-validate-1")):
        response = client.post(
            f"/api/v1/clinical/specimens/{specimen_id}/{path}",
            headers={"Idempotency-Key": key, "If-Match": f'"{version}"'},
            json={"workspace_id": workspace_id},
        )
        assert response.status_code == 200, response.text
        version = response.json()["version"]
    return version


def test_lab_result_access_golden_path_and_revoke(client, context):
    _grant_permissions(context)
    reviewer_account, reviewer_session, _ = _provision_second_actor(context)
    encounter_id = _create_visit(client, context)
    order, specimen = _create_order_and_specimen(client, context, encounter_id)
    assert _walk_specimen(client, context, specimen["id"]) == 6

    workspace_id = context["workspace"].id
    result = client.post(
        "/api/v1/clinical/results",
        headers={"Idempotency-Key": "result-create-1"},
        json={"workspace_id": workspace_id, "specimen_id": specimen["id"], "value_numeric": 5.2, "unit": "10^9/L", "reference_low": 4.0, "reference_high": 10.0, "source_message_id": "synthetic-message-1", "provenance_type": "IMPORTED_SYNTHETIC"},
    )
    assert result.status_code == 201, result.text
    result_body = result.json()
    replay = client.post(
        "/api/v1/clinical/results",
        headers={"Idempotency-Key": "result-create-1"},
        json={"workspace_id": workspace_id, "specimen_id": specimen["id"], "value_numeric": 5.2, "unit": "10^9/L", "reference_low": 4.0, "reference_high": 10.0, "source_message_id": "synthetic-message-1", "provenance_type": "IMPORTED_SYNTHETIC"},
    )
    assert replay.status_code == 201 and replay.json()["id"] == result_body["id"]

    technical = client.post(f"/api/v1/clinical/results/{result_body['id']}/validate-technical", headers={"Idempotency-Key": "result-tech-1", "If-Match": '"1"'}, json={"workspace_id": workspace_id})
    assert technical.status_code == 200 and technical.json()["status"] == "TECHNICALLY_VALIDATED"

    _set_actor(reviewer_account, reviewer_session)
    clinical = client.post(f"/api/v1/clinical/results/{result_body['id']}/validate-clinical", headers={"Idempotency-Key": "result-clinical-1", "If-Match": '"2"'}, json={"workspace_id": workspace_id})
    assert clinical.status_code == 200 and clinical.json()["status"] == "CLINICALLY_VALIDATED"
    released = client.post(f"/api/v1/clinical/results/{result_body['id']}/release", headers={"Idempotency-Key": "result-release-1", "If-Match": '"3"'}, json={"workspace_id": workspace_id})
    assert released.status_code == 200 and released.json()["status"] == "RELEASED"

    _set_actor(context["account"], context["session"])
    grant = client.post(
        "/api/v1/clinical/access/grants",
        headers={"Idempotency-Key": "grant-1"},
        json={"workspace_id": workspace_id, "resource_type": "lab_result", "resource_id": result_body["id"], "grantee_account_id": reviewer_account.id, "purpose": "TREATMENT", "scope": {"read_result": True}, "duration_hours": 24},
    )
    assert grant.status_code == 201, grant.text
    grant_body = grant.json()

    _set_actor(reviewer_account, reviewer_session)
    shared = client.get(f"/api/v1/clinical/access/results/{result_body['id']}?workspace_id={workspace_id}")
    assert shared.status_code == 200 and shared.json()["access_mode"] == "GRANTED"

    _set_actor(context["account"], context["session"])
    revoked = client.post(f"/api/v1/clinical/access/grants/{grant_body['id']}/revoke", headers={"Idempotency-Key": "revoke-1", "If-Match": '"1"'}, json={"workspace_id": workspace_id, "reason": "Synthetic test revocation"})
    assert revoked.status_code == 200 and revoked.json()["status"] == "REVOKED"
    _set_actor(reviewer_account, reviewer_session)
    denied = client.get(f"/api/v1/clinical/access/results/{result_body['id']}?workspace_id={workspace_id}")
    assert denied.status_code == 403

    _set_actor(context["account"], context["session"])
    history = client.get(f"/api/v1/clinical/access/history?workspace_id={workspace_id}&limit=10&offset=0")
    assert history.status_code == 200
    assert {entry["action"] for entry in history.json()["items"]} >= {"GRANT_CREATED", "ACCESS_USED", "GRANT_REVOKED"}
    assert all("token" not in entry and "internal_id" not in entry for entry in history.json()["items"])
    assert context["db"].query(IdentityAuditEntry).filter(IdentityAuditEntry.event_type == "ACCESS_DENIED", IdentityAuditEntry.target_id == result_body["id"]).count() >= 1
    assert client.get(f"/api/v1/clinical/specimens/worklist?workspace_id={workspace_id}&limit=1").status_code == 200
    assert order["id"]


def test_lab_result_safety_guards_and_audit(client, context):
    _grant_permissions(context)
    reviewer_account, reviewer_session, _ = _provision_second_actor(context)
    encounter_id = _create_visit(client, context)
    _, specimen = _create_order_and_specimen(client, context, encounter_id)
    workspace_id = context["workspace"].id

    before_validation = client.post(
        "/api/v1/clinical/results",
        headers={"Idempotency-Key": "result-before-specimen-validation"},
        json={"workspace_id": workspace_id, "specimen_id": specimen["id"], "value_text": "not yet verified"},
    )
    assert before_validation.status_code == 409

    stale = client.post(
        f"/api/v1/clinical/specimens/{specimen['id']}/collect",
        headers={"Idempotency-Key": "specimen-stale", "If-Match": '"9"'},
        json={"workspace_id": workspace_id},
    )
    assert stale.status_code == 409 and stale.json()["code"] == "VERSION_CONFLICT"

    _walk_specimen(client, context, specimen["id"])
    result = client.post(
        "/api/v1/clinical/results",
        headers={"Idempotency-Key": "result-critical"},
        json={"workspace_id": workspace_id, "specimen_id": specimen["id"], "value_numeric": 20, "unit": "10^9/L", "reference_low": 4, "reference_high": 10, "source_message_id": "critical-message"},
    )
    assert result.status_code == 201 and result.json()["abnormal_flag"] == "HIGH"
    result_id = result.json()["id"]
    technical = client.post(f"/api/v1/clinical/results/{result_id}/validate-technical", headers={"Idempotency-Key": "critical-tech", "If-Match": '"1"'}, json={"workspace_id": workspace_id})
    assert technical.status_code == 200
    _set_actor(reviewer_account, reviewer_session)
    clinical = client.post(f"/api/v1/clinical/results/{result_id}/validate-clinical", headers={"Idempotency-Key": "critical-clinical", "If-Match": '"2"'}, json={"workspace_id": workspace_id})
    assert clinical.status_code == 200
    blocked_release = client.post(f"/api/v1/clinical/results/{result_id}/release", headers={"Idempotency-Key": "critical-release-blocked", "If-Match": '"3"'}, json={"workspace_id": workspace_id})
    assert blocked_release.status_code == 409 and blocked_release.json()["code"] == "CRITICAL_ACK_REQUIRED"
    ack = client.post(f"/api/v1/clinical/results/{result_id}/critical/acknowledge", headers={"Idempotency-Key": "critical-ack", "If-Match": '"1"'}, json={"workspace_id": workspace_id, "reason": "Synthetic clinical review"})
    assert ack.status_code == 200 and ack.json()["status"] == "ACKNOWLEDGED"
    released = client.post(f"/api/v1/clinical/results/{result_id}/release", headers={"Idempotency-Key": "critical-release", "If-Match": '"3"'}, json={"workspace_id": workspace_id})
    assert released.status_code == 200

    db = context["db"]
    assert db.query(CoreClinicalCommandReceipt).filter(CoreClinicalCommandReceipt.operation == "result.create").count() >= 1
    assert db.query(CoreSpecimenEvent).filter(CoreSpecimenEvent.specimen_id == specimen["id"]).count() == 6
    assert db.query(CoreClinicalNotification).filter(CoreClinicalNotification.event_type == "CRITICAL_RESULT_DETECTED").count() == 1
    assert db.query(CoreLabResult).filter(CoreLabResult.id == result_id, CoreLabResult.status == "RELEASED").one()


def test_specimen_duplicate_collection_is_rejected(client, context):
    _grant_permissions(context)
    encounter_id = _create_visit(client, context)
    _, specimen = _create_order_and_specimen(client, context, encounter_id)
    workspace_id = context["workspace"].id
    first = client.post(
        f"/api/v1/clinical/specimens/{specimen['id']}/collect",
        headers={"Idempotency-Key": "duplicate-collect-1", "If-Match": '"1"'},
        json={"workspace_id": workspace_id},
    )
    second = client.post(
        f"/api/v1/clinical/specimens/{specimen['id']}/collect",
        headers={"Idempotency-Key": "duplicate-collect-2", "If-Match": '"1"'},
        json={"workspace_id": workspace_id},
    )
    assert first.status_code == 200
    assert second.status_code == 409
    assert context["db"].query(CoreSpecimenEvent).filter(CoreSpecimenEvent.specimen_id == specimen["id"], CoreSpecimenEvent.event_type == "SPECIMEN_COLLECTED").count() == 1


def test_lab_order_audit_failure_rolls_back_state_and_receipt(client, context, monkeypatch):
    from app.clinical.laboratory.service import LaboratoryService

    _grant_permissions(context)
    encounter_id = _create_visit(client, context)
    order, _ = _create_order_and_specimen(client, context, encounter_id)
    workspace_id = context["workspace"].id

    def fail_audit(*_args, **_kwargs):
        raise RuntimeError("synthetic audit failure")

    monkeypatch.setattr(LaboratoryService, "_audit", fail_audit)
    response = client.post(
        f"/api/v1/clinical/lab-orders/{order['id']}/verify",
        headers={"Idempotency-Key": "verify-audit-failure", "If-Match": '"2"'},
        json={"workspace_id": workspace_id},
    )
    assert response.status_code == 500, response.text
    db = context["db"]
    stored_order = db.query(__import__("app.clinical.laboratory.models", fromlist=["CoreLabOrder"]).CoreLabOrder).filter_by(id=order["id"]).one()
    assert stored_order.status == "PLACED" and stored_order.version == 2
    assert db.query(CoreClinicalCommandReceipt).filter(CoreClinicalCommandReceipt.operation == "lab.order.verify", CoreClinicalCommandReceipt.idempotency_key == "verify-audit-failure").count() == 0


def test_result_fhir_projection_is_side_effect_free_and_redacts_subject_by_default():
    from app.clinical.results.fhir import result_to_fhir_observation

    class SyntheticResult:
        result_id = "RESULT-SYNTHETIC-01"
        status = "RELEASED"
        version = 3
        test_code = "CBC"
        test_name = "Complete Blood Count"
        value_numeric = 5.2
        value_text = None
        unit = "10^9/L"
        abnormal_flag = "NORMAL"
        provenance_type = "IMPORTED_SYNTHETIC"
        source_message_id = "message-synthetic-01"
        patient_person_id = "PERSON-SYNTHETIC-01"
        released_at = None

    projection = result_to_fhir_observation(SyntheticResult())
    assert projection["resourceType"] == "Observation"
    assert projection["status"] == "final"
    assert projection["meta"]["versionId"] == "3"
    assert "subject" not in projection
    assert result_to_fhir_observation(SyntheticResult(), include_patient_reference=True)["subject"]["reference"] == "Patient/PERSON-SYNTHETIC-01"
