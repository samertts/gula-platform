"""The LIMS Observation names its patient, and cannot silently stop.

IA-061 / NR-218, REPAIRED. This file asserted the defect until the repair
landed; it now pins the fix and both halves of the regression.

THE DEFECT, for the record. ``app/lims/fhir_mappers.py`` built the subject as::

    f"Patient/{result.specimen.order.patient_id}"
        if hasattr(result, "specimen") and hasattr(result.specimen, "order")
        else "unknown"

``Specimen`` carries ``order_id`` -- a foreign key to ``lab_orders.id`` -- but
has no ``order`` relationship; the only ``order``-named relationship in
app/lims/models.py is ``Order.original_order``. The guard therefore never
passed, and every Observation published ``subject: {"reference": "unknown"}``
on the served route, while ``GET /fhir/Observation/{id}`` published
``Patient/1`` correctly from the same rows.

THE REPAIR mirrors ``order_to_fhir_service_request``, which had already been
fixed for the neighbouring wrong-patient defect: ``patient_id`` is keyword-only
with no default, a missing value raises rather than falling back, and the
caller resolves it from ``lims_results.order_id -> lab_orders.patient_id``.
No ``Specimen.order`` relationship was added -- that would have made the old
guard pass and quietly turned a false docstring claim true.

RATCHET BOTH WAYS. Asserting only that a patient reference is present would be
satisfied by any constant, which is how the original defect would return in a
new costume. So these tests assert that the subject names the *right* patient,
that the mapper refuses to build without one, and that no silent fallback
remains in the source.
"""
from __future__ import annotations

import inspect

import pytest


def _chain(db, make_lab, make_lab_user, *, barcode: str, token_suffix: str):
    """A persisted Lab -> Patient -> LabOrder -> Specimen -> Result."""
    from app.lims.models import Result, Specimen
    from app.models.lab_order import LabOrder
    from app.models.patient import Patient

    lab = make_lab()
    user = make_lab_user(lab_id=lab.id, role="admin")
    patient = Patient(lab_id=lab.id, full_name="Subject Probe", phone=f"0770000{token_suffix}")
    db.add(patient)
    db.flush()
    order = LabOrder(lab_id=lab.id, patient_id=patient.id, doctor_user_id=user.id)
    db.add(order)
    db.flush()
    specimen = Specimen(
        lab_id=lab.id, order_id=order.id, barcode=barcode, specimen_type="serum",
    )
    db.add(specimen)
    db.flush()
    result = Result(
        lab_id=lab.id,
        specimen_id=specimen.id,
        order_id=order.id,
        test_code="GLU",
        test_name="Glucose",
        value_numeric=5.4,
        unit="mmol/L",
    )
    db.add(result)
    db.flush()
    return {"lab": lab, "patient": patient, "order": order, "specimen": specimen, "result": result}


def test_the_mapper_now_names_the_patient(db, make_lab, make_lab_user):
    from app.lims.fhir_mappers import result_to_fhir

    built = _chain(db, make_lab, make_lab_user, barcode="IA061-FIX-0001", token_suffix="1001")
    observation = result_to_fhir(built["result"], patient_id=built["patient"].id)

    assert observation["resourceType"] == "Observation"
    assert observation["subject"]["reference"] == f"Patient/{built['patient'].id}"
    # the id the defect used to publish instead
    assert observation["subject"]["reference"] != "unknown"


def test_the_mapper_publishes_the_argument_and_not_some_row_id(db, make_lab, make_lab_user):
    """The assertion above cannot distinguish the argument from a row id.

    SQLite hands the chain ``patient.id == order.id == specimen.id ==
    result.id == 1``, so ``Patient/{patient.id}`` would also be produced by a
    mapper that published the specimen or result id. A sentinel no row can hold
    makes the assertion discriminate: whatever comes out must be the value that
    went in.
    """
    from app.lims.fhir_mappers import result_to_fhir

    built = _chain(db, make_lab, make_lab_user, barcode="IA061-FIX-0003", token_suffix="1003")
    sentinel = 987_654
    assert sentinel not in {
        built["patient"].id, built["order"].id,
        built["specimen"].id, built["result"].id,
    }

    observation = result_to_fhir(built["result"], patient_id=sentinel)
    assert observation["subject"]["reference"] == f"Patient/{sentinel}"
    # and the real row ids are nowhere in the subject
    assert observation["specimen"]["reference"] == f"Specimen/lims-spec-{built['specimen'].id}"


def test_the_mapper_refuses_to_build_without_a_patient(db, make_lab, make_lab_user):
    """The control. Any default or fallback would restore the defect."""
    from app.lims.fhir_mappers import result_to_fhir

    built = _chain(db, make_lab, make_lab_user, barcode="IA061-FIX-0002", token_suffix="1002")

    with pytest.raises(ValueError, match="must not be guessed"):
        result_to_fhir(built["result"], patient_id=None)


def test_patient_id_is_keyword_only_with_no_default():
    """A positional or defaulted parameter is how this regresses quietly."""
    from app.lims.fhir_mappers import result_to_fhir

    parameter = inspect.signature(result_to_fhir).parameters["patient_id"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY, parameter.kind
    assert parameter.default is inspect.Parameter.empty, parameter.default

    with pytest.raises(TypeError):
        result_to_fhir(object())  # no patient_id at all


def test_no_silent_fallback_remains_in_the_mapper_body():
    """Ratchet the other way: a reference must not be synthesised from nothing.

    Checked against the function body only -- the module docstring and this
    finding's own prose quote the old expression on purpose, and a substring
    ratchet over the whole file would pass on that quotation.
    """
    from app.lims import fhir_mappers

    body = inspect.getsource(fhir_mappers.result_to_fhir)
    _, _, after_docstring = body.partition('"""')
    _, _, code = after_docstring.partition('"""')

    assert "hasattr" not in code, code
    assert '"unknown"' not in code, code
    assert "patient_id" in code


def test_the_specimen_order_relationship_was_not_added():
    """The repair deliberately did not take the shortcut."""
    from app.lims.models import Result, Specimen

    assert hasattr(Specimen, "order_id")
    assert not hasattr(Specimen, "order"), (
        "Specimen.order now exists; the repair was supposed to resolve the "
        "patient in the caller instead -- re-read IA-061 before accepting this"
    )
    assert hasattr(Result, "specimen")


def test_the_servicerequest_docstring_no_longer_asserts_the_false_claim():
    """The contradiction this finding exposed is corrected, not left behind."""
    from app.lims import fhir_mappers

    doc = inspect.getdoc(fhir_mappers.order_to_fhir_service_request) or ""
    assert "already\n    reaches the patient correctly" not in doc
    assert "That was false" in doc, (
        "the correction was removed; the docstring must not re-assert that "
        "result_to_fhir reaches the patient through specimen.order.patient_id"
    )


def test_both_call_sites_pass_a_resolved_patient(db, make_lab, make_lab_user):
    """Neither served path may satisfy the argument with a placeholder."""
    from app.lims import routes

    single = inspect.getsource(routes.result_fhir)
    assert "LabOrder.patient_id" in single
    assert "patient_id=patient_id" in single
    assert "LabOrder.lab_id == lab_id" in single, "the resolution must stay tenant-scoped"

    bundle = inspect.getsource(routes.order_fhir_bundle)
    assert "patient_id=bundle_patient_id" in bundle
    assert 'observation.pop("subject", None)' in bundle, (
        "the bundle still deliberately omits patient identity"
    )
