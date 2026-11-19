"""F2 closure proof: create_test_result() no longer trusts payload.lab_id
as the sole authority for which lab a result is attributed to.

This used to be a broken object-level-authorization (BOLA/IDOR) gap: a
LAB-role caller could attribute a clinical result to any *other* active lab
in the system, not only their own, corrupting which lab is accountable for
it — `db.query(Lab).filter(Lab.id == payload.lab_id)` selected the lab
purely from the request body, with nothing checking the caller's own
affiliation.

The fix cross-checks `payload.lab_id` against the trusted context's
`lab_id` for the LAB role specifically (ADMIN stays platform-wide,
unchanged — see app/api/v1/test_results.py's module docstring and
app/core/trusted_context.py). Tests here use conftest's X-Lab-Id legacy
test header, which the app_client identity shim maps onto the trusted
context's lab_id for LAB-role callers.
"""
from __future__ import annotations


def test_lab_staff_can_attribute_a_result_to_their_own_lab(
    app_client, make_citizen, make_lab
):
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(s, health_id="HID-F2-OWN")
        own_lab = make_lab(s, name="مختبري الحقيقي")
        citizen_hid = citizen.health_id
        own_lab_id = str(own_lab.id)

    resp = client.post(
        "/v1/test-results/",
        json={
            "health_id": citizen_hid,
            "lab_id": own_lab_id,
            "test_code": "HGB",
            "test_name": "Hemoglobin",
            "value_numeric": 13.0,
        },
        headers={"X-Role": "LAB", "X-Actor-Id": "lab-caller-1", "X-Lab-Id": own_lab_id},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["lab_id"] == own_lab_id


def test_lab_staff_cannot_attribute_a_result_to_an_unrelated_lab(
    app_client, make_citizen, make_lab
):
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(s, health_id="HID-F2-BOLA")
        my_lab = make_lab(s, name="مختبري")
        other_lab = make_lab(s, name="مختبر لا علاقة له بالمتصل")
        citizen_hid = citizen.health_id
        my_lab_id = str(my_lab.id)
        other_lab_id = str(other_lab.id)

    resp = client.post(
        "/v1/test-results/",
        json={
            "health_id": citizen_hid,
            "lab_id": other_lab_id,  # not the caller's own lab
            "test_code": "HGB",
            "test_name": "Hemoglobin",
            "value_numeric": 13.0,
        },
        headers={"X-Role": "LAB", "X-Actor-Id": "lab-caller-2", "X-Lab-Id": my_lab_id},
    )
    assert resp.status_code == 403

    # No side effect: no result was created against either lab.
    with Session() as s:
        from app.models.citizen import Citizen
        from app.models.test_result import TestResult

        c = s.query(Citizen).filter(Citizen.health_id == citizen_hid).first()
        count = s.query(TestResult).filter(TestResult.citizen_id == c.id).count()
        assert count == 0


def test_admin_role_keeps_platform_wide_scope(app_client, make_citizen, make_lab):
    """The fix must not have over-corrected: ADMIN is a platform role and
    must still be able to attribute a result to any lab, matching
    backend/app's own platform_roles pattern (security/rbac.py)."""
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(s, health_id="HID-F2-ADMIN")
        other_lab = make_lab(s, name="أي مختبر")
        citizen_hid = citizen.health_id
        other_lab_id = str(other_lab.id)

    resp = client.post(
        "/v1/test-results/",
        json={
            "health_id": citizen_hid,
            "lab_id": other_lab_id,
            "test_code": "HGB",
            "test_name": "Hemoglobin",
            "value_numeric": 13.0,
        },
        headers={"X-Role": "ADMIN"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["lab_id"] == other_lab_id
