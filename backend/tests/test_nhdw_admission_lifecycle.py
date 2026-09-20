"""Hospital/NHDW vertical slice: admission -> transfer -> discharge lifecycle.

Before this pass, app/nhdw/routes.py::create_admission/update_admission/
discharge_admission/transfer_admission had zero role check (any
authenticated LabUser of any role). app/nhdw/services.py::transfer_patient
looked up the *target* bed (`to_bed_id`, pure client input) with no lab_id
filter at all -- `db.query(Bed).filter(Bed.id == data["to_bed_id"]).first()`
-- while every other cross-tenant lookup in the same file (department,
create_admission's own bed_id) was correctly lab_id-scoped. A caller could
transfer a patient into another lab's bed, flip its status to "occupied"
and overwrite its current_patient_id across the tenant boundary. Fixed by
adding the same Bed.lab_id == lab_id filter used everywhere else in this
file, and returning 404 instead of silently skipping the bed move when the
target bed doesn't resolve in this lab.

Also: update_admission/discharge_patient/transfer_patient read Admission
(and, for discharge/transfer, Bed) without a row lock, then read-checked-
then-wrote status (discharge_date, bed.status) -- the same
read-check-then-write race already closed elsewhere this session (EMS
ambulance-status CAS, Nursing task lifecycle). Fixed with
`.with_for_update()` on the admission and bed rows in all three mutation
paths, plus a `version` increment on the (previously never incremented)
OptimisticLockMixin column NHDWBaseEntity already provides.

Two independent findings surfaced while building fixtures for this file,
NEITHER fixed here, both handed off (not mine to fix, per this repo's own
CLAUDE.md and the canonical-architecture boundary this session works
under):

1. STRUCTURAL, more severe, discovered first: `Admission` declares five
   `relationship("Patient"/"HospitalMaster"/"HospitalDepartment"/"Room"/
   "Bed", foreign_keys=[...])` entries, but NHDWBase (app/nhdw/base.py) is
   its own `declarative_base()`, separate from both `app.database.Base`
   (where Patient lives) and HospitalBase (where the other four live).
   SQLAlchemy relationship() string targets resolve against the owning
   class's own registry, so none of these five names resolve. Directly
   reproduced: `db.query(Admission)` (or constructing/flushing an
   Admission) raises `sqlalchemy.exc.InvalidRequestError: ... expression
   'Patient' failed to locate a name ('Patient')` the moment any mapper
   configuration pass touches it -- in the SQLite test harness AND
   independent of database backend, since this is a pure Python/ORM
   mapper-configuration failure, not a database-level one. This is the
   same class of cross-declarative-base defect (NR-086/NR-078) that
   Abu Ali's app/orm_topology.py is actively closing for five other
   bases via a shared MetaData -- but this specific failure mode
   (relationship() name resolution) is not something a shared MetaData
   alone fixes; it needs either an explicit `primaryjoin`, moving these
   classes onto a shared registry, or Abu Ali's own judgment on the
   right canonical fix. NOT touched here. Pinned directly
   (test_admission_relationships_cannot_be_configured_cross_base).
   Practical effect: in the CURRENT state of this branch, no code path
   that queries or persists an Admission can work at all -- not a
   tenant/migration issue, a total block on the whole journey.

2. Separately, and shallower: grepping every file in
   backend/migrations/versions/ for the literal table names `hospitals`,
   `hospital_departments`, `hospital_rooms`, `hospital_beds`
   (app/hospital/models's own __tablename__ values) finds NONE of them --
   no migration, dynamic or static, ever creates these tables (the only
   dynamic-table-name migration, 20260814_0002_organization_structure.py,
   is grepped and confirmed to only ever create niam_* tables). Confirmed
   independently against a real, throwaway local PostgreSQL 16 instance
   that alembic's migration chain never reaches a point where these
   tables exist (it fails earlier for an unrelated reason -- a
   pre-existing Pharmacy migration FK type error, Abu Ali's active work
   area, not investigated further here); the full-text grep is decisive
   on its own regardless. New migrations need human approval per this
   repo's CLAUDE.md ("Requires human approval: DB schema changes"), so
   not added here. Pinned directly
   (test_hospital_structure_tables_have_no_migration).

Given (1), no HTTP-level test can exercise create_admission/
update_admission/discharge_patient/transfer_patient end-to-end right now
(every one of them would 500 on the very first Admission touch, for any
role). The role-gate tests below stay valid because the role check is the
first statement in each route -- it 403s before any Admission access ever
happens. The state-machine/tenant-scope/version-increment fixes are
proven at the source level instead (the same "wiring pin" technique used
for other currently-unbuildable infrastructure gaps this session, e.g.
test_nursing_task_authorization.py) -- decisive that the fix is wired in,
though not yet a live behavioral proof. Once finding (1) is resolved,
these wiring pins should be replaced with real HTTP-level tests exercising
the actual transitions (a 409 on re-discharge, a 404 on a cross-lab
to_bed_id, a version bump after update).
"""
from __future__ import annotations

import glob
import inspect
import os

import pytest

from tests.conftest import auth_headers

_MIGRATIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "migrations", "versions",
)

_HOSPITAL_STRUCTURE_TABLES = (
    "hospitals", "hospital_departments", "hospital_rooms", "hospital_beds",
)


# ─── P0 (structural): Admission's cross-base relationships cannot configure ──


def test_admission_relationships_cannot_be_configured_cross_base(db):
    """Pins the deeper, structural blocker: NHDWBase is its own
    declarative_base(), so Admission's relationship("Patient"/...) string
    targets can never resolve. This test starts FAILING (meaning the
    relationships now configure) the moment this is fixed -- at which
    point the wiring-pin tests below should be replaced with real
    HTTP-level behavioral tests."""
    from app.nhdw.models import Admission

    with pytest.raises(Exception) as exc:
        db.query(Admission).count()
    assert "Patient" in str(exc.value) or "failed to locate a name" in str(exc.value), (
        f"Expected the known cross-base relationship() resolution failure, "
        f"got a different error instead: {exc.value!r}. If Admission is now "
        f"queryable, this pin has been resolved -- replace it and the other "
        f"wiring-pin tests in this file with real HTTP-level tests."
    )


# ─── P1 (shallower): hospital structure tables have no migration ───────────


def test_hospital_structure_tables_have_no_migration():
    """Documents and pins a real production blocker independent of (1)
    above: no migration file creates any of the app/hospital/models
    tables that create_admission/transfer_patient query. This test starts
    FAILING (meaning a table now has a migration) the moment someone adds
    the missing migration."""
    migration_files = glob.glob(os.path.join(_MIGRATIONS_DIR, "*.py"))
    assert migration_files, "expected to find migration files to scan"
    combined_source = ""
    for path in migration_files:
        with open(path, encoding="utf-8") as f:
            combined_source += f.read()
    for table in _HOSPITAL_STRUCTURE_TABLES:
        assert f'"{table}"' not in combined_source and f"'{table}'" not in combined_source, (
            f"Migration now creates '{table}' -- the hospital-structure-tables "
            f"migration gap this test pins has been closed."
        )


# ─── Role gates: provable before any DB write (fire before Admission is touched) ──


def test_create_admission_requires_clinical_write_role(client, make_lab, make_lab_user):
    lab = make_lab("NHDW Authz Lab 1")
    staff = make_lab_user(lab.id, role="staff")

    res = client.post(
        "/nhdw/admissions",
        headers=auth_headers(staff.id, lab.id, role="staff"),
        json={
            "patient_id": 1, "hospital_id": 1,
            "department_id": 1, "admission_type": "elective",
        },
    )
    assert res.status_code == 403


def test_update_admission_requires_clinical_write_role(client, make_lab, make_lab_user):
    lab = make_lab("NHDW Authz Lab 2")
    staff = make_lab_user(lab.id, role="staff")

    res = client.put(
        "/nhdw/admissions/nonexistent-admission-id",
        headers=auth_headers(staff.id, lab.id, role="staff"),
        json={"notes": "x"},
    )
    assert res.status_code == 403


def test_discharge_admission_requires_clinical_write_role(client, make_lab, make_lab_user):
    lab = make_lab("NHDW Authz Lab 3")
    staff = make_lab_user(lab.id, role="staff")

    res = client.post(
        "/nhdw/admissions/nonexistent-admission-id/discharge",
        headers=auth_headers(staff.id, lab.id, role="staff"),
        json={"discharge_type": "home"},
    )
    assert res.status_code == 403


def test_transfer_admission_requires_clinical_write_role(client, make_lab, make_lab_user):
    lab = make_lab("NHDW Authz Lab 4")
    staff = make_lab_user(lab.id, role="staff")

    res = client.post(
        "/nhdw/admissions/nonexistent-admission-id/transfer",
        headers=auth_headers(staff.id, lab.id, role="staff"),
        json={"to_department_id": 1},
    )
    assert res.status_code == 403


# ─── Wiring pins: source-level proof the fixes are actually invoked ────────
# (Admission's cross-base relationship gap above blocks a real flush, so
# actual runtime behavior of update/discharge/transfer_patient cannot be
# proven via HTTP yet -- source-inspection is the same established
# technique used for other currently-unbuildable infrastructure gaps this
# session, e.g. test_nursing_task_authorization.py.)


def test_wiring_pin_update_admission_locks_row_and_bumps_version():
    from app.nhdw.services import NHDWService
    source = inspect.getsource(NHDWService.update_admission)
    assert "_get_admission_locked" in source
    assert "admission.version += 1" in source


def test_wiring_pin_discharge_patient_locks_row_and_bed():
    from app.nhdw.services import NHDWService
    source = inspect.getsource(NHDWService.discharge_patient)
    assert "_get_admission_locked" in source
    assert "with_for_update" in source
    assert "admission.version += 1" in source


def test_wiring_pin_transfer_patient_locks_row_and_scopes_bed_to_lab():
    from app.nhdw.services import NHDWService
    source = inspect.getsource(NHDWService.transfer_patient)
    assert "_get_admission_locked" in source
    assert 'Bed.lab_id == lab_id' in source
    assert "admission.version += 1" in source
