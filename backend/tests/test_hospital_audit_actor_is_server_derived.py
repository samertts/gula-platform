"""NR-159 — the hospital audit row records the actor's REAL role, from the server.

THE DEFECT
----------
Five audit sites in app/services/hospital_service.py passed the literal string
'hospital_staff' as `user_role`:

    log_action(db, action="bed.assign", ..., user_role='hospital_staff', ...)

Every bed assignment, discharge, transfer, operation-theater status change and
surgical safety checklist therefore claimed its actor was generic hospital
staff. These are the five most consequential physical-custody actions in the
hospital domain: they move a patient between beds and put a theater into use
for a named surgery. The `user_id` was correct throughout, so the row names the
right person and the wrong authority — misattribution of ROLE, not identity.

'hospital_staff' is worse than a wrong role: it is not a role at all. It appears
in neither of the platform's role catalogues —
`shared.rbac.EXTENDED_VALID_ROLES` (the set `LabUser.role` is validated
against) nor the ABAC enum in `app/models/authorization.py`. So the audit rows
for these five actions cannot be joined to any role definition, and a question
as basic as "may that role move a patient?" has no answer for them.

This is the same defect class as NR-158 (app/lims/services.py, "lab_tech"), found
by the AST census of all 188 `log_action` call sites in `app/`.

WHERE THE ROLE COMES FROM, AND WHY IT IS TRUSTWORTHY
----------------------------------------------------
`current_user.role`. `get_current_user` does not take the role from the token: it
calls `resolve_token_subject(db, payload)`, which loads the live row, then
compares the token's `perm_ver` against the authoritative permission version and
refuses the request on a mismatch. The role is therefore a database column
belonging to the authenticated subject, re-read per request; a token minted
before a role change is rejected rather than honoured.

It is also the source the `ClinicalCommandGuard` wrapping these very handlers
(`_run_hospital_command`) already uses, so the repair makes the service agree
with the guard beside it instead of inventing a second convention.

WHY THE PARAMETER IS KEYWORD-ONLY AND HAS NO DEFAULT
-----------------------------------------------------
`actor_role` is declared after `*` with no default, so a call site that forgets
it raises TypeError at once — which is exactly what happened to
tests/test_emergency_surgery_workflow_p0.py when this repair landed, and is the
control working. Any default would reinstate the defect being fixed: a
plausible-looking role silently standing in for the real one.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
from app.hospital.models import Bed
from app.models.patient import Patient
from app.services import hospital_service as hospital_module
from app.services.hospital_service import HospitalService

#: Every hospital service that writes an audit row naming an actor.
AUDIT_WRITERS = (
    HospitalService.assign_bed,
    HospitalService.discharge_bed,
    HospitalService.transfer_bed,
    HospitalService.update_operation_theater_status,
    HospitalService.complete_surgical_safety_checklist,
)


def test_a_actor_role_is_required_and_keyword_only():
    """The structural control.

    This is the positive control for the module: if the parameter did not exist,
    the behavioural tests below could pass while the role arrived from somewhere
    else entirely.
    """
    for fn in AUDIT_WRITERS:
        params = inspect.signature(fn).parameters
        assert "actor_role" in params, f"{fn.__qualname__} does not take actor_role"
        param = params["actor_role"]
        assert param.kind is inspect.Parameter.KEYWORD_ONLY, (
            f"{fn.__qualname__}'s actor_role is positional. A positional role slot is "
            "how a description ended up in an integer lab_id column (NR-156)"
        )
        assert param.default is inspect.Parameter.empty, (
            f"{fn.__qualname__}'s actor_role has a default ({param.default!r}). A "
            "default substitutes a plausible role for the real one, which is the "
            "defect NR-159 fixes"
        )


def test_b_no_hospital_audit_site_hard_codes_a_role():
    """The ratchet, read from source, non-comment lines only.

    A plain substring search would accept a commented-out occurrence — which is
    how an earlier ratchet in this repository stayed green while the control it
    guarded was switched off.
    """
    source = Path(hospital_module.__file__).read_text(encoding="utf-8")
    live = [ln for ln in source.splitlines() if not ln.lstrip().startswith("#")]
    offenders = [
        ln.strip()
        for ln in live
        if '"hospital_staff"' in ln or "'hospital_staff'" in ln
    ]

    assert not offenders, (
        f"app/services/hospital_service.py still hard-codes a role: {offenders}"
    )


def test_c_hospital_staff_is_not_a_role_in_either_catalogue():
    """Why the old literal could never have been right for anyone.

    Pinned as a test because the claim in the docstring above is load-bearing: if
    'hospital_staff' were ever added to a catalogue, the reasoning for this
    finding would change and this test would say so.
    """
    from shared.rbac import EXTENDED_VALID_ROLES

    assert "hospital_staff" not in EXTENDED_VALID_ROLES

    from app.models.authorization import UserTypeEnum

    assert "hospital_staff" not in {member.value for member in UserTypeEnum}


@pytest.fixture()
def hospital_actors(db, make_lab, make_lab_user):
    """One hospital tenant, two actors whose roles genuinely differ."""
    lab = make_lab(name="NR-159 Hospital")
    staff = make_lab_user(lab_id=lab.id, role="technician",
                          email="nr159-staff@test.com")
    admin = make_lab_user(lab_id=lab.id, role="lab_admin",
                          email="nr159-admin@test.com")
    patient = Patient(lab_id=lab.id, full_name="NR-159 Patient",
                      phone="07700000159", gender="F")
    db.add(patient)
    db.flush()
    return {"lab": lab, "staff": staff, "admin": admin, "patient": patient}


def _available_bed(db, lab_id: int, number: str) -> Bed:
    bed = Bed(lab_id=lab_id, room_id=1, bed_number=number, status="available")
    db.add(bed)
    db.flush()
    return bed


def _audit_roles_for(db, lab_id: int) -> list[str]:
    from app.models.audit_log import AuditLog

    return [
        row.user_role
        for row in db.query(AuditLog)
        .filter(AuditLog.lab_id == lab_id,
                AuditLog.resource_type == "hospital_bed")
        .order_by(AuditLog.id.desc())
        .limit(10)
    ]


def test_d_a_technicians_bed_assignment_is_recorded_as_a_technician(db, hospital_actors):
    """The role a wrong constant might coincidentally resemble -- asserted, not assumed.

    Without this, a repair that swapped one constant for another would look
    correct in test_e while being just as wrong.
    """
    actor = hospital_actors["staff"]
    bed = _available_bed(db, hospital_actors["lab"].id, "NR159-A")

    HospitalService.assign_bed(
        db,
        hospital_actors["lab"].id,
        actor.id,
        bed.id,
        hospital_actors["patient"].id,
        actor_role=actor.role,
        expected_version=bed.version,
    )
    db.flush()

    assert "technician" in _audit_roles_for(db, hospital_actors["lab"].id)


def test_e_an_administrators_bed_assignment_is_not_recorded_as_generic_staff(
    db, hospital_actors,
):
    """The finding. This is the row the defect falsified.

    A laboratory administrator taking physical custody of a patient must be
    auditable as an administrator, because that is the fact a reviewer needs in
    order to decide whether the action was within the actor's authority.
    """
    actor = hospital_actors["admin"]
    bed = _available_bed(db, hospital_actors["lab"].id, "NR159-B")

    HospitalService.assign_bed(
        db,
        hospital_actors["lab"].id,
        actor.id,
        bed.id,
        hospital_actors["patient"].id,
        actor_role=actor.role,
        expected_version=bed.version,
    )
    db.flush()

    roles = _audit_roles_for(db, hospital_actors["lab"].id)
    assert "lab_admin" in roles, (
        f"an administrator's bed assignment was audited as {roles}; the audit "
        "trail cannot answer whether the action was within the actor's authority"
    )
    assert "hospital_staff" not in roles


def test_f_every_route_passes_the_authenticated_subjects_role(db):
    """The wiring, read from source.

    A correct service signature proves nothing if the route feeds it a literal.
    Every `actor_role=` argument in app/routes/hospital.py must read
    `current_user.role`: one per audit-writing service call, plus the one the
    `ClinicalCommandGuard` in `_run_hospital_command` has always taken. The guard
    is counted deliberately -- it is the precedent this repair follows, and its
    presence is what makes a second, divergent role convention in the service
    layer indefensible.
    """
    import re

    from app.routes import hospital as hospital_routes

    source = Path(hospital_routes.__file__).read_text(encoding="utf-8")
    live = "\n".join(
        ln for ln in source.splitlines() if not ln.lstrip().startswith("#")
    )
    arguments = re.findall(r"actor_role\s*=\s*([^,\n]+)", live)

    assert arguments, "app/routes/hospital.py passes no actor_role at all"
    assert all(arg.strip() == "current_user.role" for arg in arguments), (
        f"a hospital route supplies a role from somewhere other than the "
        f"authenticated subject: {arguments}"
    )
    expected = len(AUDIT_WRITERS) + 1  # + ClinicalCommandGuard
    assert len(arguments) == expected, (
        f"{len(arguments)} actor_role arguments in app/routes/hospital.py; expected "
        f"{expected} ({len(AUDIT_WRITERS)} audit-writing services + the "
        "ClinicalCommandGuard). A shortfall means a call site is unwired"
    )
