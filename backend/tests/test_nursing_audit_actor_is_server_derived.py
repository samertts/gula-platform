"""NR-160 — the nursing audit row records the actor's role, from the server.

THE DEFECT
----------
Fifteen audit-writing nursing services never passed `user_role` to `log_action`
at all, so `audit_logs.user_role` was NULL for every nursing action ever
recorded: all eight care-coordination actions, all three medication-administration
actions, and patient assignment, unassignment and task creation.

This is a different failure from NR-158 and NR-159, and a less dishonest one. A
NULL role is an honest "unknown"; a hard-coded literal is a false statement that
reads as fact. But the consequence for a reader is the same: the audit trail
cannot answer the question it exists to answer — was this action within the
actor's authority? — because nothing in the row says what the actor's authority
was.

WHY THE MEDICATION CLUSTER MATTERS MOST
----------------------------------------
`record_five_rights_attestation`, `record_administration` and
`electronic_signature` are evidence records. An electronic signature whose row
does not say what the signer was permitted to do is a signature without a
capacity, which is most of what a signature is for. The same holds for a
five-rights attestation, which the platform already documents as an ATTESTATION
rather than a verification (NR-102) — its whole evidential value rests on who
attested.

WHERE THE ROLE COMES FROM
-------------------------
`current_user.role`. `get_current_user` does not read the role from the token: it
calls `resolve_token_subject(db, payload)`, which loads the live subject row, and
the token's `perm_ver` is then checked against the authoritative permission
version and the request refused on a mismatch. The role is a database column of
the authenticated subject, re-read per request.

Every one of the fifteen services is reached from exactly one place —
`app/nursing/routes.py` — and `current_user` is in scope at all fourteen call
sites there (`assign_patient` and `unassign_patient` share one route pair, and
`create_task` is called once), so no caller had to invent a role.

WHY THE PARAMETER IS KEYWORD-ONLY AND HAS NO DEFAULT
-----------------------------------------------------
Declared after `*` with no default, so a caller that forgets it raises TypeError
immediately. A default would restore the defect in a worse form: instead of an
honest NULL the row would carry a plausible, wrong role.
"""

from __future__ import annotations

import inspect
from pathlib import Path

from app.nursing import coordination as coordination_module
from app.nursing import services as services_module
from app.nursing.coordination import CareCoordinatorService
from app.nursing.medication import MedicationAdminService
from app.nursing.services import NursingService

#: Every nursing service that writes an audit row naming an actor.
AUDIT_WRITERS = (
    CareCoordinatorService.send_physician_message,
    CareCoordinatorService.request_lab_collection,
    CareCoordinatorService.coordinate_radiology,
    CareCoordinatorService.coordinate_pharmacy,
    CareCoordinatorService.manage_referral,
    CareCoordinatorService.plan_discharge,
    CareCoordinatorService.family_communication,
    CareCoordinatorService.home_care_handover,
    MedicationAdminService.record_five_rights_attestation,
    MedicationAdminService.record_administration,
    MedicationAdminService.electronic_signature,
    NursingService.assign_patient,
    NursingService.unassign_patient,
    NursingService.create_task,
)

NURSING_SOURCES = (
    "app/nursing/coordination.py",
    "app/nursing/medication.py",
    "app/nursing/services.py",
)


def test_a_actor_role_is_required_and_keyword_only():
    """The structural control, over all fourteen services at once."""
    for fn in AUDIT_WRITERS:
        params = inspect.signature(fn).parameters
        assert "actor_role" in params, f"{fn.__qualname__} does not take actor_role"
        param = params["actor_role"]
        assert param.kind is inspect.Parameter.KEYWORD_ONLY, (
            f"{fn.__qualname__}'s actor_role is positional. Every one of these "
            "services already takes db, lab_id and user_id positionally; a fourth "
            "positional string is how a description ended up in an integer column "
            "(NR-156)"
        )
        assert param.default is inspect.Parameter.empty, (
            f"{fn.__qualname__}'s actor_role has a default ({param.default!r}). A "
            "default replaces an honest NULL with a plausible, wrong role — worse "
            "than the defect NR-160 fixes"
        )


def test_b_no_nursing_audit_site_omits_the_role():
    """The ratchet: every log_action in the nursing package names a role.

    Read from source, non-comment lines only — a substring search would accept a
    commented-out occurrence. This counts sites rather than naming them, so a
    NEW audit call added without a role fails here too.
    """
    import ast

    offenders = []
    for rel in NURSING_SOURCES:
        path = Path(services_module.__file__).parent / Path(rel).name
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = (node.func.id if isinstance(node.func, ast.Name)
                    else getattr(node.func, "attr", None))
            if name != "log_action":
                continue
            has_role = (any(kw.arg == "user_role" for kw in node.keywords)
                        or len(node.args) >= 6)
            if not has_role:
                offenders.append(f"{Path(rel).name}:{node.lineno}")

    assert not offenders, (
        f"{len(offenders)} nursing audit sites still write a NULL actor role: "
        f"{offenders}"
    )


def test_c_the_role_written_is_the_one_passed_in():
    """No nursing audit site substitutes a constant for the argument.

    test_b would pass if a site wrote `user_role="nurse"`. That is the NR-158 and
    NR-159 defect, and this is the ratchet against introducing it here while
    closing NR-160.
    """
    import ast

    offenders = []
    for rel in NURSING_SOURCES:
        path = Path(services_module.__file__).parent / Path(rel).name
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = (node.func.id if isinstance(node.func, ast.Name)
                    else getattr(node.func, "attr", None))
            if name != "log_action":
                continue
            for kw in node.keywords:
                if kw.arg == "user_role" and isinstance(kw.value, ast.Constant):
                    offenders.append(
                        f"{Path(rel).name}:{node.lineno} -> {kw.value.value!r}")

    assert not offenders, (
        f"a nursing audit site hard-codes a role instead of using the actor's: "
        f"{offenders}"
    )


def test_d_every_nursing_route_passes_the_authenticated_subjects_role():
    """The wiring, read from source.

    A correct signature proves nothing if the route feeds it a literal. Every
    `actor_role=` in app/nursing/routes.py must read `current_user.role`, and
    there must be one per audit-writing service call site.
    """
    import re

    from app.nursing import routes as nursing_routes

    source = Path(nursing_routes.__file__).read_text(encoding="utf-8")
    live = "\n".join(
        ln for ln in source.splitlines() if not ln.lstrip().startswith("#")
    )
    arguments = re.findall(r"actor_role\s*=\s*([^,\n)]+)", live)

    assert arguments, "app/nursing/routes.py passes no actor_role at all"
    assert all(arg.strip() == "current_user.role" for arg in arguments), (
        f"a nursing route supplies a role from somewhere other than the "
        f"authenticated subject: {sorted(set(arguments))}"
    )
    assert len(arguments) == len(AUDIT_WRITERS), (
        f"{len(arguments)} route call sites pass actor_role but there are "
        f"{len(AUDIT_WRITERS)} audit-writing services; one is unwired"
    )


def test_e_the_coordination_services_all_carry_the_parameter():
    """A count, so that a newly added coordination action is not silently exempt.

    CareCoordinatorService is the cluster most likely to grow: it is eight
    near-identical methods, and a ninth written by copying one of them would
    inherit the fix only if it was copied after this commit.
    """
    public = [
        name for name, member in vars(CareCoordinatorService).items()
        if isinstance(member, staticmethod) and not name.startswith("_")
    ]
    assert len(public) >= 8, public

    missing = [
        name for name in public
        if "actor_role" not in inspect.signature(
            getattr(coordination_module.CareCoordinatorService, name)).parameters
    ]
    assert not missing, (
        f"these CareCoordinatorService methods do not take actor_role: {missing}"
    )
