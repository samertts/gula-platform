"""Python's ``not`` on a mapped attribute turns whole query surfaces into ``WHERE false``.

``not Model.attr`` is not SQLAlchemy's ``~``.  ``Model.attr`` is an
``InstrumentedAttribute`` with no ``__bool__`` override, so ``bool(...)`` is the
default object truthiness (``True``) and ``not Model.attr`` is the plain Python
``False``.  SQLAlchemy accepts that literal into the WHERE clause and then folds
the conjunction, because ``a AND b AND false`` is ``false``.  The compiled
statement is ``WHERE false`` — and the ``lab_id`` predicate standing beside it is
eliminated too, so the query is not merely over-restricted, it is erased.

An AST sweep of ``backend/app`` finds this construct at 28 call sites, 20 of them
in ``app/lims/routes.py`` covering Department, Instrument, InstrumentModel,
Manufacturer, Specimen, Order, Panel, Result, QCProgram, Reagent, Consumable,
Lot, Supplier, Storage, ReferenceRangeDef, DeltaCheckRule, AutoValidationRule
and LabReport.  All 35 LIMS models are writable against the canonical schema, so
LIMS is schema-healthy: the module's read surface is dead purely by this defect.

``app/routes/admin.py::list_pending_labs`` is the same construct, and its effect
is that the lab-approval queue is permanently empty, so no registered lab can
ever be found for activation.

These tests prove the restored reads AND that restoring the predicate does not
widen them across tenants — before the fix the cross-tenant assertions passed
for the wrong reason, because ``WHERE false`` refuses everyone.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

import pytest
from sqlalchemy import text

from . import harness

pytestmark = harness.requires_postgres()

LAB_ID = 994901
OTHER_LAB_ID = 994902
PENDING_LAB_ID = 994903
ACTOR_ID = 74901
DEPT_CODE = "DEPT-HAEM"
OTHER_DEPT_CODE = "DEPT-OTHER"
BARCODE = "SPEC-994901-0001"
OTHER_BARCODE = "SPEC-994902-0001"


def _now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


@pytest.fixture()
def Session() -> Any:
    S = harness.session_factory(pool_size=4)
    yield S
    harness.dispose(S)


def _purge(S: Any) -> None:
    with S() as s:
        for lab in (LAB_ID, OTHER_LAB_ID, PENDING_LAB_ID):
            for table in ("lims_specimens", "lims_departments", "lab_orders", "patients"):
                s.execute(text(f"DELETE FROM {table} WHERE lab_id = :l"), {"l": lab})
            s.execute(text("DELETE FROM lab_users WHERE lab_id = :l"), {"l": lab})
            s.execute(text("DELETE FROM labs WHERE id = :l"), {"l": lab})
        s.commit()


@pytest.fixture()
def seeded(Session: Any) -> dict[str, Any]:
    """Two active labs with one department and one specimen each, plus one pending lab."""
    _purge(Session)
    now = _now()
    ids: dict[str, Any] = {}
    with Session() as s:
        for lab, name, active in ((LAB_ID, "LIMS Lab", True),
                                  (OTHER_LAB_ID, "Other LIMS Lab", True),
                                  (PENDING_LAB_ID, "Awaiting Approval Lab", False)):
            s.execute(text("INSERT INTO labs (id,name,is_active) VALUES (:l,:n,:a)"),
                      {"l": lab, "n": name, "a": active})
        s.execute(
            text("INSERT INTO lab_users (id,lab_id,name,email,password_hash,role,is_active,"
                 "perm_version) VALUES (:i,:l,'LIMS Actor',:e,'!synthetic','master_admin',true,1)"),
            {"i": ACTOR_ID, "l": LAB_ID, "e": f"lims-{uuid.uuid4().hex[:8]}@example.invalid"},
        )
        for lab, code in ((LAB_ID, DEPT_CODE), (OTHER_LAB_ID, OTHER_DEPT_CODE)):
            s.execute(
                text("INSERT INTO lims_departments (lab_id,code,name,version,is_deleted,"
                     "created_at,updated_at) VALUES (:l,:c,'Haematology',1,false,:n,:n)"),
                {"l": lab, "c": code, "n": now},
            )
        for lab, barcode in ((LAB_ID, BARCODE), (OTHER_LAB_ID, OTHER_BARCODE)):
            patient_id = s.execute(
                text("INSERT INTO patients (lab_id,full_name,phone) VALUES (:l,'Seed Patient',:p) "
                     "RETURNING id"),
                {"l": lab, "p": f"07{lab}{uuid.uuid4().hex[:4]}"},
            ).scalar_one()
            order_id = s.execute(
                text("INSERT INTO lab_orders (lab_id,patient_id) VALUES (:l,:p) RETURNING id"),
                {"l": lab, "p": patient_id},
            ).scalar_one()
            s.execute(
                text("INSERT INTO lims_specimens (lab_id,order_id,barcode,specimen_type,status,"
                     "version,is_deleted,created_at,updated_at) "
                     "VALUES (:l,:o,:b,'whole_blood','collected',1,false,:n,:n)"),
                {"l": lab, "o": order_id, "b": barcode, "n": now},
            )
            ids[f"order_{lab}"] = order_id
        # A soft-deleted department in the actor's lab: the predicate must still exclude it.
        s.execute(
            text("INSERT INTO lims_departments (lab_id,code,name,version,is_deleted,"
                 "created_at,updated_at) VALUES (:l,'DEPT-RETIRED','Retired',1,true,:n,:n)"),
            {"l": LAB_ID, "n": now},
        )
        s.commit()
    return ids


def _actor(lab_id: int = LAB_ID) -> harness.Actor:
    return harness.Actor(user_id=ACTOR_ID, lab_id=lab_id, role="master_admin")


def _get(Session: Any, path: str, *, actor: harness.Actor) -> Any:
    with harness.client(Session, actor) as client:
        return client.get(path)


def test_lims_departments_are_readable(Session: Any, seeded: dict[str, Any]) -> None:
    response = _get(Session, "/lims/departments", actor=_actor())
    assert response.status_code == 200, response.text[:300]
    codes = [d.get("code") for d in response.json()["departments"]]
    assert DEPT_CODE in codes, (
        f"a committed department in the caller's lab was not returned; codes={codes}"
    )


def test_lims_departments_exclude_other_tenants_and_soft_deleted(
    Session: Any, seeded: dict[str, Any]
) -> None:
    """The restored predicate must exclude the other lab AND the retired row.

    Before the fix this passed vacuously — ``WHERE false`` returns nothing, so
    every exclusion assertion held while the endpoint was useless.
    """
    codes = [d.get("code") for d in _get(Session, "/lims/departments", actor=_actor()).json()["departments"]]
    assert OTHER_DEPT_CODE not in codes, f"another lab's department leaked: {codes}"
    assert "DEPT-RETIRED" not in codes, f"a soft-deleted department was returned: {codes}"


def test_lims_specimens_are_readable(Session: Any, seeded: dict[str, Any]) -> None:
    response = _get(Session, "/lims/specimens", actor=_actor())
    assert response.status_code == 200, response.text[:300]
    body = response.json()
    barcodes = [sp.get("barcode") for sp in body["specimens"]]
    assert BARCODE in barcodes, (
        f"a committed specimen in the caller's lab was not returned; total={body['total']} "
        f"barcodes={barcodes}"
    )
    assert body["total"] >= 1, f"the count query is still erased: {body['total']}"
    assert OTHER_BARCODE not in barcodes, f"another lab's specimen leaked: {barcodes}"


def test_the_lab_approval_queue_is_not_empty(Session: Any, seeded: dict[str, Any]) -> None:
    """A registered but unapproved lab must be findable, or it can never be activated."""
    response = _get(Session, "/admin/labs/pending", actor=_actor())
    assert response.status_code == 200, response.text[:300]
    body = response.json()
    ids = [lab["id"] for lab in body["pending_labs"]]
    assert PENDING_LAB_ID in ids, (
        f"the pending lab was not listed, so it cannot be approved; body={str(body)[:300]}"
    )
    assert LAB_ID not in ids, f"an already-active lab appeared in the pending queue: {ids}"
