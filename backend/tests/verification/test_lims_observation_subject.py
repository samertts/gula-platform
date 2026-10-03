"""The LIMS Observation names no patient, and the fix that assumed it did.

IA-061. ``app/lims/fhir_mappers.py:108`` builds the subject of every LIMS
Observation as::

    "subject": _fhir_reference(
        f"Patient/{result.specimen.order.patient_id}"
        if hasattr(result, "specimen") and hasattr(result.specimen, "order")
        else "unknown"
    )

``Specimen`` has ``order_id`` (a foreign key to ``lab_orders.id``) but **no
``order`` relationship**. Measured: ``hasattr(Specimen, "order")`` is False.
The only ``order``-named relationship in app/lims/models.py is
``Order.original_order`` at line 993. So the guard never passes and the
subject is always the literal string ``"unknown"`` -- a reference to a
resource that does not exist, on a clinical result.

WHAT MAKES THIS MORE THAN A COSMETIC BUG.

The docstring of ``order_to_fhir_service_request`` -- the fix that corrected
the ServiceRequest subject after it was found publishing ``Patient/{order_id}``
-- justifies itself in part by asserting:

    ``result_to_fhir`` in this same module already reaches the patient
    correctly through ``specimen.order.patient_id``

That assertion is false, and this test is what makes it checkable. The
ServiceRequest path was repaired properly; the Observation path beside it was
assumed correct and never measured.

REACHABILITY, measured rather than assumed.

Two call sites return ``result_to_fhir``:

  app/lims/routes.py:1021  GET /lims/orders/{id}/fhir-bundle
      pops "subject" from every Observation on purpose (the endpoint
      deliberately does not expand patient identity), so the bad reference
      is never published there.
  app/lims/routes.py:1465  GET /lims/results/{result_id}/fhir
      returns the mapper's output unchanged -- this is the served path that
      publishes subject: {"reference": "unknown"}.

That route is authenticated (``Depends(get_current_user)``) and tenant-scoped
(``Result.lab_id == _lab_id(current_user)``), so this is a FHIR correctness
and clinical-linkage defect, not a leak: no other tenant's data is exposed and
no wrong patient is named. An Observation with no identifiable subject is
still an Observation a consumer cannot safely file.

NOT FIXED HERE. The honest repair is a decision, not an edit: either add a
``Specimen.order`` relationship (an ORM change to a model the module docstring
calls a bounded context over untouched foundation models), or resolve the
patient through ``Specimen.order_id`` -> ``lab_orders.patient_id`` in the
route and pass it in keyword-only, the way
``order_to_fhir_service_request`` already requires. The second mirrors the
existing precedent, but choosing it changes a served FHIR response shape,
which CLAUDE.md puts behind human approval.
"""
from __future__ import annotations

import pytest


def test_specimen_has_no_order_relationship():
    """The premise. If this ever becomes True, re-measure everything below."""
    from app.lims.models import Result, Specimen

    assert hasattr(Specimen, "order_id"), "the foreign key itself should exist"
    assert not hasattr(Specimen, "order"), (
        "Specimen.order now exists -- the mapper's guard may pass and this "
        "finding must be re-measured"
    )
    assert hasattr(Result, "specimen")


def test_the_observation_subject_is_the_literal_string_unknown(db, make_lab, make_lab_user):
    """Runtime proof through the real mapper on a real persisted row."""
    from app.lims.fhir_mappers import result_to_fhir
    from app.lims.models import Result, Specimen
    from app.models.lab_order import LabOrder
    from app.models.patient import Patient

    lab = make_lab()
    user = make_lab_user(lab_id=lab.id, role="admin")
    patient = Patient(lab_id=lab.id, full_name="Subject Probe", phone="07700000001")
    db.add(patient)
    db.flush()
    order = LabOrder(lab_id=lab.id, patient_id=patient.id, doctor_user_id=user.id)
    db.add(order)
    db.flush()
    specimen = Specimen(
        lab_id=lab.id,
        order_id=order.id,
        barcode="IA061-PROBE-0001",
        specimen_type="serum",
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

    observation = result_to_fhir(result)

    assert observation["resourceType"] == "Observation"
    # measured exactly: the helper adds an empty display alongside the reference
    assert observation["subject"]["reference"] == "unknown", observation["subject"]
    assert observation["subject"] == {"reference": "unknown", "display": ""}
    # the patient exists and is reachable from the row -- the mapper just never looks
    assert (
        db.query(LabOrder.patient_id).filter(LabOrder.id == specimen.order_id).scalar()
        == patient.id
    )


def test_the_bundle_path_drops_the_subject_so_it_is_not_published_there():
    """Pins why only one of the two call sites is affected."""
    import inspect

    from app.lims import routes

    source = inspect.getsource(routes.order_fhir_bundle)
    assert 'observation.pop("subject", None)' in source
    assert 'service_request.pop("subject", None)' in source


def test_the_serving_route_returns_the_mapper_output_unchanged():
    import inspect

    from app.lims import routes

    source = inspect.getsource(routes.result_fhir)
    assert "return result_to_fhir(result)" in source
    assert "pop(" not in source, "the route now post-processes; re-measure"
    # authenticated and tenant-scoped, which is why this is not a leak
    assert "get_current_user" in source
    assert "_lab_id(current_user)" in source


def test_the_servicerequest_fix_asserts_something_untrue_about_this_mapper():
    """The contradiction, pinned as text so it cannot be quietly dropped."""
    import inspect

    from app.lims import fhir_mappers

    doc = inspect.getdoc(fhir_mappers.order_to_fhir_service_request) or ""
    claims_correct = "already" in doc and "specimen.order.patient_id" in doc
    assert claims_correct, (
        "the docstring no longer makes the claim this finding contradicts -- "
        "if it was corrected, drop this test"
    )

    from app.lims.models import Specimen

    assert not hasattr(Specimen, "order"), (
        "the claim is still made and is still false only while Specimen.order "
        "does not exist"
    )
