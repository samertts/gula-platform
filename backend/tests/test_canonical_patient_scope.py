"""NR-148 — the Master Patient Index has a scope rule now, and it is the right one.

THE MPI IS DELIBERATELY CROSS-TENANT; THAT WAS NEVER THE DEFECT.
NR-022 decided that Person/Identity is the canonical national subject and that
Patient and Citizen are contextual roles on it. An index that stopped at a
laboratory boundary could not do the one job it exists for. `lab_id` on
`canonical_patients` is PROVENANCE, and the schema says so: nullable, ON DELETE
SET NULL, no (lab_id, ...) composite index -- while `patients`, which IS
tenant-owned, carries ix_patients_lab_id and ix_patients_lab_phone.

The two defects were:

  1. `CanonicalPatient(**data.model_dump())` let the request body set lab_id,
     so a laboratory could file a canonical record under another's name.
     Provenance the client chooses is not provenance.

  2. Nothing separated callers who may act nationally from those who may not.
     Any authenticated user -- a technician at one private lab -- could search
     the entire national index by name or phone, read any canonical record, and
     MERGE two people's identities.

The rule invents no permission. `platform:view_stats` is already held by
exactly master_admin, ministry_admin and province_admin and by no lab-scoped
role, so it is read as the marker for national scope.

Every denial below is paired with a positive control. A policy that refused
everything would satisfy the denials alone and look secure while being broken.
"""
from __future__ import annotations

import os

os.environ["RUNTIME_MODE"] = "test"
os.environ["FEATURE_BACKGROUND_TASKS"] = "false"
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-" + "x" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=")
os.environ.setdefault("NID_HMAC_KEY", "a" * 64)
os.environ.setdefault("REDIS_URL", "")

import pytest
from app.models.canonical_patient import CanonicalPatient, PatientLink
from app.models.lab import Lab
from app.models.lab_user import LabUser
from app.models.patient import Patient
from app.security.auth import hash_password
from app.services.mpi import scope


@pytest.fixture()
def world(db):
    """Two labs, each with a user and a patient, plus three canonical records."""
    lab_a = Lab(name="Lab A", license_number="LIC-MPI-A", lab_type="private",
                city="Baghdad", is_active=True)
    lab_b = Lab(name="Lab B", license_number="LIC-MPI-B", lab_type="private",
                city="Mosul", is_active=True)
    db.add_all([lab_a, lab_b])
    db.flush()

    def _user(lab, role, email):
        # lab_users.lab_id is NOT NULL, so even a national role has a home lab.
        # That is exactly why scope must come from the ROLE and not from
        # whether lab_id happens to be set.
        u = LabUser(lab_id=lab.id, name=role, email=email,
                    password_hash=hash_password("Pa55word"), role=role,
                    is_active=True)
        db.add(u)
        return u

    staff_a = _user(lab_a, "lab_staff", "staff_a@a.com")
    staff_b = _user(lab_b, "lab_staff", "staff_b@b.com")
    ministry = _user(lab_a, "ministry_admin", "ministry@gov.iq")
    db.flush()

    pat_a = Patient(lab_id=lab_a.id, full_name="Patient A", phone="07700000011")
    pat_b = Patient(lab_id=lab_b.id, full_name="Patient B", phone="07700000022")
    db.add_all([pat_a, pat_b])
    db.flush()

    # own_a: contributed by Lab A.  linked_a: contributed by nobody, but linked
    # to Lab A's patient.  foreign: Lab B's, and unconnected to Lab A.
    own_a = CanonicalPatient(lab_id=lab_a.id, full_name="Contributed by A")
    linked_a = CanonicalPatient(lab_id=None, full_name="Linked to A's patient")
    foreign = CanonicalPatient(lab_id=lab_b.id, full_name="Belongs to B")
    db.add_all([own_a, linked_a, foreign])
    db.flush()
    db.add(PatientLink(patient_id=pat_a.id, canonical_id=linked_a.id,
                       linkage_method="manual"))
    db.commit()

    return {
        "lab_a": lab_a, "lab_b": lab_b,
        "staff_a": staff_a, "staff_b": staff_b, "ministry": ministry,
        "pat_a": pat_a, "pat_b": pat_b,
        "own_a": own_a, "linked_a": linked_a, "foreign": foreign,
    }


# ─── national scope is read from the existing matrix ────────────────────────

def test_a_national_scope_is_exactly_the_cross_lab_roles():
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


class _Actor:
    def __init__(self, role, lab_id=None):
        self.role = role
        self.lab_id = lab_id


def _actor(role, lab_id=None):
    return _Actor(role, lab_id)


def test_b_an_actor_with_no_role_has_no_scope():
    assert not scope.has_national_scope(_actor(None))
    assert not scope.has_national_scope(_actor(""))


# ─── provenance is server-derived ───────────────────────────────────────────

def test_c_provenance_comes_from_the_caller(world):
    """Server-derived, and never the body's.

    `lab_users.lab_id` is NOT NULL, so a national role carries a home lab too.
    Provenance records where the contribution actually came from, which stays
    truthful for both kinds of caller; the column is nullable because records
    can arrive from sources that are not a laboratory at all.
    """
    assert scope.provenance_lab_id(world["staff_a"]) == world["lab_a"].id
    assert scope.provenance_lab_id(world["ministry"]) == world["lab_a"].id
    assert scope.provenance_lab_id(_actor("lab_staff", None)) is None


def test_d_the_create_schema_cannot_carry_a_lab_id():
    """The body named the record's laboratory. It no longer has the field."""
    from app.routes.canonical_patient import CanonicalPatientCreate

    assert "lab_id" not in CanonicalPatientCreate.model_fields, (
        "CanonicalPatientCreate accepts lab_id again; the request body can "
        "forge provenance in the national index (NR-148)"
    )


# ─── visibility ─────────────────────────────────────────────────────────────

def test_e_a_lab_sees_a_record_it_contributed(db, world):
    """Positive control for the lab-scoped read path."""
    assert scope.visible_canonical(db, world["own_a"].id, world["staff_a"]) is not None


def test_f_a_lab_sees_a_record_linked_to_its_own_patient(db, world):
    """The MPI's actual purpose, for a lab-scoped caller."""
    assert scope.visible_canonical(db, world["linked_a"].id, world["staff_a"]) is not None


def test_g_a_lab_does_not_see_an_unconnected_record(db, world):
    assert scope.visible_canonical(db, world["foreign"].id, world["staff_a"]) is None


def test_h_a_national_role_sees_every_record(db, world):
    """Note the ministry user's home lab is Lab A, so `foreign` proves the
    point: it is visible by ROLE, not because of any lab connection."""
    for key in ("own_a", "linked_a", "foreign"):
        assert scope.visible_canonical(db, world[key].id, world["ministry"]) is not None, (
            f"a ministry admin cannot see {key}; the index is unusable nationally"
        )


def test_i_absence_and_denial_are_indistinguishable(db, world):
    """Neither leaks which canonical ids exist.

    An adversarial review was right that the first version of this test was
    TAUTOLOGICAL: `visible_canonical` returns None on both branches by
    construction, so asserting both are None could not fail. The claim worth
    testing is that the two are reached by DIFFERENT internal paths -- a real
    record refused, and a record that is not there -- and still arrive at the
    same answer. So the existence of the foreign record is asserted first.
    """
    present = db.query(CanonicalPatient).filter(
        CanonicalPatient.id == world["foreign"].id,
    ).one_or_none()
    assert present is not None, "the denied record must actually exist"
    assert db.query(CanonicalPatient).filter(
        CanonicalPatient.id == 999_999_999,
    ).one_or_none() is None

    denied = scope.visible_canonical(db, world["foreign"].id, world["staff_a"])
    missing = scope.visible_canonical(db, 999_999_999, world["staff_a"])
    assert denied is None and missing is None


# ─── national-only actions ──────────────────────────────────────────────────

@pytest.mark.parametrize("action", ["searching", "merging", "linking a citizen"])
def test_j_a_lab_caller_is_refused_national_actions(world, action):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        scope.require_national_scope(world["staff_a"], action)
    assert exc.value.status_code == 403

    # Positive control: the same call must SUCCEED for a national role.
    scope.require_national_scope(world["ministry"], action)


# ─── linking someone else's patient ─────────────────────────────────────────

def test_k_a_lab_may_link_its_own_patient(db, world):
    """Positive control: the legitimate linkage still works."""
    scope.require_own_patient(db, world["pat_a"].id, world["staff_a"])


def test_l_a_lab_may_not_link_another_labs_patient(db, world):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        scope.require_own_patient(db, world["pat_b"].id, world["staff_a"])
    assert exc.value.status_code == 404, "denial must not confirm the patient exists"


def test_m_a_national_role_may_link_any_patient(db, world):
    scope.require_own_patient(db, world["pat_b"].id, world["ministry"])


def test_n_a_lab_user_with_no_lab_is_refused(db, world):
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
def test_o_every_handler_still_carries_its_guard(handler, must_contain):
    """Pins the wiring: a guard removed from a route fails here by name."""
    import inspect

    from app.routes import canonical_patient as routes

    source = inspect.getsource(getattr(routes, handler))
    assert must_contain in source, (
        f"{handler}() no longer calls {must_contain} (NR-148)"
    )


# ─── NR-151: every mutation is written down ─────────────────────────────────

@pytest.mark.parametrize(("handler", "action"), [
    ("create_canonical", "canonical_patient.create"),
    ("merge", "canonical_patient.merge"),
    ("create_patient_link", "canonical_patient.link_patient"),
    ("create_citizen_link", "canonical_patient.link_citizen"),
])
def test_p_every_mutation_writes_an_audit_row(handler, action):
    """CLAUDE.md invariant 2, on the surface that had none at all.

    NR-148 hardened who may merge two people's identities; nothing recorded
    that it happened. An abusive merge was undetectable after the fact.
    """
    import inspect

    from app.routes import canonical_patient as routes

    source = inspect.getsource(getattr(routes, handler))
    assert "_audit(" in source, f"{handler}() no longer audits (NR-151)"
    assert action in source, f"{handler}() audits under the wrong action name"


def test_q_the_audit_is_written_inside_the_callers_transaction():
    """Before the commit, not after.

    An audit row that can be committed separately from the act it describes is
    not evidence of it. Each handler flushes the mutation, audits, then commits
    once.
    """
    import inspect

    from app.routes import canonical_patient as routes

    for handler in ("create_canonical", "create_patient_link", "create_citizen_link", "merge"):
        source = inspect.getsource(getattr(routes, handler))
        audit_at = source.index("_audit(")
        commit_at = source.index("db.commit()")
        assert audit_at < commit_at, (
            f"{handler}() commits before auditing, so the mutation can land "
            f"without its audit row (NR-151)"
        )


def test_r_the_audit_records_the_server_derived_actor_not_the_body():
    """The actor on an audit row must be the authenticated caller."""
    import inspect

    from app.routes import canonical_patient as routes

    source = inspect.getsource(routes._audit)
    assert 'getattr(actor, "id", None)' in source
    assert 'getattr(actor, "role", None)' in source
    assert "data." not in source, (
        "the audit helper reads from the request body; the recorded actor must "
        "come from the authenticated user (NR-151)"
    )
