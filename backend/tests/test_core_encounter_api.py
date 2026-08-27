from __future__ import annotations

from app.clinical.appointments.models import CoreAppointment
from app.clinical.encounters.models import CoreClinicalNote, CoreEncounter, CoreEncounterQueueEntry
from app.identity.models.audit import IdentityAuditEntry

from .test_core_appointment_api import _create_slot

pytest_plugins = ("tests.test_core_appointment_api",)


def _confirmed_appointment(client, context, key="encounter-appointment"):
    workspace = context["workspace"]
    slot = _create_slot(client, context, key=f"{key}-slot")
    requested = client.post(
        "/api/v1/appointments",
        headers={"Idempotency-Key": f"{key}-request"},
        json={"workspace_id": workspace.id, "patient_person_id": context["person"].id, "slot_id": slot["id"], "purpose": "TREATMENT"},
    )
    assert requested.status_code == 201, requested.text
    confirmed = client.post(
        f"/api/v1/appointments/{requested.json()['id']}/confirm?workspace_id={workspace.id}",
        headers={"Idempotency-Key": f"{key}-confirm", "If-Match": '"1"'},
        json={"reason": "Synthetic clinical visit"},
    )
    assert confirmed.status_code == 200, confirmed.text
    return confirmed.json()


def test_checkin_encounter_note_sign_and_amend_flow(client, appointment_context):
    context = appointment_context
    workspace = context["workspace"]
    appointment = _confirmed_appointment(client, context)

    checked_in = client.post(
        "/api/v1/encounters/check-in",
        headers={"Idempotency-Key": "checkin-1"},
        json={"appointment_id": appointment["id"], "workspace_id": workspace.id},
    )
    assert checked_in.status_code == 201, checked_in.text
    encounter = checked_in.json()
    assert encounter["status"] == "CHECKED_IN"

    replay = client.post(
        "/api/v1/encounters/check-in",
        headers={"Idempotency-Key": "checkin-1"},
        json={"appointment_id": appointment["id"], "workspace_id": workspace.id},
    )
    assert replay.status_code == 201
    assert replay.json()["id"] == encounter["id"]

    started = client.post(
        f"/api/v1/encounters/{encounter['id']}/start",
        headers={"Idempotency-Key": "encounter-start-1", "If-Match": '"1"'},
        json={"workspace_id": workspace.id},
    )
    assert started.status_code == 200, started.text
    assert started.json()["status"] == "IN_PROGRESS"

    note = client.post(
        f"/api/v1/encounters/{encounter['id']}/notes",
        headers={"Idempotency-Key": "note-create-1"},
        json={"encounter_id": encounter["id"], "workspace_id": workspace.id, "chief_complaint": "Synthetic cough", "assessment": "Synthetic assessment"},
    )
    assert note.status_code == 201, note.text
    note_body = note.json()
    assert note_body["status"] == "DRAFT"
    assert note_body["version"] == 1

    completed_note = client.post(
        f"/api/v1/clinical-notes/{note_body['id']}/complete",
        headers={"Idempotency-Key": "note-complete-1", "If-Match": '"1"'},
        json={"workspace_id": workspace.id},
    )
    assert completed_note.status_code == 200, completed_note.text
    assert completed_note.json()["status"] == "COMPLETED"

    signed = client.post(
        f"/api/v1/clinical-notes/{note_body['id']}/sign",
        headers={"Idempotency-Key": "note-sign-1", "If-Match": '"2"'},
        json={"workspace_id": workspace.id},
    )
    assert signed.status_code == 200, signed.text
    assert signed.json()["status"] == "SIGNED"

    amended = client.post(
        f"/api/v1/clinical-notes/{note_body['id']}/amend",
        headers={"Idempotency-Key": "note-amend-1"},
        json={"workspace_id": workspace.id, "reason": "Corrected synthetic history", "history": "Updated synthetic history"},
    )
    assert amended.status_code == 200, amended.text
    assert amended.json()["status"] == "AMENDED"
    assert amended.json()["version"] == 4
    assert amended.json()["supersedes_id"] == note_body["id"]

    completed = client.post(
        f"/api/v1/encounters/{encounter['id']}/complete",
        headers={"Idempotency-Key": "encounter-complete-1", "If-Match": '"2"'},
        json={"workspace_id": workspace.id},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "COMPLETED"

    db = context["db"]
    assert db.query(CoreEncounter).filter(CoreEncounter.id == encounter["id"]).one().status == "COMPLETED"
    assert db.query(CoreEncounterQueueEntry).filter(CoreEncounterQueueEntry.encounter_id == encounter["id"]).one().status == "COMPLETED"
    assert db.query(CoreClinicalNote).filter(CoreClinicalNote.note_id == note_body["note_id"]).count() == 2
    events = {row.event_type for row in db.query(IdentityAuditEntry).all()}
    assert {"ENCOUNTER_CHECKED_IN", "NOTE_CREATED", "NOTE_SIGNED", "NOTE_AMENDED"}.issubset(events)


def test_encounter_rejects_stale_version_and_cross_workspace_idor(client, appointment_context):
    context = appointment_context
    workspace = context["workspace"]
    appointment = _confirmed_appointment(client, context, key="encounter-negative")
    checked_in = client.post(
        "/api/v1/encounters/check-in",
        headers={"Idempotency-Key": "checkin-negative"},
        json={"appointment_id": appointment["id"], "workspace_id": workspace.id},
    )
    assert checked_in.status_code == 201
    encounter_id = checked_in.json()["id"]
    stale = client.post(
        f"/api/v1/encounters/{encounter_id}/start",
        headers={"Idempotency-Key": "encounter-stale", "If-Match": '"9"'},
        json={"workspace_id": workspace.id},
    )
    assert stale.status_code == 409
    assert stale.json()["code"] == "VERSION_CONFLICT"
    denied = client.get(f"/api/v1/encounters/{encounter_id}?workspace_id={'Z' * 26}")
    assert denied.status_code == 403
    assert denied.json()["code"] == "FORBIDDEN"


def test_signed_note_cannot_be_directly_patched(client, appointment_context):
    context = appointment_context
    workspace = context["workspace"]
    appointment = _confirmed_appointment(client, context, key="encounter-immutable")
    checked_in = client.post("/api/v1/encounters/check-in", headers={"Idempotency-Key": "checkin-immutable"}, json={"appointment_id": appointment["id"], "workspace_id": workspace.id})
    started = client.post(f"/api/v1/encounters/{checked_in.json()['id']}/start", headers={"Idempotency-Key": "start-immutable", "If-Match": '"1"'}, json={"workspace_id": workspace.id})
    note = client.post(f"/api/v1/encounters/{checked_in.json()['id']}/notes", headers={"Idempotency-Key": "note-immutable"}, json={"encounter_id": checked_in.json()["id"], "workspace_id": workspace.id, "plan": "Synthetic plan"})
    assert all(response.status_code in {200, 201} for response in (checked_in, started, note))
    note_id = note.json()["id"]
    complete = client.post(f"/api/v1/clinical-notes/{note_id}/complete", headers={"Idempotency-Key": "complete-immutable", "If-Match": '"1"'}, json={"workspace_id": workspace.id})
    sign = client.post(f"/api/v1/clinical-notes/{note_id}/sign", headers={"Idempotency-Key": "sign-immutable", "If-Match": '"2"'}, json={"workspace_id": workspace.id})
    assert complete.status_code == 200 and sign.status_code == 200
    patched = client.patch(f"/api/v1/clinical-notes/{note_id}", headers={"Idempotency-Key": "patch-immutable", "If-Match": '"3"'}, json={"workspace_id": workspace.id, "plan": "Silent overwrite"})
    assert patched.status_code == 409
    assert patched.json()["code"] == "CLINICAL_NOTE_IMMUTABLE"
