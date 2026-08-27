from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.clinical.appointments import routes as appointment_routes
from app.identity.api.workspaces import NiamActor, get_current_niam_actor_sync
from app.identity.models import (
    Account,
    IdentityRecord,
    Membership,
    NIAMAdminBranch,
    NIAMAdminFacility,
    NIAMOrganization,
    Permission,
    Person,
    Role,
    RoleAssignment,
    RolePermission,
    UserSession,
    Workspace,
    WorkspaceSessionContext,
)
from app.identity.models.audit import IdentityAuditEntry
from app.identity.models.membership import MembershipStatus
from app.identity.models.workspace import WorkspaceStatus
from app.main import app
from fastapi import HTTPException
from fastapi.testclient import TestClient


def _id(prefix: str) -> str:
    return (prefix + uuid4().hex.upper())[:26]


def _uuid() -> str:
    return str(uuid4())


@pytest.fixture()
def appointment_context(client: TestClient, db):
    organization = NIAMOrganization(
        id=_id("ORG"),
        uuid=_uuid(),
        org_id=_id("ORGREF"),
        name_en="Synthetic Care Organization",
        name_ar="منظمة رعاية اصطناعية",
        org_type="health_center",
        status="active",
        is_active=True,
    )
    branch = NIAMAdminBranch(
        id=_id("BR"),
        uuid=_uuid(),
        branch_id=_id("BRREF"),
        portal_id=_id("PORTAL"),
        organization_id=organization.id,
        name_en="Synthetic Branch",
        name_ar="فرع اصطناعي",
        status="active",
        is_active=True,
    )
    facility = NIAMAdminFacility(
        id=_id("FAC"),
        uuid=_uuid(),
        facility_id=_id("FACREF"),
        branch_id=branch.id,
        organization_id=organization.id,
        name_en="Synthetic Facility",
        name_ar="منشأة اصطناعية",
        facility_type="clinic",
        status="active",
        is_active=True,
    )
    person = Person(
        id=_id("PERSON"),
        uuid=_uuid(),
        given_name="Synthetic",
        family_name="Citizen",
        full_name_ar="مواطن اصطناعي",
        is_active=True,
    )
    identity = IdentityRecord(
        id=_id("IDENTITY"),
        uuid=_uuid(),
        person_id=person.id,
        identity_type="citizen",
        status="active",
        issued_at=datetime.now(UTC),
        is_active=True,
    )
    account = Account(
        id=_id("ACCOUNT"),
        uuid=_uuid(),
        identity_id=identity.id,
        status="active",
        is_active=True,
        is_locked=False,
        email=f"synthetic-{uuid4().hex}@example.test",
    )
    session = UserSession(
        id=_id("SESSION"),
        uuid=_uuid(),
        account_id=account.id,
        token_jti=_id("JTI"),
        session_type="web",
        is_active=True,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    workspace = Workspace(
        id=_id("WORKSPACE"),
        uuid=_uuid(),
        workspace_key=_id("WSKEY"),
        workspace_type="professional",
        name="Synthetic Clinical Workspace",
        name_ar="مساحة سريرية اصطناعية",
        status=WorkspaceStatus.active.value,
        owner_account_id=account.id,
        organization_id=organization.id,
        facility_id=facility.id,
        is_personal=False,
    )
    context = WorkspaceSessionContext(
        id=_id("CONTEXT"),
        session_id=session.id,
        account_id=account.id,
        identity_id=identity.id,
        workspace_id=workspace.id,
        is_active=True,
    )
    membership = Membership(
        id=_id("MEMBERSHIP"),
        uuid=_uuid(),
        membership_key=_id("MEMKEY"),
        account_id=account.id,
        identity_id=identity.id,
        organization_id=organization.id,
        facility_id=facility.id,
        workspace_id=workspace.id,
        relationship_type="professional",
        scope_type="workspace",
        status=MembershipStatus.active.value,
        source="administrative_provisioning",
        is_active=True,
        activated_at=datetime.now(UTC),
    )
    role = Role(
        id=_id("ROLE"),
        uuid=_uuid(),
        role_key=_id("ROLEKEY"),
        name="Synthetic Appointment Operator",
        name_ar="مشغل مواعيد اصطناعي",
        scope_type="workspace",
        status="active",
        is_system=False,
    )
    permissions = {}
    new_permissions = []
    for key in (
        "appointment.request",
        "appointment.confirm",
        "appointment.slot.manage",
        "appointment.read",
    ):
        permission = db.query(Permission).filter(Permission.permission_key == key).first()
        if permission is None:
            permission = Permission(
                id=_id("PERM"),
                uuid=_uuid(),
                permission_key=key,
                name=key,
                name_ar=key,
                resource="appointment",
                action=key.rsplit(".", 1)[-1],
                sensitivity="high",
                status="active",
            )
            new_permissions.append(permission)
        permissions[key] = permission
    assignment = RoleAssignment(
        id=_id("ASSIGN"),
        uuid=_uuid(),
        assignment_key=_id("ASSIGNKEY"),
        account_id=account.id,
        membership_id=membership.id,
        role_id=role.id,
        organization_id=organization.id,
        facility_id=facility.id,
        workspace_id=workspace.id,
        scope_type="workspace",
        status="active",
        activated_at=datetime.now(UTC),
    )
    db.add_all([organization, branch, facility, person, identity, account, session, workspace, context, membership, role, assignment, *new_permissions])
    db.flush()
    db.add_all(
        [
            RolePermission(
                id=_id("ROLEPERM"),
                role_id=role.id,
                permission_id=permission.id,
                status="active",
            )
            for permission in permissions.values()
        ],
    )
    db.flush()
    actor = NiamActor(account=account, session=session)
    actor_account_id = account.id
    actor_session_id = session.id

    def _fresh_actor() -> NiamActor:
        fresh_account = db.query(Account).filter(Account.id == actor_account_id).one()
        fresh_session = db.query(UserSession).filter(UserSession.id == actor_session_id).one()
        return NiamActor(account=fresh_account, session=fresh_session)

    app.dependency_overrides[get_current_niam_actor_sync] = _fresh_actor
    try:
        yield {
            "actor": actor,
            "person": person,
            "account": account,
            "session": session,
            "organization": organization,
            "facility": facility,
            "workspace": workspace,
            "membership": membership,
            "db": db,
        }
    finally:
        app.dependency_overrides.pop(get_current_niam_actor_sync, None)


def _create_slot(client: TestClient, context: dict[str, object], key: str = "slot-1") -> dict[str, object]:
    workspace = context["workspace"]
    account = context["account"]
    response = client.post(
        "/api/v1/appointments/slots",
        headers={"Idempotency-Key": key, "X-Request-ID": "synthetic-slot-request"},
        json={
            "workspace_id": workspace.id,
            "provider_account_id": account.id,
            "service_code": "GENERAL-CONSULT",
            "starts_at": "2030-01-01T10:00:00Z",
            "ends_at": "2030-01-01T10:30:00Z",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_core_appointment_golden_path_and_idempotent_replay(client: TestClient, appointment_context: dict[str, object]):
    slot = _create_slot(client, appointment_context)
    workspace = appointment_context["workspace"]
    workspace_id = workspace.id
    person = appointment_context["person"]
    request_body = {
        "workspace_id": workspace_id,
        "patient_person_id": person.id,
        "slot_id": slot["id"],
        "purpose": "TREATMENT",
    }
    first = client.post("/api/v1/appointments", headers={"Idempotency-Key": "request-1"}, json=request_body)
    assert first.status_code == 201, first.text
    first_body = first.json()
    assert first_body["state"] == "REQUESTED"
    assert first_body["version"] == 1

    replay = client.post("/api/v1/appointments", headers={"Idempotency-Key": "request-1"}, json=request_body)
    assert replay.status_code == 201, replay.text
    assert replay.json()["id"] == first_body["id"]

    key_conflict = client.post(
        "/api/v1/appointments",
        headers={"Idempotency-Key": "request-1"},
        json={**request_body, "purpose": "DIAGNOSIS"},
    )
    assert key_conflict.status_code == 409
    assert key_conflict.json()["code"] == "IDEMPOTENCY_CONFLICT"

    confirmed = client.post(
        f"/api/v1/appointments/{first_body['id']}/confirm?workspace_id={workspace_id}",
        headers={"Idempotency-Key": "confirm-1", "If-Match": '"1"'},
        json={"reason": "Synthetic confirmation"},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["state"] == "CONFIRMED"
    assert confirmed.json()["version"] == 2

    stale = client.post(
        f"/api/v1/appointments/{first_body['id']}/confirm?workspace_id={workspace_id}",
        headers={"Idempotency-Key": "confirm-stale", "If-Match": "1"},
        json={},
    )
    assert stale.status_code == 409
    stale_payload = stale.json()
    assert stale_payload["code"] == "VERSION_CONFLICT"
    assert stale_payload["details"]["message_ar"] == "تغير الموعد قبل تنفيذ العملية."

    listed = client.get(f"/api/v1/appointments?workspace_id={workspace_id}")
    assert listed.status_code == 200, listed.text
    assert listed.json()["total"] == 1


def test_core_appointment_denies_wrong_patient_and_wrong_workspace(client: TestClient, appointment_context: dict[str, object]):
    slot = _create_slot(client, appointment_context, key="slot-idor")
    workspace = appointment_context["workspace"]
    workspace_id = workspace.id
    denied = client.post(
        "/api/v1/appointments",
        headers={"Idempotency-Key": "request-idor"},
        json={
            "workspace_id": workspace_id,
            "patient_person_id": "Z" * 26,
            "slot_id": slot["id"],
            "purpose": "TREATMENT",
        },
    )
    assert denied.status_code == 403
    assert denied.json()["code"] == "FORBIDDEN"

    wrong_workspace = client.get(
        f"/api/v1/appointments/slots?workspace_id={'Z' * 26}",
    )
    assert wrong_workspace.status_code == 403
    assert wrong_workspace.json()["code"] == "FORBIDDEN"

    db = appointment_context["db"]
    context = db.query(WorkspaceSessionContext).filter(WorkspaceSessionContext.session_id == appointment_context["session"].id).one()
    context.identity_id = "Z" * 26
    db.commit()
    identity_mismatch = client.get(f"/api/v1/appointments/slots?workspace_id={workspace_id}")
    assert identity_mismatch.status_code == 403
    assert identity_mismatch.json()["code"] == "FORBIDDEN"
    denial = (
        db.query(IdentityAuditEntry)
        .filter(IdentityAuditEntry.event_type == "APPOINTMENT_AUTHORIZATION_DENIED")
        .first()
    )
    assert denial is not None
    assert denial.outcome == "denied"


@pytest.mark.parametrize("session_failure", ["expired", "revoked"])
def test_core_appointment_rejects_expired_or_revoked_session(client: TestClient, appointment_context: dict[str, object], session_failure: str):
    workspace = appointment_context["workspace"]
    session = appointment_context["session"]
    db = appointment_context["db"]
    if session_failure == "expired":
        session.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    else:
        session.is_active = False
    db.commit()

    response = client.get(f"/api/v1/appointments/slots?workspace_id={workspace.id}")
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


def test_core_appointment_error_contract_and_rate_limit(client: TestClient, appointment_context: dict[str, object], monkeypatch: pytest.MonkeyPatch):
    workspace = appointment_context["workspace"]
    person = appointment_context["person"]
    missing_key = client.post(
        "/api/v1/appointments",
        json={"workspace_id": workspace.id, "patient_person_id": person.id, "slot_id": "Z" * 26, "purpose": "TREATMENT"},
    )
    assert missing_key.status_code == 400
    assert missing_key.json()["code"] == "VALIDATION_ERROR"

    missing_if_match = client.post(
        f"/api/v1/appointments/{'Z' * 26}/confirm?workspace_id={workspace.id}",
        headers={"Idempotency-Key": "confirm-no-version"},
        json={},
    )
    assert missing_if_match.status_code == 428
    assert missing_if_match.json()["code"] == "PRECONDITION_REQUIRED"

    def _limited(*_args, **_kwargs):
        raise HTTPException(status_code=429, detail="rate limit reached")

    monkeypatch.setattr(appointment_routes, "rate_limit_user", _limited)
    limited = client.get(f"/api/v1/appointments/slots?workspace_id={workspace.id}")
    assert limited.status_code == 429
    assert limited.json()["code"] == "RATE_LIMITED"


def test_core_appointment_slot_conflict_is_rejected(client: TestClient, appointment_context: dict[str, object]):
    _create_slot(client, appointment_context, key="slot-conflict-1")
    conflict = client.post(
        "/api/v1/appointments/slots",
        headers={"Idempotency-Key": "slot-conflict-2"},
        json={
            "workspace_id": appointment_context["workspace"].id,
            "provider_account_id": appointment_context["account"].id,
            "service_code": "GENERAL-CONSULT",
            "starts_at": "2030-01-01T10:00:00Z",
            "ends_at": "2030-01-01T10:30:00Z",
        },
    )
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "CONFLICT"
