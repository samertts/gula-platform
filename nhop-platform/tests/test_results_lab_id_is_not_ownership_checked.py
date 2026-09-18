"""P1 characterization test — final cross-cutting forensic pass.

create_test_result() (test_results.py) takes `lab_id` straight from the
request body and uses it to select which lab authored the result
(`db.query(Lab).filter(Lab.id == payload.lab_id)`), with no check that the
caller is actually affiliated with that lab. This is a broken
object-level-authorization (BOLA/IDOR) gap: even a legitimately-scoped
LAB-role caller can attribute a result to any *other* active lab in the
system, not only their own — corrupting which lab is accountable for a
clinical result.

Root cause is the same missing identity stack as X-Role/X-Actor-Id (see
docs/engineering/MUSTAFA_PARALLEL_WORK_MAP.md finding #11): there is no
trusted per-caller lab_id to check `payload.lab_id` against, because
nothing in nhop-platform yet derives "which lab is this caller" from a
verified session. Not fixed here — a real fix requires that same
identity binding, which is out of scope per this pass's stop conditions
(would mean inventing a competing/partial auth mechanism ahead of the
real one).
"""
from __future__ import annotations


def test_lab_staff_can_attribute_a_result_to_an_unrelated_lab(
    app_client, make_citizen, make_lab, admin_headers
):
    client, Session = app_client
    with Session() as s:
        citizen = make_citizen(s, health_id="HID-BOLA-1")
        # Two unrelated labs; nothing associates the caller with either one.
        make_lab(s, name="مختبري الحقيقي")
        other_lab = make_lab(s, name="مختبر لا علاقة له بالمتصل")
        citizen_hid = citizen.health_id
        other_lab_id = str(other_lab.id)

    resp = client.post(
        "/v1/test-results/",
        json={
            "health_id": citizen_hid,
            "lab_id": other_lab_id,  # not the caller's own lab — nothing checks this
            "test_code": "HGB",
            "test_name": "Hemoglobin",
            "value_numeric": 13.0,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["lab_id"] == other_lab_id
