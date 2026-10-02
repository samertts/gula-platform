"""Three more paths published a clinical state the data did not support.

IA-047 (P1) — DISCOVERED, REPRODUCED, FIXED, VERIFIED.

IA-028 fixed `Observation.status` on `GET /ehr/fhir/Observation/{id}` and IA-036
fixed `ServiceRequest.status` in `app/lims`. Sweeping every hardcoded FHIR status
literal in the repository found the same defect class alive on three more served
paths, each reached by a different route:

1. `ehr_fhir.py` — the patient-everything bundle, Observation entries:

       "status": "final"

   Unconditional. Every lab result in the bundle was published as a final,
   verified observation, including results of orders still `pending` and orders
   that had been `cancelled`. This is IA-028 verbatim on the path IA-028 did not
   touch.

2. `ehr_fhir.py` — the same bundle, ServiceRequest entries:

       "status": order.status or "unknown"

   GULA's internal vocabulary emitted raw. `LabOrder.status` is one of
   {pending, completed, validated, cancelled} and FHIR R4 ServiceRequest.status
   is {draft, active, on-hold, revoked, completed, entered-in-error, unknown}:
   three of the four internal values are not codes in that value set at all.
   A withdrawn order went out as `"cancelled"`, which FHIR spells `"revoked"`.

3. `compliance.py` — `GET /compliance/fhir/service-request/{id}`:

       "status": "completed" if order.status == "completed" else "active"

   So a `validated` order and a `cancelled` order were both published as
   `"active"` — a withdrawn laboratory request asserted as in force and ready to
   be acted upon. IA-036's defect on a third path.

4. `compliance.py` — `GET /compliance/fhir/diagnostic-report/{id}`: a local map
   called a `completed` order's report `"final"`, while FHIR reserves "final"
   for a report "complete and verified by an authorized person" — in GULA the
   *validated* state. `validated` was not in the map at all and fell through to
   `"partial"`, understating a verified report.

   The suite had accepted this: `assert body["status"] in ("final",
   "registered", "cancelled", "partial")`. A membership test that wide is why the
   route could call an unverified report final for as long as it did. That
   assertion now pins the exact value for the exact state.

FIX: `service_request_status()` and `diagnostic_report_status()` join
`observation_status()` in app/fhir/terminology.py, so one module owns the
LabOrder → FHIR status mapping and all four call sites use it. The mappings carry
the same fail-safe direction already reviewed for Observation: an unrecognised
state never resolves to a code that invites action — ServiceRequest falls back to
FHIR's own "unknown", never "active", and DiagnosticReport to "partial", which
claims less than the data supports rather than more.

VERIFIED NEGATIVES in the same sweep, recorded rather than counted as fixes:

  * `_immunization_to_fhir`: `rec.status or "completed"`. `ImmunizationRecord
    .status` is `Column(String(50), nullable=False, default="completed")`, so
    the fallback is unreachable through the ORM and no row can be published as
    an administered vaccine on the strength of a missing status.
  * the bundle's Condition entries: `cond.clinical_status or "active"`.
    `ConditionRecord.clinical_status` is `nullable=False, default="active"`, so
    the fallback is likewise unreachable.

Both are pinned below: the fallbacks are harmless only because the columns are
non-nullable, and a migration that relaxed either one would make them live.
"""
from __future__ import annotations

import pathlib
import re

import pytest
from app.ehr.models.clinical_summary import ConditionRecord
from app.ehr.models.immunization import ImmunizationRecord
from app.fhir.terminology import (
    diagnostic_report_status,
    observation_status,
    service_request_status,
)

_BACKEND = pathlib.Path(__file__).resolve().parents[2]
_EHR_FHIR = _BACKEND / "app" / "routes" / "ehr_fhir.py"
_COMPLIANCE = _BACKEND / "app" / "routes" / "compliance.py"

# FHIR R4 required bindings, complete value sets.
_SERVICE_REQUEST_STATUSES = frozenset(
    {"draft", "active", "on-hold", "revoked", "completed", "entered-in-error", "unknown"},
)
_DIAGNOSTIC_REPORT_STATUSES = frozenset(
    {"registered", "partial", "preliminary", "final", "amended", "corrected",
     "appended", "cancelled", "entered-in-error", "unknown"},
)
_OBSERVATION_STATUSES = frozenset(
    {"registered", "preliminary", "final", "amended", "corrected", "cancelled",
     "entered-in-error", "unknown"},
)

# app/domain/order_state.py — the complete LabOrder vocabulary.
_ORDER_STATES = ("pending", "completed", "validated", "cancelled")


# ── the source vocabulary is covered, and lands inside the value sets ───────


@pytest.mark.parametrize("state", _ORDER_STATES)
def test_every_order_state_maps_into_every_value_set(state):
    assert service_request_status(state) in _SERVICE_REQUEST_STATUSES
    assert diagnostic_report_status(state) in _DIAGNOSTIC_REPORT_STATUSES
    assert observation_status(state) in _OBSERVATION_STATUSES


@pytest.mark.parametrize(
    ("state", "service_request", "report", "observation"),
    [
        ("pending", "active", "registered", "preliminary"),
        ("completed", "completed", "preliminary", "preliminary"),
        ("validated", "completed", "final", "final"),
        ("cancelled", "revoked", "cancelled", "cancelled"),
    ],
)
def test_the_three_mappings(state, service_request, report, observation):
    assert service_request_status(state) == service_request
    assert diagnostic_report_status(state) == report
    assert observation_status(state) == observation


def test_a_withdrawn_order_is_never_published_as_in_force():
    """The clinical point of the whole finding."""
    assert service_request_status("cancelled") == "revoked"
    assert service_request_status("cancelled") != "active"
    assert diagnostic_report_status("cancelled") == "cancelled"
    assert observation_status("cancelled") == "cancelled"


def test_an_unvalidated_result_is_never_published_as_verified():
    assert observation_status("completed") == "preliminary"
    assert diagnostic_report_status("completed") == "preliminary"
    assert diagnostic_report_status("completed") != "final"


@pytest.mark.parametrize("unknown", [None, "", "   ", "some_future_state", "ACTIVE_ish"])
def test_an_unrecognised_state_never_invites_action(unknown):
    assert service_request_status(unknown) == "unknown"
    assert service_request_status(unknown) != "active"
    assert diagnostic_report_status(unknown) != "final"


def test_an_absent_status_is_registered_not_partial():
    """LabOrder.status is Column(String(20), default="pending") -- nullable, so
    an absent status is reachable. The call site this replaced read
    `order.status or "pending"`, mapping None to "registered"; that behaviour is
    preserved rather than quietly reclassified as "partial"."""
    assert diagnostic_report_status(None) == "registered"
    assert diagnostic_report_status("") == "registered"
    assert diagnostic_report_status("   ") == "registered"
    assert diagnostic_report_status("nonsense") == "partial"


def test_the_mappings_are_case_and_space_tolerant():
    assert service_request_status("  CANCELLED  ") == "revoked"
    assert diagnostic_report_status("Validated") == "final"


# ── the call sites, so none can drift back ──────────────────────────────────


def test_the_bundle_no_longer_hardcodes_a_final_observation():
    source = _EHR_FHIR.read_text()
    assert '"status": "final",' not in source, (
        "an unconditional final Observation status is back in ehr_fhir"
    )
    assert source.count("observation_status(order.status)") == 2, (
        "both the single-resource route and the bundle must map the order state"
    )


def test_the_bundle_no_longer_emits_the_internal_order_vocabulary():
    source = _EHR_FHIR.read_text()
    assert '"status": order.status or "unknown"' not in source
    assert "service_request_status(order.status)" in source


def test_the_compliance_routes_use_the_canonical_mappers():
    source = _COMPLIANCE.read_text()
    assert '"completed" if order.status == "completed" else "active"' not in source
    assert "service_request_status(order.status)" in source
    assert "diagnostic_report_status(order.status)" in source
    assert 'status_map = {' not in source, "the local report map is back"


def test_no_route_module_hardcodes_a_verified_clinical_status():
    """A sweep rather than a spot check: no FHIR status literal in these two
    modules may assert a verified or in-force state unconditionally."""
    # The literal must be the whole value: a ternary such as
    # `"status": "final" if note.is_final else "preliminary"` reads a real field
    # and is not an unconditional assertion, so the trailing [,}] excludes it.
    # Matching those too is how the first draft of this guard reported four
    # false positives, two of which are the verified negatives pinned below.
    forbidden = re.compile(r'"status":\s*"(final|active|completed|current)"\s*[,}]')
    # One justified exemption, and the justification is asserted separately by
    # test_the_document_reference_status_is_truthful_because_of_the_read_filter:
    # DocumentReference.status is hardcoded "current", and that is true because
    # get_clinical_attachment filters is_deleted == False, so a withdrawn
    # document can never reach the builder. The exemption is by exact text, not
    # by loosening the pattern.
    exempt = {'"status": "current",'}

    offenders = []
    for path in (_EHR_FHIR, _COMPLIANCE):
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            if forbidden.search(line) and line.strip() not in exempt:
                offenders.append(f"{path.name}:{lineno}: {line.strip()}")
    assert offenders == [], offenders


# ── the two verified negatives, pinned to the reason they are harmless ──────


def test_the_immunization_status_fallback_is_unreachable():
    """`rec.status or "completed"` would assert an administered vaccine on the
    strength of a missing status, which could lead a clinician to skip a needed
    dose. It is unreachable only because the column cannot be null -- so this
    pins the column, not the fallback."""
    column = ImmunizationRecord.__table__.columns["status"]
    assert column.nullable is False
    assert column.default is not None and column.default.arg == "completed"


def test_the_condition_clinical_status_fallback_is_unreachable():
    """Same shape: `cond.clinical_status or "active"` in the bundle would assert
    a currently-active condition from a missing status."""
    column = ConditionRecord.__table__.columns["clinical_status"]
    assert column.nullable is False
    assert column.default is not None and column.default.arg == "active"


def test_the_document_reference_status_is_truthful_because_of_the_read_filter():
    """The justification for the one exemption above, asserted rather than
    trusted. `_attachment_to_document_reference` hardcodes `"status": "current"`,
    and DocumentReference.status is {current, superseded, entered-in-error}. That
    is honest only because `get_clinical_attachment` filters
    `is_deleted == False`, so a withdrawn attachment never reaches the builder.
    Remove that filter and the hardcode starts publishing deleted documents as
    current."""
    import inspect

    from app.services.ehr_service import get_clinical_attachment

    source = inspect.getsource(get_clinical_attachment)
    assert "ClinicalAttachment.is_deleted.is_(False)" in source, (
        "the attachment read is no longer filtered on is_deleted, so the "
        "hardcoded DocumentReference status \"current\" is now a false claim"
    )


def test_the_composition_status_reads_the_only_field_that_exists():
    """A verified negative, pinned. The Composition entries map
    `is_final -> final/preliminary`, and ClinicalNote has no status column at
    all -- `is_final` is the only field there is, so this is a faithful read and
    not a hardcoded assertion."""
    from app.ehr.models.clinical_note import ClinicalNote

    columns = set(ClinicalNote.__table__.columns.keys())
    assert "is_final" in columns
    assert "status" not in columns, (
        "ClinicalNote now has a status column; the is_final mapping in the "
        "bundle and in the Procedure route may now be ignoring it"
    )


def test_the_procedure_resource_is_built_from_a_clinical_note():
    """Recorded so the `is_final -> completed/in-progress` mapping is not
    mistaken for a status-ignoring defect: GET /ehr/fhir/Procedure/{id} reads a
    ClinicalNote, which has no status of its own. Both values are real
    Procedure.status codes. That a Procedure is synthesised from a note at all
    is a modelling question, not this finding."""
    import inspect

    from app.routes.ehr_fhir import fhir_read_procedure

    source = inspect.getsource(fhir_read_procedure)
    assert "ehr_service.get_clinical_note(" in source
