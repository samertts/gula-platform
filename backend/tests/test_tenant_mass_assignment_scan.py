"""Regression fixtures for two false positives found while triaging
scripts/tenant_mass_assignment_scan.py's real output against this branch's
own codebase (not hypothetical — both are named, real functions):

  1. The "update" shape recorded every `for k,v in data.items(): setattr(...)`
     as `<setattr target>` without checking whether the mutated object's
     class actually has a `lab_id` column. backend/app/services/ehr_service.py
     ::update_clinical_note was reported ASSIGNABLE even though ClinicalNote
     has no lab_id at all — the model is scoped by patient_id, not lab_id.
  2. The same shape did not recognize the exclusion-guard pattern
     (`if k not in (..., "lab_id", ...): setattr(...)`) as re-asserting the
     tenant, only a reassignment *after* the copy.
     backend/app/routes/care_continuum.py::api_update_primary_care_encounter
     excludes lab_id exactly this way and was still reported ASSIGNABLE.

Both are fixed in the scanner itself (_setattr_target_model,
_excludes_lab_id_from_copy) rather than by hand-waiving the two call sites,
since the same shapes recur elsewhere in this codebase.
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts"))

import tenant_mass_assignment_scan as scan  # noqa: E402


def _sites_for(source: str, filename: str = "module.py"):
    import ast

    fake_path = scan.ROOT / filename
    tree = ast.parse(source, filename=str(fake_path))
    finder = scan.SiteFinder(fake_path, {"Widget": "x:1"})
    finder.visit(tree)
    schemas = scan.pydantic_fields([(fake_path, tree)])
    return scan.classify(finder.sites, [(fake_path, tree)], schemas, {"Widget": "x:1"})


# ─── false positive 1: update-shape model has no lab_id column ─────────────

NON_TENANT_MODEL_UPDATE = '''
def get_note(db, note_id):
    return db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()

def update_note(db, note_id, data: dict) -> "ClinicalNote":
    note = get_note(db, note_id)
    for k, v in data.items():
        setattr(note, k, v)
    return note
'''


def test_update_shape_is_not_flagged_when_the_model_has_no_lab_id():
    sites = _sites_for(NON_TENANT_MODEL_UPDATE)
    assert len(sites) == 1
    assert sites[0]["verdict"].startswith("NOT_TENANT_SCOPED")
    assert sites[0]["model"] == "ClinicalNote"


# ─── false positive 2: lab_id excluded from the copy via a guard ───────────

EXCLUSION_GUARD_UPDATE = '''
def update_widget(db, widget_id, data: dict):
    w = db.query(Widget).filter(Widget.id == widget_id).first()
    for k, v in data.items():
        if hasattr(w, k) and k not in ("id", "lab_id", "created_at"):
            setattr(w, k, v)
    return w
'''


def test_update_shape_is_not_flagged_when_lab_id_is_excluded_from_the_copy():
    sites = _sites_for(EXCLUSION_GUARD_UPDATE)
    assert len(sites) == 1
    assert sites[0]["verdict"].startswith("BLOCKED"), sites[0]["verdict"]
    assert "excluded" in sites[0]["verdict"]


# ─── positive control: the scanner must still catch the real shape ────────

REAL_TENANT_MODEL_UPDATE = '''
def update_widget(db, widget_id, data: dict) -> "Widget":
    w = db.query(Widget).filter(Widget.id == widget_id).first()
    for k, v in data.items():
        setattr(w, k, v)
    return w
'''


def test_update_shape_is_still_flagged_for_a_real_tenant_scoped_model():
    sites = _sites_for(REAL_TENANT_MODEL_UPDATE)
    assert len(sites) == 1
    assert sites[0]["verdict"].startswith("ASSIGNABLE"), sites[0]["verdict"]
    assert sites[0]["model"] == "Widget"


def test_update_shape_still_recognizes_an_explicit_reassignment_as_safe():
    source = '''
def update_widget(db, widget_id, data: dict, lab_id: int) -> "Widget":
    w = db.query(Widget).filter(Widget.id == widget_id).first()
    for k, v in data.items():
        setattr(w, k, v)
    w.lab_id = lab_id
    return w
'''
    sites = _sites_for(source)
    assert len(sites) == 1
    assert sites[0]["verdict"].startswith("BLOCKED"), sites[0]["verdict"]


# ─── the real sites that motivated this, checked directly ─────────────────

def test_the_real_ehr_service_sites_are_all_reclassified():
    """Regression pin: re-running the actual scan against this repo must
    not report any of ehr_service.py's 17 update functions as ASSIGNABLE.
    """
    trees = list(scan.modules())
    models = scan.tenant_models(trees)
    finder_sites = []
    for path, tree in trees:
        finder = scan.SiteFinder(path, models)
        finder.visit(tree)
        finder_sites.extend(finder.sites)
    schemas = scan.pydantic_fields(trees)
    sites = scan.classify(finder_sites, trees, schemas, models)

    ehr_sites = [s for s in sites if s["file"] == "backend/app/services/ehr_service.py"]
    assert len(ehr_sites) >= 15, "the ehr_service.py fixture set moved; re-check this pin"
    still_assignable = [s for s in ehr_sites if s["verdict"].startswith("ASSIGNABLE")]
    assert still_assignable == [], (
        f"ehr_service.py sites still reported ASSIGNABLE after the model-"
        f"resolution fix: {still_assignable}"
    )


def test_the_real_care_continuum_site_is_reclassified_as_blocked():
    trees = list(scan.modules())
    models = scan.tenant_models(trees)
    finder_sites = []
    for path, tree in trees:
        finder = scan.SiteFinder(path, models)
        finder.visit(tree)
        finder_sites.extend(finder.sites)
    schemas = scan.pydantic_fields(trees)
    sites = scan.classify(finder_sites, trees, schemas, models)

    cc_sites = [s for s in sites if s["file"] == "backend/app/routes/care_continuum.py"]
    assert len(cc_sites) == 1
    assert cc_sites[0]["verdict"].startswith("BLOCKED"), cc_sites[0]["verdict"]
