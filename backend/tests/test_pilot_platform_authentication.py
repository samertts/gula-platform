"""pilot_platform had no authentication at all.

Found via scripts/tenant_mass_assignment_scan.py's create-shape sweep:
create_pilot/enroll_facility/decide_gate/record_deployment all build their
models from an unstructured `body: dict[str, Any]` with no lab_id
re-assertion. Checking reachability (this scan deliberately does not) showed
something more basic than a tenant-scope gap: unlike every sibling
national-platform router (ems, critical_care, public_health, command_center,
biomedical — all gated on system:admin), pilot_platform's router had no
`Depends(get_current_user)` or permission check anywhere, on a router that
IS wired into the live app (backend/app/factory.py). Every write endpoint
here accepted a fully unauthenticated request.

Fix: gate the whole router on system:admin, matching every sibling
national-platform router exactly — not a new rule invented for this one.
"""
from __future__ import annotations


def _valid_payload(lab_id: int) -> dict:
    # lab_id is NOT NULL on pilot_programs (it extends TenantEntity) and
    # nothing derives it server-side — only system:admin (master_admin) can
    # reach this endpoint at all, and master_admin choosing which lab a
    # national pilot targets is the intended cross-tenant use of this
    # field, not a gap: the actual defect this file fixes is the missing
    # authentication, not the client-supplied lab_id.
    return {"module_name": "lab_results", "version": "1.0.0", "lab_id": lab_id}


def test_create_pilot_rejects_an_unauthenticated_request(client):
    resp = client.post("/pilot-platform/pilots", json={"module_name": "lab_results", "version": "1.0.0"})
    assert resp.status_code in (401, 403)


def test_create_pilot_rejects_a_caller_without_system_admin(client, make_lab, make_lab_user):
    from tests.conftest import auth_headers

    lab = make_lab()
    admin = make_lab_user(lab.id, role="admin")

    resp = client.post(
        "/pilot-platform/pilots",
        json=_valid_payload(lab.id),
        headers=auth_headers(admin.id, lab.id, role="admin"),
    )
    assert resp.status_code == 403


def test_create_pilot_allows_a_system_admin_caller(client, make_lab, make_lab_user):
    from tests.conftest import auth_headers

    lab = make_lab()
    master = make_lab_user(lab.id, role="master_admin")

    resp = client.post(
        "/pilot-platform/pilots",
        json=_valid_payload(lab.id),
        headers=auth_headers(master.id, lab.id, role="master_admin"),
    )
    assert resp.status_code == 201, resp.text
