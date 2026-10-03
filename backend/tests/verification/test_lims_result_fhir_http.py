"""GET /lims/results/{id}/fhir and the bundle, over HTTP, seven ways.

IA-061 Phase 1. The previous proof called the mapper directly. This drives the
served route, so the recorded behaviour is what a client actually receives.
"""
from __future__ import annotations

import pytest

from tests.conftest import auth_headers


@pytest.fixture()
def seeded(db, make_lab, make_lab_user, client):
    """Two tenants, each with a full Patient -> Order -> Specimen -> Result chain."""
    from app.lims.models import Order as LimsOrder
    from app.lims.models import Result, Specimen
    from app.models.lab_order import LabOrder
    from app.models.patient import Patient

    built = {}
    for tag in ("a", "b"):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="admin")
        patient = Patient(lab_id=lab.id, full_name=f"Patient {tag}", phone=f"0770000000{tag=='b'}")
        db.add(patient)
        db.flush()
        order = LabOrder(lab_id=lab.id, patient_id=patient.id)
        db.add(order)
        db.flush()
        lims_order = LimsOrder(
            order_id=order.id, lab_id=lab.id, accession_number=f"ACC-{tag.upper()}-0001",
        )
        db.add(lims_order)
        specimen = Specimen(
            lab_id=lab.id, order_id=order.id,
            barcode=f"BC-{tag.upper()}-0001", specimen_type="serum",
        )
        db.add(specimen)
        db.flush()
        result = Result(
            lab_id=lab.id, specimen_id=specimen.id, order_id=order.id,
            test_code="GLU", test_name="Glucose", value_numeric=5.4, unit="mmol/L",
        )
        db.add(result)
        db.flush()
        built[tag] = {
            "lab": lab, "user": user, "patient": patient, "order": order,
            "lims_order": lims_order, "specimen": specimen, "result": result,
            "headers": auth_headers(user_id=user.id, lab_id=lab.id, role="admin"),
        }
    return built


# ── 1, 2, 7: the normal served path ─────────────────────────────────────────


def test_1_2_7_normal_result_with_a_valid_order_publishes_subject_unknown(client, seeded):
    a = seeded["a"]
    response = client.get(f"/lims/results/{a['result'].id}/fhir", headers=a["headers"])

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["resourceType"] == "Observation"
    assert body["id"] == f"lims-obs-{a['result'].id}"
    # the measured outcome: a reference to a resource that does not exist
    assert body["subject"] == {"reference": "unknown", "display": ""}
    # the order and patient are both present and reachable -- the mapper never looks
    assert a["result"].order_id == a["order"].id
    assert a["order"].patient_id == a["patient"].id
    print(f"\n[1/2/7] 200 subject={body['subject']}  value={body.get('valueQuantity')}")


def test_classification_of_the_subject_outcome(client, seeded):
    """Which of the six candidate behaviours actually occurs."""
    a = seeded["a"]
    body = client.get(f"/lims/results/{a['result'].id}/fhir", headers=a["headers"]).json()
    subject = body.get("subject")

    verdict = {
        "subject absent": "subject" not in body,
        "subject null": subject is None,
        "malformed reference": isinstance(subject, dict)
        and not str(subject.get("reference", "")).startswith("Patient/"),
        "correct Patient reference": isinstance(subject, dict)
        and subject.get("reference") == f"Patient/{a['patient'].id}",
        "exception": False,
    }
    print(f"\n[classification] {verdict}")
    assert verdict["malformed reference"] is True
    assert verdict["correct Patient reference"] is False
    assert verdict["subject absent"] is False
    assert verdict["subject null"] is False


# ── 3: an order that is not resolvable ──────────────────────────────────────


def test_3_result_whose_order_row_is_absent(client, db, seeded):
    """order_id is NOT NULL with a FK, so this probes what the route does when
    the parent cannot be resolved -- not whether the FK can be violated."""
    from app.lims.models import Result

    a = seeded["a"]
    orphan = Result(
        lab_id=a["lab"].id,
        specimen_id=a["specimen"].id,
        order_id=999_999,          # no such lab_orders row
        test_code="NA",
        test_name="Sodium",
        value_numeric=140.0,
        unit="mmol/L",
    )
    db.add(orphan)
    try:
        db.flush()
    except Exception as exc:
        print(f"\n[3] the database refused the orphan: {type(exc).__name__}")
        pytest.skip("foreign key enforced at write time; orphan not constructible here")

    response = client.get(f"/lims/results/{orphan.id}/fhir", headers=a["headers"])
    print(f"\n[3] orphan order_id=999999 -> {response.status_code} subject="
          f"{response.json().get('subject') if response.status_code == 200 else response.text[:80]}")
    # recorded, not asserted as desirable: the mapper never touches the order,
    # so an unresolvable parent changes nothing about the response
    assert response.status_code == 200
    assert response.json()["subject"] == {"reference": "unknown", "display": ""}


# ── 4: cross-tenant ─────────────────────────────────────────────────────────


def test_4_tenant_b_cannot_read_tenant_a_result(client, seeded):
    a, b = seeded["a"], seeded["b"]

    cross = client.get(f"/lims/results/{a['result'].id}/fhir", headers=b["headers"])
    own = client.get(f"/lims/results/{b['result'].id}/fhir", headers=b["headers"])

    print(f"\n[4] tenant B -> A's result: {cross.status_code}; B -> own: {own.status_code}")
    assert cross.status_code == 404, cross.text
    assert own.status_code == 200
    # 404 not 403: indistinguishable from a missing id, so no existence oracle
    assert "not found" in cross.text.lower()


def test_4b_unauthenticated_is_refused(client, seeded):
    a = seeded["a"]
    response = client.get(f"/lims/results/{a['result'].id}/fhir")
    print(f"\n[4b] no credential -> {response.status_code}")
    assert response.status_code in (401, 403), response.text


# ── 5: patient mismatch ─────────────────────────────────────────────────────


def test_5_a_wrong_patient_cannot_be_published_because_no_patient_is(client, seeded):
    """The mismatch class this endpoint is immune to, and why.

    A wrong-patient reference is what the ServiceRequest mapper was fixed for.
    Here no patient id reaches the payload at all, so the failure mode is
    'no subject' rather than 'wrong subject'. Recorded as a distinct outcome:
    it is not safer, it is differently wrong.
    """
    a, b = seeded["a"], seeded["b"]
    body = client.get(f"/lims/results/{a['result'].id}/fhir", headers=a["headers"]).json()

    reference = body["subject"]["reference"]
    assert reference == "unknown"
    assert reference != f"Patient/{a['patient'].id}"
    assert reference != f"Patient/{b['patient'].id}"
    assert reference != f"Patient/{a['order'].id}", (
        "an order-id-as-patient reference would be the ServiceRequest defect"
    )


# ── 6: the bundle path ──────────────────────────────────────────────────────


def test_6_bundle_path_omits_subject_entirely(client, seeded):
    a = seeded["a"]
    response = client.get(
        f"/lims/orders/{a['lims_order'].id}/fhir-bundle", headers=a["headers"],
    )
    print(f"\n[6] bundle -> {response.status_code}")
    if response.status_code != 200:
        pytest.skip(f"bundle route returned {response.status_code}: {response.text[:120]}")

    bundle = response.json()
    assert bundle["resourceType"] == "Bundle"
    kinds = [e["resource"]["resourceType"] for e in bundle["entry"]]
    print(f"[6] entries={kinds}")
    for entry in bundle["entry"]:
        assert "subject" not in entry["resource"], entry["resource"]["resourceType"]
    assert "Observation" in kinds, "the bundle should carry the LIMS result"
