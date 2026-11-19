"""Regression fixtures for scripts/security/detect_missing_tenant_scope.py.

A static detector that can't be shown to detect anything (or that only
"detects" over a vacuous/empty run) is worthless — these are the mandatory
positive and negative controls for it.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts" / "security"))

from detect_missing_tenant_scope import scan_source  # noqa: E402

VULNERABLE_FIXTURE = '''
from fastapi import APIRouter, Depends

router = APIRouter()

@router.put("/widgets/{widget_id}/toggle")
def toggle_widget(widget_id: int, actor=Depends(require_manage_users), db=Depends(get_db)):
    """Same shape as the pre-fix F5 bug: a role/permission gate with no
    check that actor may act on THIS widget's owning tenant."""
    target = db.query(Widget).filter(Widget.id == widget_id).first()
    target.is_active = not target.is_active
    db.commit()
    return {"ok": True}
'''

SAFE_FIXTURE = '''
from fastapi import APIRouter, Depends

router = APIRouter()

@router.put("/widgets/{widget_id}/toggle")
def toggle_widget(widget_id: int, actor=Depends(require_manage_users), db=Depends(get_db)):
    target = db.query(Widget).filter(Widget.id == widget_id).first()
    require_own_lab(actor, target.lab_id)
    target.is_active = not target.is_active
    db.commit()
    return {"ok": True}
'''

READ_ONLY_FIXTURE = '''
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/widgets/{widget_id}")
def get_widget(widget_id: int, db=Depends(get_db)):
    return db.query(Widget).filter(Widget.id == widget_id).first()
'''

NO_RESOURCE_ID_FIXTURE = '''
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/widgets")
def create_widget(payload: dict, db=Depends(get_db)):
    return db.add(payload)
'''


def test_positive_control_flags_the_known_vulnerable_shape():
    hits = scan_source(VULNERABLE_FIXTURE, filename="vulnerable.py")
    assert len(hits) == 1
    assert hits[0].func == "toggle_widget"
    assert hits[0].method == "put"


def test_negative_control_does_not_flag_a_scoped_mutation():
    hits = scan_source(SAFE_FIXTURE, filename="safe.py")
    assert hits == []


def test_get_routes_are_never_flagged_even_with_a_resource_id():
    hits = scan_source(READ_ONLY_FIXTURE, filename="readonly.py")
    assert hits == []


def test_mutating_routes_without_a_resource_id_are_not_flagged():
    hits = scan_source(NO_RESOURCE_ID_FIXTURE, filename="norid.py")
    assert hits == []


def test_scan_is_not_vacuously_true_over_the_real_admin_module():
    """The detector must actually discriminate on the real codebase, not
    just its own fixtures: admin.py's toggle_user/change_user_role now carry
    can_manage_user() (F5's fix) and must NOT be flagged, while feeding it
    the pre-fix shape (can_manage_user always returning True, no lab check)
    would have been flagged had this detector existed then.
    """
    admin_py = (
        pathlib.Path(__file__).resolve().parents[1] / "app" / "routes" / "admin.py"
    )
    hits = scan_source(admin_py.read_text(), filename=str(admin_py))
    flagged_funcs = {h.func for h in hits}
    assert "toggle_user" not in flagged_funcs
    assert "change_user_role" not in flagged_funcs
