"""Hospital vertical slice: role gate + explicit update boundary + CAS.

Before this pass, app/routes/hospital.py::create_hospital/update_hospital/
deactivate_hospital/create_campus had zero role check (any authenticated
LabUser of any role) -- the entire hospital.py route surface still has
no role gates beyond these four (see docs/engineering/
MUSTAFA_ACTIVE_REPAIR_QUEUE.md, "hospital-vertical-slice-remaining-scope"
for the rest, deliberately not touched this pass).

app/services/hospital_service.py::update_hospital did
`for k, v in data.items(): setattr(hospital, k, v)` over the full
request dict. The route's own HospitalUpdate schema already bounds which
fields reach this method today, so this was not independently
exploitable through the current API surface -- but the ORM-level loop
had no boundary of its own: any field later added to HospitalUpdate
would become immediately writable with no additional review. Fixed with
an explicit _HOSPITAL_UPDATABLE_FIELDS allow-list mirroring that same
schema, proven below by calling the service directly with a field
outside both the schema and the allow-list.

update_hospital/deactivate_hospital also had no row lock or version
increment despite HospitalBaseEntity already providing an
OptimisticLockMixin `version` column (unused, same pattern already
fixed in Nursing/NHDW/EMS this session). Fixed with `.with_for_update()`
+ `version += 1` in both methods.
"""
from __future__ import annotations

from app.models.audit_log import AuditLog
from app.services.hospital_service import HospitalService

from tests.conftest import auth_headers


def _make_hospital(db, lab, user_id=1):
    return HospitalService.create_hospital(
        db, lab_id=lab.id, user_id=user_id,
        data={"code": f"H-{lab.id}", "name": "Test Hospital", "hospital_type": "general"},
    )


# ─── Role gates: provable before any DB write ───────────────────────────────


def test_create_hospital_requires_admin_role(client, db, make_lab, make_lab_user):
    lab = make_lab("Hospital Sec Lab 1")
    staff = make_lab_user(lab.id, role="staff")

    res = client.post(
        "/hospital/",
        headers=auth_headers(staff.id, lab.id, role="staff"),
        json={"code": "HX", "name": "X", "hospital_type": "general"},
    )
    assert res.status_code == 403


def test_update_hospital_requires_admin_role(client, db, make_lab, make_lab_user):
    lab = make_lab("Hospital Sec Lab 2")
    staff = make_lab_user(lab.id, role="staff")
    hospital = _make_hospital(db, lab)

    res = client.put(
        f"/hospital/{hospital.id}",
        headers=auth_headers(staff.id, lab.id, role="staff"),
        json={"name": "Renamed"},
    )
    assert res.status_code == 403


def test_deactivate_hospital_requires_admin_role(client, db, make_lab, make_lab_user):
    lab = make_lab("Hospital Sec Lab 3")
    staff = make_lab_user(lab.id, role="staff")
    hospital = _make_hospital(db, lab)

    res = client.delete(
        f"/hospital/{hospital.id}",
        headers=auth_headers(staff.id, lab.id, role="staff"),
    )
    assert res.status_code == 403
    db.refresh(hospital)
    assert hospital.is_active is True  # untouched


def test_create_campus_requires_admin_role(client, db, make_lab, make_lab_user):
    lab = make_lab("Hospital Sec Lab 4")
    staff = make_lab_user(lab.id, role="staff")
    hospital = _make_hospital(db, lab)

    res = client.post(
        f"/hospital/{hospital.id}/campuses",
        headers=auth_headers(staff.id, lab.id, role="staff"),
        json={"code": "C1", "name": "Main"},
    )
    assert res.status_code == 403


def test_admin_role_succeeds_where_staff_is_denied(client, db, make_lab, make_lab_user):
    lab = make_lab("Hospital Sec Lab 5")
    admin = make_lab_user(lab.id, role="admin")
    hospital = _make_hospital(db, lab)

    res = client.put(
        f"/hospital/{hospital.id}",
        headers=auth_headers(admin.id, lab.id, role="admin"),
        json={"name": "Renamed By Admin"},
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Renamed By Admin"


# ─── Explicit update boundary (allow-list) ─────────────────────────────────


def test_update_hospital_ignores_fields_outside_the_allow_list(db, make_lab):
    lab = make_lab("Hospital Sec Lab 6")
    hospital = _make_hospital(db, lab)
    original_code = hospital.code
    original_lab_id = hospital.lab_id

    # Simulates a future-loosened schema/direct service call carrying
    # fields that must never be settable through the generic update path.
    HospitalService.update_hospital(
        db, hospital_id=hospital.id, lab_id=lab.id, user_id=2,
        data={
            "name": "Legit Rename",
            "code": "HIJACKED",
            "lab_id": lab.id + 999,
            "id": 999999,
            "version": 999,
            "created_by": 999,
        },
    )

    db.refresh(hospital)
    assert hospital.name == "Legit Rename"       # allowed field applied
    assert hospital.code == original_code         # protected: unchanged
    assert hospital.lab_id == original_lab_id      # protected: unchanged
    assert hospital.id != 999999                    # protected: unchanged
    assert hospital.created_by != 999               # protected: unchanged


def test_update_hospital_cannot_be_used_to_smuggle_a_fake_version(db, make_lab):
    lab = make_lab("Hospital Sec Lab 7")
    hospital = _make_hospital(db, lab)
    assert hospital.version == 1

    HospitalService.update_hospital(
        db, hospital_id=hospital.id, lab_id=lab.id, user_id=1,
        data={"name": "X", "version": 12345},
    )

    db.refresh(hospital)
    assert hospital.version == 2  # server-incremented, not client-supplied


# ─── CAS / version ──────────────────────────────────────────────────────────


def test_update_hospital_increments_version(db, make_lab):
    lab = make_lab("Hospital Sec Lab 8")
    hospital = _make_hospital(db, lab)
    assert hospital.version == 1

    HospitalService.update_hospital(db, hospital_id=hospital.id, lab_id=lab.id, user_id=1, data={"name": "V2"})
    db.refresh(hospital)
    assert hospital.version == 2


def test_deactivate_hospital_increments_version(db, make_lab):
    lab = make_lab("Hospital Sec Lab 9")
    hospital = _make_hospital(db, lab)

    HospitalService.deactivate_hospital(db, hospital_id=hospital.id, lab_id=lab.id, user_id=1)
    db.refresh(hospital)
    assert hospital.is_active is False
    assert hospital.version == 2


# ─── Tenant isolation ───────────────────────────────────────────────────────


def test_update_hospital_rejects_cross_tenant_target(db, make_lab):
    lab_one = make_lab("Hospital Sec Lab 10a")
    lab_two = make_lab("Hospital Sec Lab 10b")
    hospital = _make_hospital(db, lab_one)

    from app.domain.exceptions import NotFoundError
    import pytest
    with pytest.raises(NotFoundError):
        HospitalService.update_hospital(
            db, hospital_id=hospital.id, lab_id=lab_two.id, user_id=1, data={"name": "Hijacked"},
        )

    db.refresh(hospital)
    assert hospital.name == "Test Hospital"  # unchanged


# ─── Audit ──────────────────────────────────────────────────────────────────


def test_update_hospital_audit_row_has_correct_tenant_and_resource(db, make_lab):
    lab = make_lab("Hospital Sec Lab 11")
    hospital = _make_hospital(db, lab)

    HospitalService.update_hospital(db, hospital_id=hospital.id, lab_id=lab.id, user_id=7, data={"name": "Audited"})

    entry = db.query(AuditLog).filter(AuditLog.action == "hospital.update").order_by(AuditLog.id.desc()).first()
    assert entry is not None
    assert entry.lab_id == lab.id
    assert entry.resource_type == "hospital"
    assert entry.resource_id == hospital.id
    assert entry.user_id == 7
