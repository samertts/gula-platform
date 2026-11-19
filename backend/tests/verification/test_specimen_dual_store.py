"""Core Sample and LIMS Specimen: two live specimen stores, one barcode space.

IA-066. Both tables carry a unique `barcode` and both anchor to
`lab_orders.id`. Neither references the other. This drives both for one order
and records whether the same physical specimen can exist twice.
"""
from __future__ import annotations

import pytest

BARCODE = "SPEC-DUAL-0001"


@pytest.fixture()
def one_order(db, make_lab, make_lab_user):
    from app.models.lab_order import LabOrder
    from app.models.patient import Patient

    lab = make_lab()
    user = make_lab_user(lab_id=lab.id, role="admin")
    patient = Patient(lab_id=lab.id, full_name="Specimen Probe", phone="07700000700")
    db.add(patient)
    db.flush()
    order = LabOrder(lab_id=lab.id, patient_id=patient.id)
    db.add(order)
    db.flush()
    return {"lab": lab, "user": user, "patient": patient, "order": order}


def test_both_stores_declare_a_unique_barcode_in_separate_tables():
    from app.lims.models import Specimen
    from app.models.sample import Sample

    assert Sample.__table__.c.barcode.unique is True
    assert Specimen.__table__.c.barcode.unique is True
    assert Sample.__table__.name == "samples"
    assert Specimen.__table__.name == "lims_specimens"
    # neither references the other
    sample_targets = {fk.target_fullname for c in Sample.__table__.c for fk in c.foreign_keys}
    spec_targets = {fk.target_fullname for c in Specimen.__table__.c for fk in c.foreign_keys}
    assert not any(t.startswith("lims_specimens") for t in sample_targets), sample_targets
    assert not any(t.startswith("samples") for t in spec_targets), spec_targets
    assert "lab_orders.id" in sample_targets and "lab_orders.id" in spec_targets
    print(f"\n[barcode] samples->{sorted(sample_targets)}  lims_specimens->{sorted(spec_targets)}")


def test_the_same_barcode_can_exist_once_in_each_store(db, one_order):
    """Uniqueness is per table, so one physical label yields two rows."""
    from app.lims.models import Specimen
    from app.models.sample import Sample

    o = one_order
    sample = Sample(order_id=o["order"].id, barcode=BARCODE, sample_type="serum")
    db.add(sample)
    specimen = Specimen(
        lab_id=o["lab"].id, order_id=o["order"].id, barcode=BARCODE, specimen_type="serum",
    )
    db.add(specimen)
    db.flush()   # no cross-table constraint to violate

    assert sample.id is not None and specimen.id is not None
    assert sample.barcode == specimen.barcode == BARCODE
    print(f"\n[dual specimen] barcode={BARCODE!r} exists as samples.id={sample.id} "
          f"AND lims_specimens.id={specimen.id} -- no correlation column")


def test_no_shared_identifier_correlates_the_two_specimen_rows(db, one_order):
    from app.lims.models import Specimen
    from app.models.sample import Sample

    sample_cols = set(Sample.__table__.c.keys())
    spec_cols = set(Specimen.__table__.c.keys())
    assert not {c for c in sample_cols if "specimen" in c}, sample_cols
    assert not {c for c in spec_cols if c in ("sample_id", "core_sample_id")}, spec_cols
    # the overlap is descriptive, not identifying
    print(f"\n[correlation] shared column names: {sorted(sample_cols & spec_cols)}")
    assert "barcode" in sample_cols & spec_cols, "barcode is the only identifying overlap"


def test_a_duplicate_barcode_within_one_store_is_refused(db, one_order):
    """What the per-table constraint does protect, so the gap is precise."""
    from app.models.sample import Sample

    o = one_order
    db.add(Sample(order_id=o["order"].id, barcode="SPEC-SAME-1", sample_type="serum"))
    db.flush()
    db.add(Sample(order_id=o["order"].id, barcode="SPEC-SAME-1", sample_type="plasma"))
    with pytest.raises(Exception) as excinfo:
        db.flush()
    print(f"\n[intra-store duplicate] refused: {type(excinfo.value).__name__}")
    db.rollback()


def test_the_lims_specimen_docstring_claims_to_replace_the_core_sample():
    """The module's own stated intent, pinned against the live core model."""
    import inspect

    from app.lims.models import Specimen
    from app.models.sample import Sample

    doc = inspect.getdoc(Specimen) or ""
    assert "replaces existing Sample model" in doc, doc[:200]
    # and yet the core model is still written by served routes
    assert Sample.__table__ is not None
    print(f"\n[intent] Specimen docstring: {doc.splitlines()[0]!r}")


def test_core_sample_is_still_written_by_served_routes():
    """'Replaces' is not what the route tree does."""
    import pathlib
    import re

    root = pathlib.Path(__file__).resolve().parents[2] / "app"
    writers = []
    for rel in ("routes/samples.py", "routes/device_results.py", "routes/test_results.py"):
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(errors="replace")
        if re.search(r"\bSample\s*\(", text) or "models.sample import" in text:
            writers.append(rel)
    assert writers, "no served route writes the core Sample -- re-measure the claim"
    print(f"\n[core writers] {writers}")
