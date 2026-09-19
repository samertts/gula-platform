"""NR-148 — the Master Patient Index has a scope rule now, and it is the right one.

THE MPI IS DELIBERATELY CROSS-TENANT; THAT WAS NEVER THE DEFECT.
Person/Identity is the canonical national subject; Patient and Citizen are
contextual roles on it. An index that stopped at a laboratory boundary
could not do the one job it exists for — recognizing that Lab A's patient
and Lab B's patient are the same person. `lab_id` on `canonical_patients`
is PROVENANCE, and the schema says so: nullable, ON DELETE SET NULL, no
(lab_id, ...) composite index — while `patients`, which IS tenant-owned,
carries ix_patients_lab_id and ix_patients_lab_phone.

The two defects were:

  1. `CanonicalPatient(**data.model_dump())` let the request body set
     lab_id, so a laboratory could file a canonical record under another
     laboratory's name. Provenance the client chooses is not provenance.
  2. Nothing separated callers who may act nationally from those who may
     not. Any authenticated user — a technician at one private lab —
     could search the entire national index by name/phone, read any
     canonical record, and MERGE two people's identities.

The fix (ported from an independently converged upstream fix for the same
finding, backend/app/services/mpi/scope.py) invents no new permission:
platform:view_stats is already held by exactly master_admin/ministry_admin/
province_admin and by no lab-scoped role, so it is read as the marker for
national scope.

Every denial below is paired with a positive control — a policy that
refused everything would satisfy the denials alone and look secure while
being broken.
"""
from __future__ import annotations

import pytest
from app.models.canonical_patient import CanonicalPatient, PatientLink
from app.services.mpi import scope


class _Actor:
    def __init__(self, role, lab_id=None):
        self.role = role
        self.lab_id = lab_id


def _actor(role, lab_id=None):
    return _Actor(role, lab_id)


@pytest.fixture()
def world(db, make_lab, make_lab_user):
    """Two labs, each with a user and a patient, plus three canonical records."""
    lab_a = make_lab(name="Lab A MPI")
    lab_b = make_lab(name="Lab B MPI")

    staff_a = make_lab_user(lab_a.id, role="lab_staff", email="mpi_staff_a@test.com")
    ministry = make_lab_user(lab_a.id, role="ministry_admin", email="mpi_ministry@test.com")

    from app.models.patient import Patient

    pat_a = Patient(lab_id=lab_a.id, full_name="Patient A", phone="07700000011")
    pat_b = Patient(lab_id=lab_b.id, full_name="Patient B", phone="07700000022")
    db.add_all([pat_a, pat_b])
    db.flush()

    # own_a: contributed by Lab A. linked_a: contributed by nobody, but
    # linked to Lab A's patient. foreign: Lab B's, unconnected to Lab A.
    own_a = CanonicalPatient(lab_id=lab_a.id, full_name="Contributed by A")
    linked_a = CanonicalPatient(lab_id=None, full_name="Linked to A's patient")
    foreign = CanonicalPatient(lab_id=lab_b.id, full_name="Belongs to B")
    db.add_all([own_a, linked_a, foreign])
    db.flush()
    db.add(PatientLink(patient_id=pat_a.id, canonical_id=linked_a.id, linkage_method="manual"))
    db.commit()

    return {
        "lab_a": lab_a, "lab_b": lab_b,
        "staff_a": staff_a, "ministry": ministry,
        "pat_a": pat_a, "pat_b": pat_b,
        "own_a": own_a, "linked_a": linked_a, "foreign": foreign,
    }


# ─── national scope is read from the existing matrix ────────────────────────

def test_national_scope_is_exactly_the_cross_lab_roles():
    """Positive control AND the definition, asserted rather than assumed."""
    national = {"master_admin", "ministry_admin", "province_admin"}
    lab_scoped = {"lab_staff", "lab_admin", "technician", "doctor", "staff",
                  "admin", "citizen"}

    for role in national:
        assert scope.has_national_scope(_actor(role)), f"{role} lost national scope"
    for role in lab_scoped:
        assert not scope.has_national_scope(_actor(role)), (
            f"{role} gained national scope over the patient index"
        )


def test_an_actor_with_no_role_has_no_scope():
    assert not scope.has_national_scope(_actor(None))
    assert not scope.has_national_scope(_actor(""))


# ─── provenance is server-derived ───────────────────────────────────────────

def test_provenance_comes_from_the_caller(world):
    """Server-derived, and never the body's. lab_users.lab_id is NOT NULL,
    so a national role carries a home lab too — provenance stays truthful
    for both kinds of caller, and the column is nullable because records
    can arrive from sources that are not a laboratory at all."""
    assert scope.provenance_lab_id(world["staff_a"]) == world["lab_a"].id
    assert scope.provenance_lab_id(world["ministry"]) == world["lab_a"].id
    assert scope.provenance_lab_id(_actor("lab_staff", None)) is None


def test_the_create_schema_cannot_carry_a_lab_id():
    """The body named the record's laboratory. It no longer has the field."""
    from app.routes.canonical_patient import CanonicalPatientCreate

    assert "lab_id" not in CanonicalPatientCreate.model_fields, (
        "CanonicalPatientCreate accepts lab_id again; the request body can "
        "forge provenance in the national index (NR-148)"
    )


# ─── visibility ─────────────────────────────────────────────────────────────

def test_a_lab_sees_a_record_it_contributed(db, world):
    assert scope.visible_canonical(db, world["own_a"].id, world["staff_a"]) is not None


def test_a_lab_sees_a_record_linked_to_its_own_patient(db, world):
    """The MPI's actual purpose, for a lab-scoped caller."""
    assert scope.visible_canonical(db, world["linked_a"].id, world["staff_a"]) is not None


def test_a_lab_does_not_see_an_unconnected_record(db, world):
    assert scope.visible_canonical(db, world["foreign"].id, world["staff_a"]) is None


def test_a_national_role_sees_every_record(db, world):
    """The ministry user's home lab is Lab A, so `foreign` proves the point:
    it is visible by ROLE, not because of any lab connection."""
    for key in ("own_a", "linked_a", "foreign"):
        assert scope.visible_canonical(db, world[key].id, world["ministry"]) is not None, (
            f"a ministry admin cannot see {key}; the index is unusable nationally"
        )


def test_absence_and_denial_are_indistinguishable(db, world):
    """Neither leaks which canonical ids exist."""
    denied = scope.visible_canonical(db, world["foreign"].id, world["staff_a"])
    missing = scope.visible_canonical(db, 999_999_999, world["staff_a"])
    assert denied is None and missing is None


# ─── national-only actions ──────────────────────────────────────────────────

@pytest.mark.parametrize("action", ["searching", "merging", "linking a citizen"])
def test_a_lab_caller_is_refused_national_actions(world, action):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        scope.require_national_scope(world["staff_a"], action)
    assert exc.value.status_code == 403

    scope.require_national_scope(world["ministry"], action)  # positive control


# ─── linking someone else's patient ─────────────────────────────────────────

def test_a_lab_may_link_its_own_patient(db, world):
    scope.require_own_patient(db, world["pat_a"].id, world["staff_a"])


def test_a_lab_may_not_link_another_labs_patient(db, world):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        scope.require_own_patient(db, world["pat_b"].id, world["staff_a"])
    assert exc.value.status_code == 404, "denial must not confirm the patient exists"


def test_a_national_role_may_link_any_patient(db, world):
    scope.require_own_patient(db, world["pat_b"].id, world["ministry"])


def test_a_lab_user_with_no_lab_is_refused(db, world):
    """A lab-scoped role whose lab_id is missing must fail closed, not open."""
    from fastapi import HTTPException

    orphan = _actor("lab_staff", None)
    assert scope.visible_canonical(db, world["own_a"].id, orphan) is None
    with pytest.raises(HTTPException):
        scope.require_own_patient(db, world["pat_a"].id, orphan)


# ─── regression guard on the route wiring ───────────────────────────────────

@pytest.mark.parametrize(("handler", "must_contain"), [
    ("search_canonical", "require_national_scope"),
    ("merge", "require_national_scope"),
    ("get_by_citizen", "require_national_scope"),
    ("create_citizen_link", "require_national_scope"),
    ("get_canonical", "visible_canonical"),
    ("get_by_patient", "require_own_patient"),
    ("create_patient_link", "require_own_patient"),
    ("create_canonical", "provenance_lab_id"),
])
def test_every_handler_still_carries_its_guard(handler, must_contain):
    """Pins the wiring: a guard removed from a route fails here by name."""
    import inspect

    from app.routes import canonical_patient as routes

    source = inspect.getsource(getattr(routes, handler))
    assert must_contain in source, f"{handler}() no longer calls {must_contain} (NR-148)"
