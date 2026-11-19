"""The LIMS ServiceRequest named the wrong patient and ignored the order's state.

Second-order sweep after IA-028 (Observation.status hardcoded "final"). The same
defect class was looked for in the two sibling resources, and the answer differed:

DiagnosticReport — VERIFIED NEGATIVE, recorded rather than "fixed".
    `report_to_fhir_diagnostic` already calls `_map_report_status(report.status)`,
    which maps LabReport.status onto real FHIR codes (draft -> preliminary,
    final -> final, amended/corrected -> amended, cancelled -> cancelled) with a
    fail-safe "preliminary" default. That is the correct pattern. No change made.

IA-036 (P1) — ServiceRequest.status was the literal "active".
    `Order.order_status` exists and has a twelve-state machine, and the mapper
    read `order.priority`, `order.ordered_at`, `order.ordered_by` and
    `order.accession_number` from the same object while ignoring its state.
    Measured on PostgreSQL: pending, in_progress, completed, validated, released
    and cancelled all published `status: "active"` — so a withdrawn request was
    published as in force and ready to be acted upon.

IA-037 (P1) — ServiceRequest.subject named a Patient by an *order* id.
    `lims_orders.order_id` is a foreign key to `lab_orders.id`, not a patient.
    The mapper built `Patient/{order.order_id}`, so six requests belonging to
    patient 22 published `subject: Patient/36` .. `Patient/41`. Where the two id
    ranges overlap that resolves to a different real person, which attributes a
    laboratory request to the wrong patient.

    This was a singleton, not a class: `result_to_fhir` in the same module
    already reaches the patient correctly through `specimen.order.patient_id`,
    and a sweep of all 19 `Patient/{...}` references in backend/app found 18
    using a patient id and this one outlier.

    Published only by `GET /lims/orders/{order_id}/fhir`. The sibling
    `/fhir-bundle` endpoint pops `subject` deliberately — it does not expand
    patient identity — so the wrong reference never reached that response, and
    the finding is recorded against one route rather than two.
"""
from __future__ import annotations

import ast
import pathlib

import pytest
from app.lims.fhir_mappers import (
    _map_order_status,
    _map_report_status,
    order_to_fhir_service_request,
)
from app.lims.state_machine import _ORDER_TRANSITIONS

_BACKEND = pathlib.Path(__file__).resolve().parents[2]
_MAPPERS = _BACKEND / "app" / "lims" / "fhir_mappers.py"
_LIMS_ROUTES = _BACKEND / "app" / "lims" / "routes.py"

# FHIR R4 ServiceRequest.status — the complete value set.
_SERVICE_REQUEST_STATUSES = frozenset(
    {"draft", "active", "on-hold", "revoked", "completed", "entered-in-error", "unknown"},
)
# FHIR R4 DiagnosticReport.status — the subset this platform can produce.
_DIAGNOSTIC_REPORT_STATUSES = frozenset(
    {"registered", "partial", "preliminary", "final", "amended", "corrected",
     "appended", "cancelled", "entered-in-error", "unknown"},
)


class _Order:
    """Minimal stand-in; the mapper only reads attributes."""

    def __init__(self, order_status="pending", **kw):
        self.id = kw.get("id", 1)
        self.fhir_id = kw.get("fhir_id")
        self.order_status = order_status
        self.accession_number = kw.get("accession_number", "ACC1")
        self.priority = kw.get("priority", "routine")
        self.ordered_at = kw.get("ordered_at")
        self.ordered_by = kw.get("ordered_by")
        self.order_id = kw.get("order_id", 999)  # the FK to lab_orders.id


# ── IA-036 status ────────────────────────────────────────────────────────────


def test_every_state_in_the_machine_maps_to_a_real_fhir_code():
    """The source vocabulary is the state machine, so cover all of it."""
    assert len(_ORDER_TRANSITIONS) == 12, "the state machine changed; re-check this mapping"
    for state in _ORDER_TRANSITIONS:
        assert _map_order_status(state) in _SERVICE_REQUEST_STATUSES, (
            f"state {state!r} maps outside the ServiceRequest value set"
        )


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("pending", "active"),
        ("accessioned", "active"),
        ("collecting", "active"),
        ("collected", "active"),
        ("in_transport", "active"),
        ("received", "active"),
        ("in_progress", "active"),
        ("completed", "completed"),
        ("validated", "completed"),
        ("released", "completed"),
        ("corrected", "completed"),
        ("cancelled", "revoked"),
    ],
)
def test_the_status_mapping(state, expected):
    assert _map_order_status(state) == expected


def test_a_withdrawn_order_is_not_published_as_active():
    """The clinical point. "active" invites a consumer to act on the request."""
    assert _map_order_status("cancelled") == "revoked"
    assert _map_order_status("cancelled") != "active"


@pytest.mark.parametrize("unknown", [None, "", "   ", "some_future_state", "ACTIVE_ish"])
def test_an_unrecognised_state_is_never_active(unknown):
    """Fail safe: defaulting to "active" would invite action on a withdrawn
    request, so an unmapped state resolves to FHIR's own "unknown"."""
    assert _map_order_status(unknown) == "unknown"


def test_the_status_mapping_is_case_and_space_tolerant():
    assert _map_order_status("CANCELLED") == "revoked"
    assert _map_order_status("  cancelled  ") == "revoked"


# ── IA-037 subject ───────────────────────────────────────────────────────────


def test_the_subject_is_the_patient_and_not_the_order():
    order = _Order(order_id=36)  # the FK to lab_orders.id
    resource = order_to_fhir_service_request(order, patient_id=22)
    assert resource["subject"]["reference"] == "Patient/22"
    assert resource["subject"]["reference"] != "Patient/36", (
        "the subject is being built from the order id again"
    )


def test_a_missing_patient_id_cannot_be_omitted_by_a_caller():
    """The control. A default would let a call site silently regress."""
    with pytest.raises(TypeError):
        order_to_fhir_service_request(_Order())  # type: ignore[call-arg]


def test_an_unresolved_patient_raises_rather_than_guessing():
    """ServiceRequest.subject is 1..1. There is no honest resource without it,
    and an order-derived reference is the defect, so this refuses to build one."""
    with pytest.raises(ValueError, match="must not be guessed"):
        order_to_fhir_service_request(_Order(), patient_id=None)


def test_the_rest_of_the_resource_still_builds():
    """Positive control: a suite that only forbids things passes on an empty
    mapper."""
    order = _Order(order_status="cancelled", accession_number="ACC-7", priority="stat")
    resource = order_to_fhir_service_request(order, patient_id=5)
    assert resource["resourceType"] == "ServiceRequest"
    assert resource["intent"] == "order"
    assert resource["priority"] == "stat"
    assert resource["code"]["coding"][0]["code"] == "ACC-7"
    assert resource["status"] == "revoked"
    assert resource["subject"]["reference"] == "Patient/5"


# ── DiagnosticReport: the verified negative, pinned so it stays correct ──────


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("draft", "preliminary"),
        ("final", "final"),
        ("amended", "amended"),
        ("corrected", "amended"),
        ("cancelled", "cancelled"),
    ],
)
def test_the_report_status_mapping_was_already_correct(state, expected):
    """Recorded as a verified negative, not a fix. Pinned so a later change
    cannot quietly reintroduce the IA-028 class here."""
    assert _map_report_status(state) == expected


def test_an_unrecognised_report_state_is_never_final():
    for unknown in ("", "nonsense", "FINAL_ish"):
        assert _map_report_status(unknown) == "preliminary"


def test_every_report_status_is_a_real_fhir_code():
    for state in ("draft", "final", "amended", "corrected", "cancelled", "nonsense"):
        assert _map_report_status(state) in _DIAGNOSTIC_REPORT_STATUSES


# ── the call sites, so neither can drift back ────────────────────────────────


def _function_source(path: pathlib.Path, name: str) -> str:
    """The function's *code*, with its docstring removed.

    ast.unparse includes the docstring, and these docstrings quote the defect
    they describe — `Patient/{order.order_id}` appears in the prose explaining
    why it is wrong. A guard that matched that would fail on its own
    documentation, which is the mirror of a ratchet passing on a commented-out
    line. Only executable code is inspected here.
    """
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == name:
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                body = body[1:]
            return "\n".join(ast.unparse(stmt) for stmt in body)
    raise AssertionError(f"{name} not found in {path.name}")


def test_the_mapper_no_longer_derives_the_subject_from_the_order():
    source = _function_source(_MAPPERS, "order_to_fhir_service_request")
    assert "Patient/{order.order_id}" not in source
    assert "f'Patient/{patient_id}'" in source or 'f"Patient/{patient_id}"' in source


def test_the_mapper_no_longer_hardcodes_the_status():
    source = _function_source(_MAPPERS, "order_to_fhir_service_request")
    assert "_map_order_status(order.order_status)" in source
    assert "'status': 'active'" not in source


@pytest.mark.parametrize("route", ["order_fhir", "order_fhir_bundle"])
def test_every_route_resolves_the_patient_through_the_parent_order(route):
    """Both call sites must reach lab_orders for the patient, under the tenant
    predicate — resolving it unscoped would be a cross-tenant read."""
    source = _function_source(_LIMS_ROUTES, route)
    assert "LabOrder.patient_id" in source, f"{route} does not resolve the patient"
    assert "LabOrder.id == lims_order.order_id" in source
    assert "LabOrder.lab_id" in source, f"{route} resolves the patient unscoped"


def test_both_routes_remain_tenant_scoped_on_the_lims_order():
    """Positive control: the fix must not have widened the tenant boundary.

    The predicate is matched as `lims_models.Order.lab_id`, not `Order.lab_id`.
    The shorter form is a *substring* of `LabOrder.lab_id`, which the patient
    resolution this fix added also contains — so the loose assertion passed even
    with the LIMS order's own tenant predicate deleted. Removing it must fail
    here, and a negative proof confirmed that it now does.
    """
    for route in ("order_fhir", "order_fhir_bundle"):
        source = _function_source(_LIMS_ROUTES, route)
        assert "lims_models.Order.lab_id ==" in source, (
            f"{route} lost the tenant predicate on the LIMS order itself"
        )


def test_the_bundle_still_withholds_patient_identity():
    """That endpoint deliberately does not expand patient identity, which is why
    the wrong reference never reached its response. Keep it that way."""
    source = _function_source(_LIMS_ROUTES, "order_fhir_bundle")
    assert 'pop("subject", None)' in source or "pop('subject', None)" in source
