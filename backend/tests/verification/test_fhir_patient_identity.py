"""Patient identity across every laboratory FHIR path that builds a subject.

IA-063 and IA-064, plus the negative results that bound them.

Three distinct reference builders exist, with three shapes:

    app/routes/ehr_fhir.py:88   _patient_ref(id)        -> {reference, type}
    app/lims/fhir_mappers.py:27 _fhir_reference(ref)    -> {reference, display}
    app/national/api/routes/interop.py:118
                                _patient_reference(p,c) -> {reference, identifier, display}

FHIR allows any subset of Reference fields, so differing shapes are an
inconsistency rather than invalidity, and are recorded as such. What matters is
whether the *id inside the reference* identifies the patient, and whether all
three agree about what kind of identifier `Patient/{x}` carries.
"""
from __future__ import annotations

import pytest

from tests.conftest import auth_headers

ORU = (
    "MSH|^~\\&|LAB|FAC|GULA|GULA|20260101120000||ORU^R01|{control}|P|2.5\r"
    "PID|1||{pid3}||DOE^JANE\r"
    "OBR|1||{control}|CBC^Complete Blood Count\r"
    "OBX|1|NM|GLU^Glucose||5.4|mmol/L|3.9-5.8|N|||F\r"
)


@pytest.fixture()
def actor(db, make_lab, make_lab_user, client):
    lab = make_lab()
    user = make_lab_user(lab_id=lab.id, role="master_admin")
    db.flush()
    return auth_headers(user_id=user.id, lab_id=lab.id, role="master_admin")


# ── Phase 9: do the three helpers agree on what Patient/{x} means? ───────────


def test_the_three_reference_builders_have_three_different_shapes():
    import inspect

    from app.lims.fhir_mappers import _fhir_reference
    from app.routes.ehr_fhir import _patient_ref

    lims_shape = set(_fhir_reference("Patient/1").keys())
    core_shape = set(_patient_ref("1").keys())

    assert core_shape == {"reference", "type"}, core_shape
    assert lims_shape == {"reference", "display"}, lims_shape
    assert core_shape != lims_shape

    interop_source = inspect.getsource(
        __import__("app.national.api.routes.interop", fromlist=["x"])._patient_reference,
    )
    assert '"identifier"' in interop_source
    assert '"type"' not in interop_source
    print(f"\n[shapes] core={sorted(core_shape)} lims={sorted(lims_shape)} "
          f"interop={{reference, identifier, display}}")


def test_the_core_observation_duplicates_its_own_helper_rather_than_diverging():
    """Not a defect: the inline literal is shape-identical to _patient_ref."""
    import inspect

    from app.routes import ehr_fhir

    source = inspect.getsource(ehr_fhir._lab_result_to_observation)
    assert '"subject": {"reference": f"Patient/{order.patient_id}", "type": "Patient"}' in source
    helper = inspect.getsource(ehr_fhir._patient_ref)
    assert '"type": "Patient"' in helper and '"reference": f"Patient/{patient_id}"' in helper


# ── Phase 4: can any path publish a non-patient id as the patient? ──────────


def test_no_lab_fhir_path_publishes_an_order_or_specimen_id_as_the_patient(
    client, db, make_lab, make_lab_user,
):
    """The wrong-id class the ServiceRequest mapper was fixed for."""
    from app.lims.models import Order as LimsOrder
    from app.lims.models import Result as LimsResult
    from app.lims.models import Specimen
    from app.models.lab_order import LabOrder
    from app.models.lab_result import LabResult
    from app.models.patient import Patient

    lab = make_lab()
    user = make_lab_user(lab_id=lab.id, role="master_admin")
    # make the id spaces overlap-prone: several patients, then one order
    patients = []
    for n in range(3):
        p = Patient(lab_id=lab.id, full_name=f"P{n}", phone=f"0770000010{n}")
        db.add(p)
        patients.append(p)
    db.flush()
    order = LabOrder(lab_id=lab.id, patient_id=patients[0].id)
    db.add(order)
    db.flush()
    lims_order = LimsOrder(order_id=order.id, lab_id=lab.id, accession_number="ACC-ID-1")
    db.add(lims_order)
    specimen = Specimen(lab_id=lab.id, order_id=order.id, barcode="BC-ID-1", specimen_type="serum")
    db.add(specimen)
    core = LabResult(order_id=order.id, test_name="Glucose", value=5.4, token="IA063-T1")
    db.add(core)
    db.flush()
    lims_result = LimsResult(
        lab_id=lab.id, specimen_id=specimen.id, order_id=order.id,
        test_code="GLU", test_name="Glucose", value_numeric=5.4,
    )
    db.add(lims_result)
    db.flush()

    h = auth_headers(user_id=user.id, lab_id=lab.id, role="master_admin")
    forbidden = {
        f"Patient/{order.id}": "LabOrder.id",
        f"Patient/{lims_order.id}": "LimsOrder.id",
        f"Patient/{specimen.id}": "Specimen.id",
        f"Patient/{lims_result.id}": "LimsResult.id",
        f"Patient/{core.id}": "LabResult.id",
    }
    correct = f"Patient/{patients[0].id}"

    observed = {}
    for label, path in (
        ("core Observation", f"/fhir/Observation/{core.id}"),
        ("lims Observation", f"/lims/results/{lims_result.id}/fhir"),
        ("lims ServiceRequest", f"/lims/orders/{lims_order.id}/fhir"),
    ):
        response = client.get(path, headers=h)
        if response.status_code != 200:
            observed[label] = f"HTTP {response.status_code}"
            continue
        observed[label] = (response.json().get("subject") or {}).get("reference")
    print(f"\n[phase4] correct={correct!r}  observed={observed}")

    for label, reference in observed.items():
        if not isinstance(reference, str) or not reference.startswith("Patient/"):
            continue
        # a reference that resolves to a non-patient row is the defect class
        assert reference not in forbidden or reference == correct, (
            f"{label} published {reference} which is a {forbidden.get(reference)}"
        )


# ── Phase 5: the matrix ─────────────────────────────────────────────────────


def test_same_patient_two_orders_produce_two_subjects_both_naming_that_patient(
    client, db, make_lab, make_lab_user,
):
    from app.models.lab_order import LabOrder
    from app.models.lab_result import LabResult
    from app.models.patient import Patient

    lab = make_lab()
    user = make_lab_user(lab_id=lab.id, role="master_admin")
    patient = Patient(lab_id=lab.id, full_name="Repeat", phone="07700000200")
    db.add(patient)
    db.flush()
    refs = []
    for n in range(2):
        order = LabOrder(lab_id=lab.id, patient_id=patient.id)
        db.add(order)
        db.flush()
        result = LabResult(order_id=order.id, test_name="Glucose", value=5.0 + n, token=f"IA063-R{n}")
        db.add(result)
        db.flush()
        h = auth_headers(user_id=user.id, lab_id=lab.id, role="master_admin")
        response = client.get(f"/fhir/Observation/{result.id}", headers=h)
        assert response.status_code == 200, response.text
        refs.append(response.json()["subject"]["reference"])
    print(f"\n[same patient, two orders] {refs}")
    assert refs == [f"Patient/{patient.id}"] * 2


def test_different_tenant_cannot_read_either_store(client, db, make_lab, make_lab_user):
    from app.lims.models import Result as LimsResult
    from app.lims.models import Specimen
    from app.models.lab_order import LabOrder
    from app.models.lab_result import LabResult
    from app.models.patient import Patient

    built = []
    for tag in ("a", "b"):
        lab = make_lab()
        user = make_lab_user(lab_id=lab.id, role="master_admin")
        patient = Patient(lab_id=lab.id, full_name=f"T{tag}", phone=f"0770000030{tag=='b'}")
        db.add(patient)
        db.flush()
        order = LabOrder(lab_id=lab.id, patient_id=patient.id)
        db.add(order)
        db.flush()
        specimen = Specimen(lab_id=lab.id, order_id=order.id, barcode=f"BC-T{tag}", specimen_type="serum")
        db.add(specimen)
        core = LabResult(order_id=order.id, test_name="Glucose", value=5.4, token=f"IA063-T{tag}")
        db.add(core)
        db.flush()
        lims = LimsResult(
            lab_id=lab.id, specimen_id=specimen.id, order_id=order.id,
            test_code="GLU", test_name="Glucose", value_numeric=5.4,
        )
        db.add(lims)
        db.flush()
        built.append({
            "core": core, "lims": lims,
            "h": auth_headers(user_id=user.id, lab_id=lab.id, role="master_admin"),
        })

    a, b = built
    lims_cross = client.get(f"/lims/results/{a['lims'].id}/fhir", headers=b["h"])
    core_cross = client.get(f"/fhir/Observation/{a['core'].id}", headers=b["h"])
    print(f"\n[cross-tenant] lims={lims_cross.status_code} core={core_cross.status_code}")
    assert lims_cross.status_code == 404
    assert core_cross.status_code in (403, 404), core_cross.text


# ── Phase 6: are the published ids internal database ids? ───────────────────


def test_published_patient_ids_are_internal_database_ids(client, db, make_lab, make_lab_user):
    from app.models.lab_order import LabOrder
    from app.models.lab_result import LabResult
    from app.models.patient import Patient

    lab = make_lab()
    user = make_lab_user(lab_id=lab.id, role="master_admin")
    patient = Patient(lab_id=lab.id, full_name="Internal Id", phone="07700000400")
    db.add(patient)
    db.flush()
    order = LabOrder(lab_id=lab.id, patient_id=patient.id)
    db.add(order)
    db.flush()
    result = LabResult(order_id=order.id, test_name="Glucose", value=5.4, token="IA063-INT")
    db.add(result)
    db.flush()

    h = auth_headers(user_id=user.id, lab_id=lab.id, role="master_admin")
    body = client.get(f"/fhir/Observation/{result.id}", headers=h).json()

    assert body["subject"]["reference"] == f"Patient/{patient.id}"
    assert str(patient.id).isdigit(), "the published id is the integer primary key"
    # a stable public identifier exists on the model but is not what is published
    assert hasattr(patient, "health_id")
    print(f"\n[phase6] published Patient/{patient.id} is patients.id (integer PK); "
          f"patients.health_id exists but is not used in the reference")


# ── IA-064: the served HL7 converter ────────────────────────────────────────


def test_ia064_hl7_uses_the_inbound_identifier_as_the_fhir_patient_id(client, actor):
    response = client.post(
        "/fhir-interoperability/hl7/convert",
        json={"message": ORU.format(control="CTRL-1", pid3="MRN-FOREIGN-9001")},
        headers=actor,
    )
    if response.status_code in (401, 403):
        pytest.skip(f"converter requires an institutional permission this actor lacks: {response.status_code}")
    assert response.status_code == 200, response.text
    body = response.json()
    bundle = body["bundle"]

    subjects = {
        e["resource"]["resourceType"]: (e["resource"].get("subject") or {}).get("reference")
        for e in bundle["entry"]
    }
    print(f"\n[IA-064] simulationOnly={body.get('simulationOnly')} subjects={subjects}")

    # PID-3, an identifier minted by the sending facility, becomes the FHIR id
    assert subjects["Observation"] == "Patient/MRN-FOREIGN-9001"
    assert subjects["DiagnosticReport"] == "Patient/MRN-FOREIGN-9001"
    patient_entry = next(e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Patient")
    assert patient_entry["id"] == "MRN-FOREIGN-9001"


def test_ia064_the_synthetic_tag_is_on_the_bundle_only(client, actor):
    response = client.post(
        "/fhir-interoperability/hl7/convert",
        json={"message": ORU.format(control="CTRL-2", pid3="MRN-FOREIGN-9002")},
        headers=actor,
    )
    if response.status_code in (401, 403):
        pytest.skip("converter requires an institutional permission this actor lacks")
    bundle = response.json()["bundle"]

    assert bundle["meta"]["tag"][0]["code"] == "synthetic-only"
    unmarked = [
        e["resource"]["resourceType"] for e in bundle["entry"] if "meta" not in e["resource"]
    ]
    print(f"\n[IA-064] bundle tagged synthetic-only; resources WITHOUT meta: {unmarked}")
    assert unmarked, "every resource is now tagged -- this finding is stale"

    # the contrast: the unreachable module tags every resource individually
    import inspect

    from app.integration import fhir_r4_exchange

    source = inspect.getsource(fhir_r4_exchange.synthetic_bundle)
    assert source.count("_synthetic_meta()") >= 5


def test_ia064_a_message_with_no_patient_identifier_is_now_refused(client, actor):
    """This test used to assert the defect; it now asserts the repair.

    As originally written it recorded what the converter did:

        assert refs[0] == refs[1] == "Patient/synthetic-patient"

    — two distinct ORU^R01 messages, each with an empty PID-3, both produced
    `Patient/synthetic-patient`, so in any FHIR store that upserts by id the
    second overwrote or merged with the first. That is a result attributed to
    the wrong patient.

    IA-064 is FIXED: PID-3 is Required in an ORU^R01 under HL7 v2.5, and
    `parse_oru_r01` now refuses the message rather than guessing an identity,
    which the route maps to 422. The shape ratchets live in
    tests/verification/test_hl7_patient_identity.py.
    """
    statuses = []
    for n in (1, 2):
        response = client.post(
            "/fhir-interoperability/hl7/convert",
            json={"message": ORU.format(control=f"CTRL-NOPID-{n}", pid3="")},
            headers=actor,
        )
        if response.status_code in (401, 403):
            pytest.skip("converter requires an institutional permission this actor lacks")
        statuses.append(response.status_code)
        body = response.json()
        assert "bundle" not in body, (
            "a bundle was produced for an identifier-less message; before the "
            "fix this one carried Patient/synthetic-patient"
        )
        assert "PID-3" in str(body.get("detail", "")), body

    print(f"\n[IA-064 fixed] two distinct messages, no PID-3 -> {statuses}")
    assert statuses == [422, 422], statuses


def test_ia064_module_with_zero_importers_is_not_reachable():
    """Bounded: no importer and no route, which is not the same as proven dead."""
    import pathlib
    import re

    root = pathlib.Path(__file__).resolve().parents[2] / "app"
    hits = [
        p for p in root.rglob("*.py")
        if p.name != "fhir_r4_exchange.py"
        and re.search(r"fhir_r4_exchange", p.read_text(errors="replace"))
    ]
    assert hits == [], [str(h) for h in hits]
