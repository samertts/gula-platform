"""verify_test_result no longer trusts a client-supplied verified_by field.

The request body used to name the verifying clinician (TestResultVerifyRequest
.verified_by), so the single most authority-bearing field on a verified
clinical result — who attested it — was whatever string the caller sent.
Any caller permitted to verify at all (LAB/DOCTOR/ADMIN) could attribute the
verification to an arbitrary name, real or fabricated. Abu Ali's branch
independently closed this same gap (NR-144); ported the same fix here for
this branch's own nhop-platform copy — verified_by is now read from the
server-established trusted context (actor_id), and the request schema is
emptied out (kept, with extra="forbid", so an old client sending the field
is rejected rather than silently ignored).
"""
from __future__ import annotations


def test_verified_by_comes_from_trusted_context_not_request_body(
    app_client, make_citizen, make_lab, make_result
):
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(s, health_id="HID-VERIFY-1")
        lab = make_lab(s)
        row = make_result(s, citizen_id=citizen.id, lab_id=lab.id)
        result_id = str(row.id)

    resp = client.put(
        f"/v1/test-results/{result_id}/verify",
        json={},
        headers={"X-Role": "ADMIN", "X-Actor-Id": "real-caller-id"},
    )
    assert resp.status_code == 200
    assert resp.json()["verified_by"] == "real-caller-id"


def test_body_supplied_verified_by_has_no_effect(
    app_client, make_citizen, make_lab, make_result
):
    """The route no longer declares a body parameter at all, so an old
    client still sending verified_by is simply ignored — the recorded
    verifier is still the trusted-context actor id, never the attacker-
    supplied name in the body."""
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(s, health_id="HID-VERIFY-2")
        lab = make_lab(s)
        row = make_result(s, citizen_id=citizen.id, lab_id=lab.id)
        result_id = str(row.id)

    resp = client.put(
        f"/v1/test-results/{result_id}/verify",
        json={"verified_by": "attacker-supplied-name"},
        headers={"X-Role": "ADMIN", "X-Actor-Id": "real-caller-id"},
    )
    assert resp.status_code == 200
    assert resp.json()["verified_by"] == "real-caller-id"
