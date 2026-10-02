"""Eleven FHIR mappers are unreachable, and the two that are reachable carried
a status table that could not be resolved.

IA-048 (P2 for the served half, latent for the rest) — DISCOVERED, REPRODUCED,
FIXED where served, VERIFIED. The unreachable mappers are recorded as latent
rather than fixed, and ratcheted so a future wiring cannot deliver the defect.

REACHABILITY, measured by sweeping every importer of app/national/fhir outside
that package, its own tests, and the re-export shim app/fhir/__init__.py:

    FHIRPatientMapper              integration/transformation/fhir_mapping.py
    FHIRProcedureMapper            routes/ehr_fhir.py          (served)
    FHIRObservationMapper          -- no caller
    FHIRDiagnosticReportMapper     -- no caller
    FHIRConditionMapper            -- no caller
    FHIREncounterMapper            -- no caller
    FHIRImmunizationMapper         -- no caller
    FHIRAllergyIntoleranceMapper   -- no caller
    FHIRCarePlanMapper             -- no caller
    FHIRMedicationRequestMapper    -- no caller
    FHIRMedicationStatementMapper  -- no caller
    FHIROrganizationMapper         -- no caller
    FHIRPractitionerMapper         -- no caller

THE LATENT TRAPS, in the unreachable eleven. These are NOT live defects and are
not counted as findings — nothing can reach them — but each would ship the
moment someone wires the mapper to a route:

    national/fhir/observation.py:14        "status": "final"
    national/fhir/diagnostic_report.py:14  "status": "final"
    national/fhir/diagnostic_report.py:38  "status": "final"
    national/fhir/condition.py:47          "verificationStatus" code "confirmed"
    national/fhir/condition.py:92          "clinicalStatus" code "active"

The Condition ones are the sharpest: a hardcoded `confirmed` verificationStatus
asserts a diagnosis has been established, and a hardcoded `active`
clinicalStatus asserts the patient has the condition now. This is the same class
IA-011 recorded ("the unreached one calls abnormal results normal") and the same
class IA-028 and IA-047 fixed on the served paths.

FIXED, because it is served: FHIRProcedureMapper._map_status, reached by
GET /ehr/fhir/Procedure/{id}. Two defects in one table:

  * `"discontinued": "discontinued"` — not a code in FHIR R4
    Procedure.status at all. The platform declares fhirVersion 4.0.1
    (app/contracts/fhir.py), whose value set is preparation | in-progress |
    not-done | on-hold | stopped | completed | entered-in-error | unknown. R4
    spells a halted procedure "stopped", so the resource went out carrying a
    code no consumer can resolve.
  * the fallback was `"completed"`, and `from_dict` additionally defaulted a
    missing status to `"completed"` before the mapper saw it. An unrecognised or
    absent status therefore published the procedure as performed and finished.

Scope stated honestly: the only served caller passes
`"completed" if record.is_final else "in-progress"`, so neither bad branch was
reachable through that route today. Both are corrected anyway — an invalid code
and a fail-unsafe default in a served mapper are a trap, and correcting a
mapping table cannot affect a caller that never hits it.
"""
from __future__ import annotations

import pathlib
import re

import pytest
from app.national.fhir.procedure import FHIRProcedureMapper

_BACKEND = pathlib.Path(__file__).resolve().parents[2]
_APP = _BACKEND / "app"
_NATIONAL_FHIR = _APP / "national" / "fhir"

# FHIR R4 Procedure.status — the complete value set.
_PROCEDURE_STATUSES = frozenset(
    {"preparation", "in-progress", "not-done", "on-hold", "stopped",
     "completed", "entered-in-error", "unknown"},
)

_MAPPERS_WITH_A_CALLER = {
    "FHIRPatientMapper",
    "FHIRProcedureMapper",
}

_MAPPERS_WITHOUT_A_CALLER = {
    "FHIRObservationMapper",
    "FHIRDiagnosticReportMapper",
    "FHIRConditionMapper",
    "FHIREncounterMapper",
    "FHIRImmunizationMapper",
    "FHIRAllergyIntoleranceMapper",
    "FHIRCarePlanMapper",
    "FHIRMedicationRequestMapper",
    "FHIRMedicationStatementMapper",
    "FHIROrganizationMapper",
    "FHIRPractitionerMapper",
}


def _callers_of(name: str) -> list[str]:
    """Modules outside the mapper package that name this mapper.

    Excludes the package's own files, its own tests, and app/fhir/__init__.py --
    a re-export shim that names every mapper and would otherwise make all
    thirteen look reachable.
    """
    hits = []
    for path in _APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(_BACKEND).as_posix()
        if (
            relative.startswith("app/national/fhir/")
            or "/tests/" in relative
            or relative == "app/fhir/__init__.py"
        ):
            continue
        if name in path.read_text(errors="replace"):
            hits.append(relative)
    return sorted(hits)


# ── reachability, ratcheted both ways ───────────────────────────────────────


@pytest.mark.parametrize("mapper", sorted(_MAPPERS_WITHOUT_A_CALLER))
def test_an_unreachable_mapper_stays_unreachable(mapper):
    """The ratchet. Wiring one of these to a route delivers a hardcoded clinical
    status with it -- a final observation, or a confirmed diagnosis -- so this
    test fails first and says to fix the status before wiring it up."""
    callers = _callers_of(mapper)
    assert callers == [], (
        f"{mapper} now has a caller ({callers}). Before this ships, check its "
        "hardcoded status: the mappers in app/national/fhir assert "
        '"final"/"confirmed"/"active" regardless of the record (IA-048).'
    )


@pytest.mark.parametrize("mapper", sorted(_MAPPERS_WITH_A_CALLER))
def test_a_reachable_mapper_is_still_reachable(mapper):
    """Positive control: the sweep must be able to see a caller at all. Without
    this, a broken sweep would report every mapper unreachable and the ratchet
    above would pass vacuously."""
    assert _callers_of(mapper) != []


def test_the_latent_hardcoded_statuses_are_where_this_finding_says_they_are():
    """Pins the trap list. If one of these is fixed the test fails, which is the
    cue to update the finding; if a new one appears, likewise."""
    expected = {
        ("observation.py", '"status": "final",'),
        ("diagnostic_report.py", '"status": "final",'),
    }
    found = set()
    for path in _NATIONAL_FHIR.glob("*.py"):
        for line in path.read_text().splitlines():
            if re.search(r'"status":\s*"(final|active|completed)"\s*[,}]', line):
                found.add((path.name, line.strip()))
    assert found == expected, (
        f"the latent hardcoded-status set changed: {found ^ expected}"
    )


def test_the_condition_mapper_still_hardcodes_what_this_finding_records():
    source = (_NATIONAL_FHIR / "condition.py").read_text()
    assert '"code": "confirmed"' in source, (
        "condition.py no longer hardcodes a confirmed verificationStatus -- "
        "update IA-048"
    )


# ── the served mapper, fixed ────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("internal", "expected"),
    [
        ("preparation", "preparation"),
        ("in_progress", "in-progress"),
        ("not_done", "not-done"),
        ("on_hold", "on-hold"),
        ("stopped", "stopped"),
        ("discontinued", "stopped"),
        ("completed", "completed"),
        ("entered_in_error", "entered-in-error"),
        ("unknown", "unknown"),
    ],
)
def test_the_procedure_status_mapping(internal, expected):
    assert FHIRProcedureMapper._map_status(internal) == expected


def test_every_mapped_procedure_status_is_a_real_r4_code():
    for internal in FHIRProcedureMapper._STATUS_MAP:
        assert FHIRProcedureMapper._map_status(internal) in _PROCEDURE_STATUSES


def test_discontinued_is_not_published_as_itself():
    """It is not a code in the R4 value set; R4 spells it "stopped"."""
    assert FHIRProcedureMapper._map_status("discontinued") == "stopped"
    assert "discontinued" not in _PROCEDURE_STATUSES


@pytest.mark.parametrize("unknown", [None, "", "   ", "some_future_state", "COMPLETEDish"])
def test_an_unrecognised_procedure_status_is_never_completed(unknown):
    """The fail-safe direction: claiming a procedure was performed is the one
    direction in which being wrong is unsafe."""
    assert FHIRProcedureMapper._map_status(unknown) == "unknown"
    assert FHIRProcedureMapper._map_status(unknown) != "completed"


def test_a_payload_with_no_status_is_not_published_as_performed():
    """`from_dict` used to default a missing status to "completed" before the
    mapper ever saw it, so correcting the mapper alone would not have been
    enough."""
    resource = FHIRProcedureMapper.from_dict({"id": "p1"}, patient_id="PAT1")
    assert resource["status"] == "unknown"


def test_the_mapping_is_case_and_separator_tolerant():
    assert FHIRProcedureMapper._map_status("IN-PROGRESS") == "in-progress"
    assert FHIRProcedureMapper._map_status("  Completed  ") == "completed"


def test_the_served_route_still_supplies_a_status_the_table_knows():
    """The only served caller, pinned: it passes "completed"/"in-progress", so
    the corrected fallback changes nothing for it. If that changes, the fallback
    becomes live and this test says to look."""
    import inspect

    from app.routes.ehr_fhir import fhir_read_procedure

    source = inspect.getsource(fhir_read_procedure)
    assert '"status": "completed" if record.is_final else "in-progress"' in source
    for value in ("completed", "in-progress"):
        assert FHIRProcedureMapper._map_status(value.replace("-", "_")) in _PROCEDURE_STATUSES


def test_the_procedure_resource_still_builds():
    """Positive control: a suite that only forbids things passes on an empty
    mapper."""
    resource = FHIRProcedureMapper.from_dict(
        {"id": "p9", "status": "completed", "code": "80146002", "display": "Appendectomy"},
        patient_id="PAT7",
        encounter_id="ENC3",
    )
    assert resource["resourceType"] == "Procedure"
    assert resource["status"] == "completed"
    assert resource["subject"]["reference"] == "Patient/PAT7"
    assert resource["encounter"]["reference"] == "Encounter/ENC3"
    assert resource["code"]["coding"][0]["code"] == "80146002"
