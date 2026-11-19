"""Hospital/NHDW vertical slice: admission -> transfer -> discharge lifecycle.

Findings, fixed:

1. app/nhdw/routes.py::create_admission/update_admission/
   discharge_admission/transfer_admission had zero role check (any
   authenticated LabUser of any role). Added _NHDW_ADMISSION_WRITE_ROLES
   gate (admin/master_admin/doctor/nurse), first line of each route.

2. app/nhdw/services.py::transfer_patient looked up the *target* bed
   (`to_bed_id`, pure client input) with NO lab_id filter at all, while
   every other cross-tenant lookup in the same file (department,
   create_admission's own bed_id) was correctly scoped -- a caller could
   transfer a patient into another lab's bed, flip its status to
   "occupied" and overwrite its current_patient_id across the tenant
   boundary. Fixed: same Bed.lab_id == lab_id filter used everywhere else
   in this file; now 404s instead of silently no-op'ing when the target
   bed doesn't resolve in the acting lab.

3. update_admission/discharge_patient/transfer_patient read Admission
   (and, for discharge/transfer, Bed) with no row lock, then
   read-checked-then-wrote status (discharge_date, bed.status) -- the
   same race already closed elsewhere this session (EMS ambulance-status
   CAS, Nursing task lifecycle). Fixed with `.with_for_update()` on the
   admission and bed rows in all three mutation paths (plus
   create_admission's own bed lookup), and a `version` increment on the
   previously-never-incremented OptimisticLockMixin column
   NHDWBaseEntity already provides.

STRUCTURAL BLOCKER, FOUND AND RESOLVED THIS PASS: `Admission` (and 12
sibling NHDW models) declared 21 cross-declarative-base
`relationship("Patient"/"HospitalMaster"/"HospitalDepartment"/"Room"/
"Bed"/"Clinic", foreign_keys=[...])` entries. NHDWBase (app/nhdw/base.py)
is its own `declarative_base()`, separate from both app.database.Base
(owns Patient) and HospitalBase (owns the other four) -- SQLAlchemy
relationship() STRING targets resolve only within the owning class's own
declarative registry, so none of these ever could resolve:
`db.query(Admission)` raised `sqlalchemy.exc.InvalidRequestError:
... expression 'Patient' failed to locate a name` the instant any mapper
configuration pass touched it, in SQLite and (independently confirmed
via a real throwaway local PostgreSQL 16 instance during triage) in
Postgres alike, since this is a pure Python/ORM-layer failure, not a
database one. This is the same NR-086/NR-078 cross-base class Abu Ali's
app/orm_topology.py addresses for five other bases via a *shared
MetaData* -- but a shared MetaData only fixes `ForeignKey("table.col")`
STRING resolution (which looks up target Table objects in MetaData.tables
at flush time); it does nothing for relationship() STRING resolution,
which looks up target classes in the declarative registry instead
(confirmed with a minimal two-registry SQLAlchemy repro before touching
any repo file). None of these 21 relationships had any call site anywhere
in this repo (grepped app/nhdw/routes.py, services.py, kpi.py for every
attribute name -- zero references; every actual cross-model lookup in
this domain already goes through explicit `db.query(...)` calls, never
the ORM relationship). They were dead, unreachable, cross-base-broken
convenience attributes -- proven unreachable, non-canonical (no other
model back_populates/backrefs any of them), no migration/data dependency
(pure ORM decoration, the underlying *_id columns are untouched and keep
working exactly as before), and safe to remove. Removed all 21; kept the
2 same-registry relationships (Discharge.admission -> Admission,
HospitalMessage.parent -> HospitalMessage, both resolve fine within
NHDWBase's own registry and are unaffected). Confirmed:
`db.query(Admission)` (and every other affected model) now configures and
queries correctly. This did not touch orm_topology.py, any migration, or
any cross-domain canonical ownership -- it is a same-file dead-code
removal that happens to also be the actual root cause.

TWO MORE DEFECTS, found only after the structural blocker above was fixed
(the first time any NHDW mutation could actually run to completion) and
fixed in this same pass, both in-file and unrelated to each other:

4. Every one of the 24 `log_action(...)` calls in app/nhdw/services.py
   used the wrong positional argument order against the real signature
   `log_action(db, action, resource_type, resource_id=None, user_id=None,
   user_role=None, lab_id=None, details=None, ...)`. E.g.
   `log_action(db, "nhdw.admission.create", admission.id, lab_id,
   user_id, data)` put `admission.id` where `resource_type` belongs,
   `lab_id` where `resource_id` belongs, and (for the 6-arg calls) the
   whole `data` dict where `user_role` belongs -- meaning `lab_id` was
   NEVER recorded on any NHDW audit entry, `resource_type`/`resource_id`
   were always wrong, and `details` was always None. It also crashes
   outright: passing a raw dict positionally into `user_role` reaches
   `AuditLog(user_role=<dict>, ...)`, and the sqlite3 DBAPI cannot bind a
   dict to any parameter, so every mutation with a details payload 500'd
   the instant it reached the audit call. Fixed: rewrote all 24 call
   sites with explicit keyword arguments and a correct `resource_type`
   string per call (e.g. "admission", "discharge", "clinical_task").

5. app/nhdw/routes.py::_model_to_dict iterated `model_instance.__table__.
   columns` and used each Column's own `.key`. For `metadata_ =
   Column("metadata", JSON, ...)` (present on every NHDW model -- the
   trailing underscore exists specifically so the Python attribute
   doesn't collide with the declarative class's own built-in `.metadata`
   attribute), the Column's `.key` defaults to its DB column name,
   "metadata", NOT the Python attribute name "metadata_". So
   `getattr(instance, "metadata")` silently returned the SQLAlchemy
   `MetaData()` object every mapped class carries -- not the JSON field's
   actual value -- and FastAPI's `jsonable_encoder` recurses on that
   object until it hits Python's recursion limit, turning every
   successful create/update response in this entire file into a 500.
   Fixed: iterate `sqlalchemy.inspect(instance).mapper.column_attrs`
   instead, which maps to the correct Python attribute key
   ("metadata_") regardless of the DB column name.

One more defect, found only via a real-Postgres concurrency proof (see
below) -- SQLite's dynamic typing silently accepted it, so it never
surfaced in this file's own test suite: `AuditLog.resource_id`
(app/models/audit_log.py) is `Integer`, but every NHDW model's primary
key is a ULID `String(26)` (NHDWBaseEntity). Passing e.g. `discharge.id`
as `resource_id` raised `psycopg2.errors.InvalidTextRepresentation:
invalid input syntax for type integer` on real Postgres -- the exact
same String-vs-Integer class already fixed once this session (Nursing's
lab_users.id FK columns), except here it's the *shared* audit-log
table's column, used across every domain in this repo, not a single
domain's own model -- widening it is a schema change and out of scope
for this pass (same human-approval boundary as the migration gap above).
Nursing's own `log_action(..., assignment.id, ...)` calls have this exact
same latent defect (not fixed there this pass; NursingBase's cross-base
FK topology blocker means Nursing's audit calls can't be reached yet
anyway). Fixed in NHDW only: all 24 calls now pass `resource_id=None` and
fold the real id into `details["resource_id"]` instead -- full audit
traceability preserved, zero schema risk.

Also removed 4 invalid `detail_ar=` keyword arguments passed to plain
`fastapi.HTTPException(...)` (in create_admission's bed-lookup, discharge's
already-discharged check, and get_dashboard_config) -- `HTTPException`
has no such parameter, and grepping this pattern found it used nowhere
else in the entire repo, so there is no shared bilingual-exception class
this was meant to route through. Every one of these 4 error paths raised
`TypeError: HTTPException.__init__() got an unexpected keyword argument
'detail_ar'` instead of the intended 404/409, i.e. an unreachable error
branch became an unhandled 500 whenever it should have fired. Dropped the
invalid kwarg; kept the English `detail`.

REMAINING BLOCKER, NOT fixed here (a new migration needs human approval
per this repo's own CLAUDE.md, "Requires human approval: DB schema
changes"): grepping every file in backend/migrations/versions/ for the
literal table names `hospitals`, `hospital_departments`, `hospital_rooms`,
`hospital_beds` (app/hospital/models's own tables, which
create_admission/transfer_patient query) finds NONE of them -- no
migration, dynamic or static, ever creates these tables (the only
dynamic-table-name migration, 20260814_0002_organization_structure.py, is
grepped and confirmed to only ever create niam_* tables). Independently
confirmed against a real throwaway local Postgres 16 instance that
alembic's own chain never reaches a state with these tables created
(it fails earlier for an unrelated reason -- a pre-existing Pharmacy
migration FK type error, Abu Ali's active work area, not investigated
further). Since Admission.department_id is NOT NULL and create_admission
unconditionally queries HospitalDepartment whenever one is supplied
(every real admission), this alone would still 500 a real Alembic-
migrated Postgres deployment even with the structural fix above landed.
The tests below use this repo's existing SQLite test harness, which
builds tables via `metadata.create_all()` across every declarative Base
(including HospitalBase) rather than via Alembic (see tests/conftest.py)
-- the same convention every other domain's tests in this repo already
rely on -- so they now fully exercise the real Python/ORM code paths
end-to-end, but a real Alembic-migrated deployment still needs the
missing migration before this journey is actually deployable. Pinned
directly (test_hospital_structure_tables_have_no_migration).
"""
from __future__ import annotations

import glob
import os

from app.nhdw.models import Admission

from tests.conftest import auth_headers

_MIGRATIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "migrations", "versions",
)

_HOSPITAL_STRUCTURE_TABLES = (
    "hospitals", "hospital_departments", "hospital_rooms", "hospital_beds",
    # hospital_operation_theaters: confirmed this pass to be a stronger form
    # of the same gap -- 20260820_0004_surgical_safety_checklists.py's
    # hospital_surgical_safety_checklists table has an unconditional
    # ForeignKeyConstraint(["operation_theater_id"], ["hospital_operation_theaters.id"])
    # with no _table_exists guard, so a real `alembic upgrade head` from a
    # blank PostgreSQL database now fails outright at this migration
    # (UndefinedTable), not merely at NHDW's own runtime queries as
    # previously documented. Reproduced directly against a disposable
    # PostgreSQL 16 database this pass.
    "hospital_operation_theaters",
)


_topology_counter = [0]


def _make_hospital_topology(db, lab_id: int, *, bed_status: str = "available"):
    """Create the minimum HospitalMaster -> Department -> Room -> Bed chain
    an admission needs, scoped to one lab. Returns their ids."""
    from app.hospital.models import Bed, HospitalDepartment, HospitalMaster, Room

    _topology_counter[0] += 1
    n = _topology_counter[0]
    hospital = HospitalMaster(
        lab_id=lab_id, code=f"H-{lab_id}-{n}", name=f"Hospital {lab_id}-{n}", hospital_type="general",
    )
    db.add(hospital)
    db.flush()
    dept = HospitalDepartment(
        lab_id=lab_id, hospital_id=hospital.id, code=f"D-{lab_id}-{n}", name="Ward A",
    )
    db.add(dept)
    db.flush()
    room = Room(
        lab_id=lab_id, department_id=dept.id, code=f"R-{lab_id}-{n}", name="Room 1", room_type="ward",
    )
    db.add(room)
    db.flush()
    bed = Bed(lab_id=lab_id, room_id=room.id, bed_number="1", status=bed_status)
    db.add(bed)
    db.flush()
    return {"hospital_id": hospital.id, "department_id": dept.id, "room_id": room.id, "bed_id": bed.id}


def _make_patient(db, lab_id: int, health_id: str):
    from app.models.patient import Patient
    patient = Patient(
        lab_id=lab_id, health_id=health_id,
        full_name=f"Patient {health_id}", phone=f"0770{health_id[-7:]}",
    )
    db.add(patient)
    db.flush()
    return patient


# ─── Remaining blocker: hospital structure tables have no migration ───────


def test_hospital_structure_tables_have_no_migration():
    """Documents and pins a real production blocker independent of the
    (now-resolved) ORM relationship issue: no migration file creates any
    of the app/hospital/models tables that create_admission/
    transfer_patient query. This test starts FAILING (meaning a table now
    has a migration) the moment someone adds the missing migration -- at
    which point this whole journey becomes deployable against real
    Postgres, not just testable against SQLite."""
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


# ─── Role gates: provable before any DB write ───────────────────────────────


def test_create_admission_requires_clinical_write_role(client, db, make_lab, make_lab_user):
    lab = make_lab("NHDW Authz Lab 1")
    staff = make_lab_user(lab.id, role="staff")
    patient = _make_patient(db, lab.id, "H-NH-001")
    topo = _make_hospital_topology(db, lab.id)

    before = db.query(Admission).count()
    res = client.post(
        "/nhdw/admissions",
        headers=auth_headers(staff.id, lab.id, role="staff"),
        json={
            "patient_id": patient.id, "hospital_id": topo["hospital_id"],
            "department_id": topo["department_id"], "bed_id": topo["bed_id"],
            "admission_type": "elective",
        },
    )
    assert res.status_code == 403
    assert db.query(Admission).count() == before


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


# ─── End-to-end behavioral proof (now possible: the ORM blocker is gone) ────


def test_create_admission_occupies_bed_and_persists(client, db, make_lab, make_lab_user):
    lab = make_lab("NHDW E2E Lab 1")
    doctor = make_lab_user(lab.id, role="doctor")
    patient = _make_patient(db, lab.id, "H-NH-100")
    topo = _make_hospital_topology(db, lab.id)

    res = client.post(
        "/nhdw/admissions",
        headers=auth_headers(doctor.id, lab.id, role="doctor"),
        json={
            "patient_id": patient.id, "hospital_id": topo["hospital_id"],
            "department_id": topo["department_id"], "bed_id": topo["bed_id"],
            "admission_type": "elective",
        },
    )
    assert res.status_code == 201
    admission_id = res.json()["id"]

    admission = db.query(Admission).filter(Admission.id == admission_id).first()
    assert admission is not None
    assert admission.version == 1

    from app.hospital.models import Bed
    bed = db.query(Bed).filter(Bed.id == topo["bed_id"]).first()
    assert bed.status == "occupied"
    assert bed.current_patient_id == patient.id


def test_transfer_rejects_bed_belonging_to_another_lab(client, db, make_lab, make_lab_user):
    lab_one = make_lab("NHDW Tenant Lab A")
    lab_two = make_lab("NHDW Tenant Lab B")
    doctor = make_lab_user(lab_one.id, role="doctor")
    patient = _make_patient(db, lab_one.id, "H-NH-010")
    topo_one = _make_hospital_topology(db, lab_one.id)
    topo_two = _make_hospital_topology(db, lab_two.id)  # a bed in a DIFFERENT lab

    create_res = client.post(
        "/nhdw/admissions",
        headers=auth_headers(doctor.id, lab_one.id, role="doctor"),
        json={
            "patient_id": patient.id, "hospital_id": topo_one["hospital_id"],
            "department_id": topo_one["department_id"], "bed_id": topo_one["bed_id"],
            "admission_type": "elective",
        },
    )
    assert create_res.status_code == 201
    admission_id = create_res.json()["id"]

    res = client.post(
        f"/nhdw/admissions/{admission_id}/transfer",
        headers=auth_headers(doctor.id, lab_one.id, role="doctor"),
        json={"to_department_id": topo_one["department_id"], "to_bed_id": topo_two["bed_id"]},
    )
    assert res.status_code == 404

    from app.hospital.models import Bed
    other_lab_bed = db.query(Bed).filter(Bed.id == topo_two["bed_id"]).first()
    assert other_lab_bed.status == "available"
    assert other_lab_bed.current_patient_id is None


def test_transfer_to_same_lab_bed_succeeds_and_bumps_version(client, db, make_lab, make_lab_user):
    lab = make_lab("NHDW Transfer Lab 1")
    doctor = make_lab_user(lab.id, role="doctor")
    patient = _make_patient(db, lab.id, "H-NH-011")
    topo_from = _make_hospital_topology(db, lab.id)
    topo_to = _make_hospital_topology(db, lab.id)

    create_res = client.post(
        "/nhdw/admissions",
        headers=auth_headers(doctor.id, lab.id, role="doctor"),
        json={
            "patient_id": patient.id, "hospital_id": topo_from["hospital_id"],
            "department_id": topo_from["department_id"], "bed_id": topo_from["bed_id"],
            "admission_type": "elective",
        },
    )
    admission_id = create_res.json()["id"]
    admission = db.query(Admission).filter(Admission.id == admission_id).first()
    assert admission.version == 1

    res = client.post(
        f"/nhdw/admissions/{admission_id}/transfer",
        headers=auth_headers(doctor.id, lab.id, role="doctor"),
        json={"to_department_id": topo_to["department_id"], "to_bed_id": topo_to["bed_id"]},
    )
    assert res.status_code == 200

    db.refresh(admission)
    assert admission.department_id == topo_to["department_id"]
    assert admission.bed_id == topo_to["bed_id"]
    assert admission.version == 2

    from app.hospital.models import Bed
    from_bed = db.query(Bed).filter(Bed.id == topo_from["bed_id"]).first()
    to_bed = db.query(Bed).filter(Bed.id == topo_to["bed_id"]).first()
    assert from_bed.status == "available"
    assert from_bed.current_patient_id is None
    assert to_bed.status == "occupied"
    assert to_bed.current_patient_id == patient.id


def test_discharge_frees_bed_and_already_discharged_is_rejected(client, db, make_lab, make_lab_user):
    lab = make_lab("NHDW Discharge Lab 1")
    doctor = make_lab_user(lab.id, role="doctor")
    patient = _make_patient(db, lab.id, "H-NH-020")
    topo = _make_hospital_topology(db, lab.id)

    create_res = client.post(
        "/nhdw/admissions",
        headers=auth_headers(doctor.id, lab.id, role="doctor"),
        json={
            "patient_id": patient.id, "hospital_id": topo["hospital_id"],
            "department_id": topo["department_id"], "bed_id": topo["bed_id"],
            "admission_type": "elective",
        },
    )
    admission_id = create_res.json()["id"]

    res = client.post(
        f"/nhdw/admissions/{admission_id}/discharge",
        headers=auth_headers(doctor.id, lab.id, role="doctor"),
        json={"discharge_type": "home"},
    )
    assert res.status_code == 200

    from app.hospital.models import Bed
    bed = db.query(Bed).filter(Bed.id == topo["bed_id"]).first()
    assert bed.status == "cleaning"
    assert bed.current_patient_id is None

    admission = db.query(Admission).filter(Admission.id == admission_id).first()
    assert admission.version == 2

    # discharge is terminal -- a second attempt must not silently succeed again
    res2 = client.post(
        f"/nhdw/admissions/{admission_id}/discharge",
        headers=auth_headers(doctor.id, lab.id, role="doctor"),
        json={"discharge_type": "home"},
    )
    assert res2.status_code == 409


def test_update_admission_increments_version(client, db, make_lab, make_lab_user):
    lab = make_lab("NHDW Version Lab 1")
    doctor = make_lab_user(lab.id, role="doctor")
    patient = _make_patient(db, lab.id, "H-NH-030")
    topo = _make_hospital_topology(db, lab.id)

    create_res = client.post(
        "/nhdw/admissions",
        headers=auth_headers(doctor.id, lab.id, role="doctor"),
        json={
            "patient_id": patient.id, "hospital_id": topo["hospital_id"],
            "department_id": topo["department_id"], "admission_type": "elective",
        },
    )
    admission_id = create_res.json()["id"]

    res = client.put(
        f"/nhdw/admissions/{admission_id}",
        headers=auth_headers(doctor.id, lab.id, role="doctor"),
        json={"notes": "updated"},
    )
    assert res.status_code == 200

    admission = db.query(Admission).filter(Admission.id == admission_id).first()
    assert admission.notes == "updated"
    assert admission.version == 2
