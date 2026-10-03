"""One laboratory test, two result rows, two FHIR Observations, no correlation.

IA-062. `lab_results` and `lims_results` both carry
`order_id -> lab_orders.id NOT NULL CASCADE` and neither references the other.
This drives both stores for the same order and the same test_code and records
what a FHIR consumer receives from each.

Measured structure (static, from the ORM):
    lab_results.order_id   -> lab_orders.id   NOT NULL  CASCADE   (models/lab_result.py:31)
    lims_results.order_id  -> lab_orders.id   NOT NULL  CASCADE   (lims/models.py:1062)
    lims_results unique    -> (specimen_id, test_code)            (lims/models.py:1134)
    references between the two stores: none
"""
from __future__ import annotations

import pytest

from tests.conftest import auth_headers

TEST_CODE = "GLU"


@pytest.fixture()
def both_stores(db, make_lab, make_lab_user, client):
    """One order; one row in each result store for the same test_code."""
    from app.lims.models import Order as LimsOrder
    from app.lims.models import Result as LimsResult
    from app.lims.models import Specimen
    from app.models.lab_order import LabOrder
    from app.models.lab_result import LabResult
    from app.models.patient import Patient

    lab = make_lab()
    user = make_lab_user(lab_id=lab.id, role="admin")
    patient = Patient(lab_id=lab.id, full_name="Dual Store", phone="07712345678")
    db.add(patient)
    db.flush()
    order = LabOrder(lab_id=lab.id, patient_id=patient.id)
    db.add(order)
    db.flush()

    # lab_results has NO lab_id: its tenancy is transitive through
    # order_id -> lab_orders.lab_id, unlike lims_results which carries its own.
    core = LabResult(
        order_id=order.id,
        test_name="Glucose",
        value=5.4,
        unit="mmol/L",
        token="IA062-CORE-TOKEN-0001",
    )
    db.add(core)

    lims_order = LimsOrder(order_id=order.id, lab_id=lab.id, accession_number="ACC-DUAL-1")
    db.add(lims_order)
    specimen = Specimen(
        lab_id=lab.id, order_id=order.id, barcode="BC-DUAL-1", specimen_type="serum",
    )
    db.add(specimen)
    db.flush()
    lims = LimsResult(
        lab_id=lab.id,
        specimen_id=specimen.id,
        order_id=order.id,
        test_code=TEST_CODE,
        test_name="Glucose",
        value_numeric=9.9,          # deliberately different from the core row
        unit="mmol/L",
    )
    db.add(lims)
    db.flush()

    return {
        "lab": lab, "patient": patient, "order": order, "core": core,
        "lims": lims, "specimen": specimen, "lims_order": lims_order,
        "headers": auth_headers(user_id=user.id, lab_id=lab.id, role="admin"),
    }


def test_both_rows_persist_for_one_order_and_one_test(db, both_stores):
    """No constraint links or deduplicates the two stores."""
    from app.lims.models import Result as LimsResult
    from app.models.lab_result import LabResult

    order_id = both_stores["order"].id
    core_rows = db.query(LabResult).filter(LabResult.order_id == order_id).all()
    lims_rows = db.query(LimsResult).filter(LimsResult.order_id == order_id).all()

    assert len(core_rows) == 1
    assert len(lims_rows) == 1
    # same order, same analyte, different values -- both accepted
    assert core_rows[0].value == 5.4
    assert lims_rows[0].value_numeric == 9.9
    print(f"\n[dual] order={order_id} core={core_rows[0].value} "
          f"lims={lims_rows[0].value_numeric} -- both persisted")


def test_no_correlation_identity_exists_between_the_stores(db, both_stores):
    """The reconciliation question, asked of the schema itself."""
    from app.lims.models import Result as LimsResult
    from app.models.lab_result import LabResult

    core_cols = set(LabResult.__table__.c.keys())
    lims_cols = set(LimsResult.__table__.c.keys())

    # neither table has a column pointing at the other
    assert not {c for c in core_cols if "lims" in c}, core_cols
    assert not {c for c in lims_cols if c in ("lab_result_id", "core_result_id")}, lims_cols

    # no foreign key in either direction
    core_targets = {fk.target_fullname for c in LabResult.__table__.c for fk in c.foreign_keys}
    lims_targets = {fk.target_fullname for c in LimsResult.__table__.c for fk in c.foreign_keys}
    assert not any(t.startswith("lims_results") for t in core_targets), core_targets
    assert not any(t.startswith("lab_results") for t in lims_targets), lims_targets

    # the only shared anchor is the parent order
    assert "lab_orders.id" in core_targets
    assert "lab_orders.id" in lims_targets

    # and the two stores do not even model tenancy the same way
    assert "lab_id" not in core_cols, "lab_results gained a lab_id -- re-measure"
    assert "lab_id" in lims_cols
    print("\n[tenancy] lab_results: transitive via order; lims_results: own lab_id")
    print(f"\n[correlation] shared anchor only: lab_orders.id   "
          f"core->{sorted(core_targets)}  lims->{sorted(lims_targets)}")


def test_both_stores_serve_a_fhir_observation_for_the_same_order(client, both_stores):
    """Two Observations, two id namespaces, one physical laboratory event."""
    h = both_stores["headers"]

    lims_response = client.get(
        f"/lims/results/{both_stores['lims'].id}/fhir", headers=h,
    )
    core_response = client.get(
        f"/fhir/Observation/{both_stores['core'].id}", headers=h,
    )

    print(f"\n[fhir] /lims/results/{both_stores['lims'].id}/fhir -> {lims_response.status_code}")
    print(f"[fhir] /fhir/Observation/{both_stores['core'].id} -> {core_response.status_code}")

    assert lims_response.status_code == 200, lims_response.text
    lims_obs = lims_response.json()
    assert lims_obs["resourceType"] == "Observation"
    assert lims_obs["id"] == f"lims-obs-{both_stores['lims'].id}"

    if core_response.status_code != 200:
        pytest.skip(
            f"/fhir/Observation returned {core_response.status_code}: "
            f"{core_response.text[:140]} -- the LIMS half of the divergence stands either way"
        )

    core_obs = core_response.json()
    assert core_obs["resourceType"] == "Observation"
    # disjoint id namespaces: no collision, and no way to tell they describe one event
    assert str(core_obs["id"]) != lims_obs["id"]
    print(f"[fhir] core id={core_obs['id']!r}  lims id={lims_obs['id']!r}  "
          f"core subject={core_obs.get('subject')}  lims subject={lims_obs.get('subject')}")


def test_the_lims_unique_constraint_cannot_see_the_core_store(db, both_stores):
    """(specimen_id, test_code) is scoped inside LIMS, so it cannot deduplicate."""
    from app.lims.models import Result as LimsResult

    indexes = {
        idx.name: (sorted(c.name for c in idx.columns), idx.unique)
        for idx in LimsResult.__table__.indexes
    }
    unique = {n: cols for n, (cols, uq) in indexes.items() if uq}
    assert unique, indexes
    # every unique index is scoped to LIMS-owned columns only
    for name, cols in unique.items():
        assert "order_id" not in cols or "specimen_id" in cols, (name, cols)
        assert not any(c.startswith("lab_result") for c in cols), (name, cols)
    print(f"\n[unique] {unique}")


def test_a_second_lims_result_for_the_same_specimen_and_test_is_refused(db, both_stores):
    """What the LIMS constraint DOES protect, recorded so the gap is precise."""
    from app.lims.models import Result as LimsResult

    duplicate = LimsResult(
        lab_id=both_stores["lab"].id,
        specimen_id=both_stores["specimen"].id,
        order_id=both_stores["order"].id,
        test_code=TEST_CODE,
        test_name="Glucose",
        value_numeric=1.1,
        unit="mmol/L",
    )
    db.add(duplicate)
    with pytest.raises(Exception) as excinfo:
        db.flush()
    print(f"\n[intra-lims duplicate] refused: {type(excinfo.value).__name__}")
    db.rollback()
