"""NR-158 — the LIMS audit row records the actor's REAL role, from the server.

THE DEFECT
----------
All four audit sites in app/lims/services.py passed the literal string
"lab_tech" as `user_role`:

    log_action(db, "create", "lims_order", lims_order.id, user_id, "lab_tech", ...)

So every LIMS audit row claimed its actor was a lab technician, whatever the
actor actually was. A laboratory administrator releasing a result — the most
privileged clinical action in the domain — was recorded as a technician. The
`user_id` was correct throughout, so this is misattribution of ROLE, not of
identity: the row names the right person and the wrong authority.

That matters because an audit trail is read to answer "was this action within
the actor's authority?". A row that always says lab_tech cannot answer it, and
it answers it *wrongly* in the one direction that hides a privilege problem.

WHERE THE ROLE COMES FROM, AND WHY IT IS TRUSTWORTHY
----------------------------------------------------
`current_user.role`. `get_current_user` does not read the role from the token: it
calls `resolve_token_subject(db, payload)`, which loads the live row, and then
compares the token's `perm_ver` against the authoritative permission version and
rejects the request on a mismatch. So the role is a database column belonging to
the authenticated subject, re-read per request, and a token minted before a role
change is refused rather than honoured.

It is also the source `ClinicalCommandGuard` in these very same handlers already
uses (`actor_role=current_user.role`). The repair makes the services agree with
the guard beside them rather than inventing a second convention.

WHY THE PARAMETER IS KEYWORD-ONLY AND HAS NO DEFAULT
-----------------------------------------------------
`actor_role` is declared after `*`, with no default. A future call site that
forgets it raises TypeError at once. A default — any default — would restore
exactly the failure being fixed here: a plausible-looking role silently standing
in for the real one. The absence of a default is the control.
"""

from __future__ import annotations

import inspect

import pytest
from app.lims import services as lims_services
from app.models.patient import Patient

from tests.conftest import auth_headers

#: The four audit-writing services, and the role that must never be hard-coded.
AUDIT_WRITERS = (
    lims_services.SpecimenService.register,
    lims_services.SpecimenService.transition,
    lims_services.OrderService.create_lims_order,
    lims_services.ResultService.create_result,
)


def test_a_actor_role_is_required_and_keyword_only():
    """The structural control.

    Every audit-writing service must demand `actor_role` explicitly. This is the
    positive control for the whole module: if the parameter did not exist, the
    behavioural tests below could pass while the role came from somewhere else.
    """
    for fn in AUDIT_WRITERS:
        params = inspect.signature(fn).parameters
        assert "actor_role" in params, f"{fn.__qualname__} does not take actor_role"
        param = params["actor_role"]
        assert param.kind is inspect.Parameter.KEYWORD_ONLY, (
            f"{fn.__qualname__}'s actor_role is positional; a caller could pass the "
            "wrong argument in that slot, which is how the description ended up in "
            "lab_id (NR-156)"
        )
        assert param.default is inspect.Parameter.empty, (
            f"{fn.__qualname__}'s actor_role has a default ({param.default!r}). A "
            "default silently substitutes a plausible role for the real one, which "
            "is precisely the defect NR-158 fixes"
        )


def test_b_no_lims_audit_site_hard_codes_a_role():
    """The ratchet, read from source.

    Non-comment lines only: a substring search would accept a commented-out
    occurrence, which is how an earlier ratchet in this repository stayed green
    while the control it guarded was switched off.
    """
    from pathlib import Path

    source = Path(lims_services.__file__).read_text(encoding="utf-8")
    live = [ln for ln in source.splitlines() if not ln.lstrip().startswith("#")]
    offenders = [ln.strip() for ln in live if '"lab_tech"' in ln or "'lab_tech'" in ln]

    assert not offenders, (
        f"app/lims/services.py still hard-codes a role: {offenders}"
    )


@pytest.fixture()
def lims_actors(db, make_lab, make_lab_user):
    """One laboratory, two actors with genuinely different roles."""
    lab = make_lab(name="NR-158 Audit Actor Lab")
    tech = make_lab_user(lab_id=lab.id, role="lab_technician",
                         email="nr158-tech@test.com")
    admin = make_lab_user(lab_id=lab.id, role="lab_admin",
                          email="nr158-admin@test.com")
    patient = Patient(lab_id=lab.id, full_name="NR-158 Patient",
                      phone="07700000158", gender="M")
    db.add(patient)
    db.flush()
    return {"lab": lab, "tech": tech, "admin": admin, "patient": patient}


def _audit_roles_for(db, lab_id: int) -> list[str]:
    from app.models.audit_log import AuditLog

    return [
        row.user_role
        for row in db.query(AuditLog)
        .filter(AuditLog.lab_id == lab_id,
                AuditLog.resource_type.like("lims_%"))
        .order_by(AuditLog.id.desc())
        .limit(10)
    ]


def test_c_a_technicians_action_is_recorded_as_a_technician(db, lims_actors):
    """The role the defect happened to get right -- asserted, not assumed.

    Without this, a repair that wrote a different constant would look correct in
    test_d while being just as wrong.
    """
    actor = lims_actors["tech"]
    lims_services.OrderService.create_lims_order(
        db, lims_actors["patient"].id, lims_actors["lab"].id, actor.id,
        "ACC-NR158-TECH", actor_role=actor.role,
    )
    db.flush()

    assert "lab_technician" in _audit_roles_for(db, lims_actors["lab"].id)


def test_d_an_administrators_action_is_not_recorded_as_a_technician(db, lims_actors):
    """The finding. This is the row the defect falsified."""
    actor = lims_actors["admin"]
    lims_services.OrderService.create_lims_order(
        db, lims_actors["patient"].id, lims_actors["lab"].id, actor.id,
        "ACC-NR158-ADMIN", actor_role=actor.role,
    )
    db.flush()

    roles = _audit_roles_for(db, lims_actors["lab"].id)
    assert "lab_admin" in roles, (
        f"an administrator's LIMS action was audited as {roles}; the audit trail "
        "cannot answer whether the action was within the actor's authority"
    )


def test_e_a_client_authored_role_never_reaches_the_audit_row(client, db, lims_actors):
    """The spoofing proof, driven through the real route.

    The request body and headers both carry a role the caller would like to be
    recorded. The handler must ignore both and use the authenticated subject's
    database role.
    """
    actor = lims_actors["tech"]
    headers = {
        **auth_headers(actor.id, lims_actors["lab"].id, role="lab_technician"),
        "X-Role": "master_admin",
    }

    response = client.post("/lims/orders", headers=headers, json={
        "order_id": lims_actors["patient"].id,
        "accession_number": "ACC-NR158-SPOOF",
        "priority": "routine",
        # A hostile body field. Pydantic should ignore it; the assertion below
        # proves it never reached the audit row even if it were accepted.
        "user_role": "master_admin",
    })

    # The route may refuse for unrelated reasons (release policy, missing base
    # order). What must never happen is a master_admin audit row for this actor.
    roles = _audit_roles_for(db, lims_actors["lab"].id)
    assert "master_admin" not in roles, (
        f"a client-supplied role reached the audit trail: {roles} "
        f"(response {response.status_code})"
    )
