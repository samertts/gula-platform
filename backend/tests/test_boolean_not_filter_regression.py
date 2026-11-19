"""Regression guard: the repo-wide `not X.field` vs `~X.field` boolean-
filter defect (Batch 5), covering one representative LIVE site per
affected domain.

Every site below used Python's `not` applied directly to a SQLAlchemy
column/attribute inside a `.filter()`/`.filter_by()` call. Python
evaluates `not <attribute>` immediately at query-*build* time (a bare
column has no `__bool__` override, so `bool(Model.column)` is always
`True`, making `not Model.column` the literal Python `False`), and
`.filter(False)` compiles to `WHERE 0 = 1` -- the query unconditionally
matches zero rows, regardless of what data actually exists. Fixed with
SQLAlchemy's `~` boolean-NOT operator everywhere. See
scripts/security/boolean_not_filter_guard.py for the deterministic
detector that found all 28 repo-wide occurrences (23 beyond the 5
originally known), and docs/security/AUTHORIZATION_GAP_REGISTER.md for
the full per-site evidence.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from tests.conftest import auth_headers


def test_lims_list_departments_finds_a_created_department(client, make_lab, make_lab_user):
    """LIMS (app/lims/routes.py) had 20 identically-shaped occurrences --
    every list/count route filtering `not Model.is_deleted` always
    returned empty/zero. This is app/lims/routes.py's own do-not-repeat
    "already audited" domain from a prior batch -- re-verified here, not
    assumed still correct."""
    lab = make_lab("Boolean Filter LIMS Lab")
    user = make_lab_user(lab.id, role="admin")
    headers = auth_headers(user.id, lab.id, role="admin")

    create_resp = client.post(
        "/lims/departments",
        headers=headers,
        json={"code": "BF1", "name": "Boolean Filter Dept"},
    )
    assert create_resp.status_code == 201, create_resp.text

    list_resp = client.get("/lims/departments", headers=headers)
    assert list_resp.status_code == 200
    names = [d["name"] for d in list_resp.json()["departments"]]
    assert "Boolean Filter Dept" in names, (
        "list_departments returned empty despite a real, just-created, "
        "non-deleted department -- the not-vs-~ filter bug reproduced"
    )


def test_pharmacy_auto_quarantine_finds_an_expired_batch(db, make_lab):
    """app/pharmacy/inventory.py::auto_quarantine_expired had
    `not DrugBatch.is_quarantined` sitting next to a correct
    `~DrugBatch.is_deleted` in the same filter() call -- confirming this
    was an oversight, not an intentional choice."""
    from app.pharmacy.inventory import ExpiryMonitoringService
    from app.pharmacy.models import DrugBatch, DrugCatalog

    lab = make_lab("Boolean Filter Pharmacy Lab")
    catalog = DrugCatalog(lab_id=lab.id, code="BF-DRUG-1", name="Test Drug")
    db.add(catalog)
    db.flush()

    batch = DrugBatch(
        lab_id=lab.id,
        drug_catalog_id=catalog.id,
        batch_number="BF-BATCH-1",
        expiry_date=date.today() - timedelta(days=5),
        quantity_initial=100,
        quantity_remaining=50,
        is_quarantined=False,
    )
    db.add(batch)
    db.commit()

    service = ExpiryMonitoringService(db, lab_id=lab.id)
    quarantined_count = service.auto_quarantine_expired()

    assert quarantined_count == 1, (
        "auto_quarantine_expired found 0 expired batches despite one real, "
        "expired, non-deleted, non-quarantined batch existing -- the "
        "not-vs-~ filter bug reproduced"
    )
    db.refresh(batch)
    assert batch.is_quarantined is True


def test_pharmacy_expiry_alerts_route_finds_a_real_batch(client, db, make_lab, make_lab_user):
    """GET /pharmacy/dashboard/expiry-alerts (app/pharmacy/routes.py:1355
    -> PharmacyService.get_expiry_alerts -> get_expiring_batches,
    app/pharmacy/services.py:198) is a LIVE route backed by this same
    defect -- pharmacists could never see near-expiry medication needing
    action. (Note: GET /pharmacy/batches/expiring, also backed by the
    same fixed method, is shadowed by the earlier-registered
    /batches/{batch_id} route -- a separate, pre-existing route-ordering
    defect, out of this batch's bound, not fixed here.)"""
    from app.pharmacy.models import DrugBatch, DrugCatalog

    lab = make_lab("Boolean Filter Pharmacy Route Lab")
    user = make_lab_user(lab.id, role="pharmacist")

    catalog = DrugCatalog(lab_id=lab.id, code="BF-DRUG-2", name="Test Drug 2")
    db.add(catalog)
    db.flush()
    batch = DrugBatch(
        lab_id=lab.id,
        drug_catalog_id=catalog.id,
        batch_number="BF-BATCH-2",
        expiry_date=date.today() + timedelta(days=30),
        quantity_initial=100,
        quantity_remaining=40,
        is_quarantined=False,
    )
    db.add(batch)
    db.commit()

    resp = client.get(
        "/pharmacy/dashboard/expiry-alerts",
        headers=auth_headers(user.id, lab.id, role="pharmacist"),
    )
    assert resp.status_code == 200, resp.text
    batch_ids = [a["batch_id"] for a in resp.json()]
    assert batch.id in batch_ids, (
        "GET /pharmacy/dashboard/expiry-alerts did not find a real, "
        "non-deleted, non-quarantined, expiring batch -- the not-vs-~ "
        "filter bug reproduced"
    )


def test_radiology_revoke_share_succeeds_for_a_real_share(db):
    """app/radiology/pacs.py::ImageSharingService.revoke_share had
    `not ImageShare.is_revoked` -- the route (DELETE
    /radiology/sharing/{share_id}) always got a 404 "already revoked"
    for ANY share, valid or not, because revoke_share itself could never
    find the row to revoke."""
    from app.radiology.pacs import ImageSharingService

    sharing = ImageSharingService(db)
    share = sharing.create_share(
        study_uid="1.2.3.boolean.filter.test",
        shared_by="1",
        shared_with="test@example.com",
        share_type="link",
        expires_in_hours=24,
    )

    revoked = sharing.revoke_share(share.id)
    assert revoked is True, (
        "revoke_share returned False for a real, non-revoked share -- "
        "the not-vs-~ filter bug reproduced"
    )

    db.refresh(share)
    assert share.is_revoked is True


def test_admin_pending_labs_lists_an_inactive_lab(client, make_lab, make_lab_user):
    """app/routes/admin.py::list_pending_labs (GET /admin/labs/pending)
    had `not Lab.is_active` -- the pending-approval dashboard always
    showed zero labs, even when real labs were awaiting activation."""
    pending_lab = make_lab("Boolean Filter Pending Lab", is_active=False)
    admin_lab = make_lab("Boolean Filter Admin Lab")
    admin = make_lab_user(admin_lab.id, role="master_admin")

    resp = client.get(
        "/admin/labs/pending",
        headers=auth_headers(admin.id, admin_lab.id, role="master_admin"),
    )
    assert resp.status_code == 200
    body = resp.json()
    found = any(row["id"] == pending_lab.id for row in body["pending_labs"])
    assert found, (
        "GET /admin/labs/pending did not list a real, existing, inactive "
        "lab -- the not-vs-~ filter bug reproduced"
    )
