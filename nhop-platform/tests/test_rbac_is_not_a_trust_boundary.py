"""Characterization tests for a known security gap in core/rbac.py.

require_roles() reads X-Role straight off the incoming request with no
verification against any session, token, or server-side identity — it is
client-asserted input, not authorization. These tests exist to PROVE that,
not to endorse it: they document the current, insecure behavior so that
(a) nobody mistakes the 401/403 gate added to citizens.py/test_results.py
for real access control, and (b) whoever wires nhop-platform to the real
JWT-backed auth stack (see docs/engineering/MUSTAFA_PARALLEL_WORK_MAP.md,
"X-Role is not a trust boundary") gets an immediate, loud test failure here
as a forcing function to update/replace this file — that's a feature of
this test file, not a bug to silence.

Do NOT copy this pattern to justify adding more require_roles(...) gates
elsewhere and calling it "authorization" — see the work map for why.
"""
from __future__ import annotations


def test_x_role_header_is_taken_at_face_value_with_no_corroboration(
    app_client, make_citizen
):
    """Identical request, zero authentication material, two different
    self-asserted roles -> two different authorization outcomes. If X-Role
    were being checked against anything server-side (a session, a token,
    a membership record), a bare unverified string could not by itself
    swing 403 -> 200."""
    client, Session = app_client
    with Session() as s:
        make_citizen(s, health_id="HID-SPOOF-1")

    denied = client.get("/v1/citizens/HID-SPOOF-1", headers={"X-Role": "CITIZEN"})
    assert denied.status_code == 403

    # Nothing else about the request changed — no token, no cookie, no
    # session, no prior login — only the client's own claim about its role.
    admitted = client.get("/v1/citizens/HID-SPOOF-1", headers={"X-Role": "ADMIN"})
    assert admitted.status_code == 200


def test_any_arbitrary_caller_can_self_declare_admin_and_write_pii(app_client):
    """A request with no prior authentication step at all — just an
    X-Role header the caller made up — can register a new citizen record.
    This is the concrete "client-controlled input directly grants
    authorization" failure mode: nothing about this request proves the
    caller is who X-Role claims."""
    client, _ = app_client

    resp = client.post(
        "/v1/citizens/register",
        json={"full_name": "لا يوجد مصادقة هنا"},
        headers={"X-Role": "ADMIN"},  # entirely self-asserted
    )
    assert resp.status_code == 201


def test_missing_role_header_is_the_only_thing_that_is_actually_enforced(app_client):
    """The one real guarantee this mechanism provides: SOME value must be
    present. It provides no guarantee about who supplied it or whether
    it's true."""
    client, _ = app_client

    resp = client.post("/v1/citizens/register", json={"full_name": "بلا رأس"})
    assert resp.status_code == 401
