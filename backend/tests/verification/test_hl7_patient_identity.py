"""Two patients' lab results collapsed onto one FHIR identity.

IA-064. ``app/capabilities/fhir_interoperability/hl7.py::to_fhir_bundle``
derived every id in the bundle from two HL7 fields, and substituted a literal
whenever either was absent:

    patient_id     = message.patient_identifier or "synthetic-patient"
    report_id      = f"report-{message.control_id or 'synthetic'}"
    observation_id = f"obs-{message.control_id or 'synthetic'}-{index}"

So two ORU^R01 messages that both lacked PID-3 and MSH-10 produced **the same
Patient id, the same DiagnosticReport id and the same Observation ids**.
Measured before the repair, with two different patients:

    message A   ALI AHMED      glucose  3.1 mmol/L   -> Patient/synthetic-patient
                                                        obs-synthetic-1
                                                        report-synthetic
    message B   FATIMA HASSAN  glucose 19.4 mmol/L   -> Patient/synthetic-patient
                                                        obs-synthetic-1
                                                        report-synthetic

In any FHIR store that upserts by resource id the second message silently
overwrites the first, or the two merge into one patient carrying contradictory
results — a hypoglycaemia and a severe hyperglycaemia on the same record. This
is the worst class of laboratory error: a result attributed to the wrong
patient.

Reachable through ``POST /fhir-interoperability/hl7/convert``.

Same shape as IA-061, where ``result_to_fhir`` published ``Patient/unknown``,
and the same repair: **refuse**. Both PID-3 and MSH-10 are required by HL7
v2.5 in an ORU^R01, so rejecting the message is correct in its own right and
not merely the safe option. The parse boundary refuses first; ``to_fhir_bundle``
refuses as well, because ``HL7Message`` is a public frozen dataclass that
callers construct without going through the parser.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

HL7_SOURCE = (
    pathlib.Path(__file__).resolve().parents[2]
    / "app" / "capabilities" / "fhir_interoperability" / "hl7.py"
)

#: The HL7 fields the bundle's identities and clinical codes are derived from,
#: with the segment position the parser reads each from. All four are Required
#: in an ORU^R01 under HL7 v2.5, so refusing a message that omits one is
#: faithful to the standard and not merely the cautious choice.
#:
#: Pinned as an exact mapping. A fifth field defaulted to a literal fails
#: test_no_identity_field_is_defaulted_with_or, and removing one from here
#: fails the parametrised refusal tests, so the ledger cannot drift from the
#: code in either direction.
REQUIRED_FIELDS = {
    "patient_identifier": "PID-3",
    "control_id": "MSH-10",
    "service_code": "OBR-4",
}

#: OBX-3 is handled separately: it is per-observation, not per-message, so it
#: cannot be driven by blanking one field of the template message.
OBSERVATION_CODE_FIELD = "OBX-3"

#: The literals that used to be substituted. Pinned so that none of them can
#: return under a different spelling of the same idea.
FORBIDDEN_PLACEHOLDERS = ("synthetic-patient", "synthetic", "unknown", "anonymous")


def _message(*, pid3: str = "PAT-001", control: str = "MSG-001",
             name: str = "ALI^AHMED", value: str = "5.5",
             service: str = "GLU^Glucose", obx_code: str = "GLU^Glucose") -> str:
    return (
        f"MSH|^~\\&|LAB|HOSP|GULA|MOH|20260101||ORU^R01|{control}|P|2.5\r"
        f"PID|1||{pid3}||{name}\r"
        f"OBR|1||ORD-1|{service}|||20260101\r"
        f"OBX|1|NM|{obx_code}||{value}|mmol/L|3.9-5.6|N|||F\r"
    )


# --------------------------------------------------------------------------
# positive control: the converter works, so the refusals below mean something
# --------------------------------------------------------------------------

def test_a_complete_message_still_converts():
    """Without this, refusing every message would pass the whole suite."""
    from app.capabilities.fhir_interoperability.hl7 import (
        parse_oru_r01,
        to_fhir_bundle,
    )

    bundle = to_fhir_bundle(parse_oru_r01(_message()))
    by_type = {e["resource"]["resourceType"]: e["resource"] for e in bundle["entry"]}

    assert by_type["Patient"]["id"] == "PAT-001"
    assert by_type["Observation"]["id"] == "obs-MSG-001-1"
    assert by_type["DiagnosticReport"]["id"] == "report-MSG-001"
    assert by_type["Observation"]["subject"]["reference"] == "Patient/PAT-001"
    assert by_type["Observation"]["valueQuantity"]["value"] == 5.5


# --------------------------------------------------------------------------
# the defect: no identity may be invented
# --------------------------------------------------------------------------

@pytest.mark.parametrize("missing", sorted(REQUIRED_FIELDS))
def test_the_parser_refuses_a_message_with_no_identity(missing):
    from app.capabilities.fhir_interoperability.hl7 import (
        HL7ConversionError,
        parse_oru_r01,
    )

    kwargs = {
        "patient_identifier": {"pid3": ""},
        "control_id": {"control": ""},
        "service_code": {"service": ""},
    }[missing]
    with pytest.raises(HL7ConversionError) as excinfo:
        parse_oru_r01(_message(**kwargs))

    assert REQUIRED_FIELDS[missing] in str(excinfo.value), (
        "the refusal must name the field the sender has to supply"
    )


def test_an_observation_with_no_analyte_code_is_refused():
    """OBX-3, the fifth substitution site — found by this suite's own ratchet.

    ``to_fhir_bundle`` published ``item.get("code") or "unknown"`` as
    ``Observation.code``, so an OBX with no identifier became a numeric
    result with no analyte: a glucose of 19.4 published as a measurement of
    "unknown". OBX-3 is Required in HL7 v2.5, and a test code is clinical
    semantics, which must not be invented.
    """
    from app.capabilities.fhir_interoperability.hl7 import (
        HL7ConversionError,
        parse_oru_r01,
    )

    with pytest.raises(HL7ConversionError) as excinfo:
        parse_oru_r01(_message(obx_code=""))
    assert OBSERVATION_CODE_FIELD in str(excinfo.value)


@pytest.mark.parametrize("missing", sorted(REQUIRED_FIELDS))
def test_the_bundle_builder_refuses_too(missing):
    """HL7Message is constructed directly by callers, bypassing the parser."""
    from app.capabilities.fhir_interoperability.hl7 import (
        HL7ConversionError,
        HL7Message,
        to_fhir_bundle,
    )

    fields = {
        "message_type": "ORU^R01",
        "control_id": "MSG-001",
        "sender": "LAB",
        "receiver": "GULA",
        "patient_identifier": "PAT-001",
        "patient_name": "ALI AHMED",
        "service_code": "GLU",
        "observed_at": "20260101",
        "observations": [{"code": "GLU", "value": "5.5", "unit": "mmol/L"}],
    }
    fields[missing] = None

    with pytest.raises(HL7ConversionError):
        to_fhir_bundle(HL7Message(**fields))


def test_two_identifierless_messages_can_no_longer_collide():
    """The defect stated as the collision itself, not as its cause.

    This is the assertion that would have caught IA-064 directly: it says
    nothing about placeholders, only that two distinct patients must never
    reach the same bundle identity.
    """
    from app.capabilities.fhir_interoperability.hl7 import (
        HL7ConversionError,
        parse_oru_r01,
        to_fhir_bundle,
    )

    a = _message(pid3="", control="", name="ALI^AHMED", value="3.1")
    b = _message(pid3="", control="", name="FATIMA^HASSAN", value="19.4")

    bundles = []
    for raw in (a, b):
        with pytest.raises(HL7ConversionError):
            bundles.append(to_fhir_bundle(parse_oru_r01(raw)))

    assert not bundles, (
        "an identifier-less message produced a bundle; before IA-064 both of "
        "these produced Patient/synthetic-patient with contradictory glucose "
        "values on one record"
    )


def test_distinct_patients_get_distinct_identities():
    """The converse, so the repair is not 'refuse everything'."""
    from app.capabilities.fhir_interoperability.hl7 import (
        parse_oru_r01,
        to_fhir_bundle,
    )

    a = to_fhir_bundle(parse_oru_r01(
        _message(pid3="PAT-A", control="MSG-A", name="ALI^AHMED", value="3.1")
    ))
    b = to_fhir_bundle(parse_oru_r01(
        _message(pid3="PAT-B", control="MSG-B", name="FATIMA^HASSAN", value="19.4")
    ))

    def identities(bundle):
        return {
            e["resource"]["resourceType"]: e["resource"]["id"]
            for e in bundle["entry"]
        }

    ia, ib = identities(a), identities(b)
    shared = {k for k in ia if ia[k] == ib[k]}
    assert not shared, f"two different patients share these ids: {sorted(shared)}"


# --------------------------------------------------------------------------
# shape ratchets, so the idiom cannot return in a fifth place
# --------------------------------------------------------------------------

def test_no_identity_field_is_defaulted_with_or():
    """AST: neither field may appear as the left side of a ``X or "literal"``.

    This is how all four sites were written. The behavioural tests above cover
    the four that existed; this covers the pattern.
    """
    tree = ast.parse(HL7_SOURCE.read_text())
    offenders: list[str] = []

    for node in ast.walk(tree):
        if not (isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or)):
            continue
        values = node.values
        for left, right in zip(values, values[1:]):
            names: set[str] = {
                sub.attr for sub in ast.walk(left) if isinstance(sub, ast.Attribute)
            }
            if not (names & set(REQUIRED_FIELDS)):
                continue
            if isinstance(right, ast.Constant) and isinstance(right.value, str):
                offenders.append(f"{sorted(names & set(REQUIRED_FIELDS))} or {right.value!r}")

    assert not offenders, (
        f"an identity field is being defaulted to a literal, which is exactly "
        f"how two patients came to share one FHIR id: {offenders}"
    )


def test_the_placeholder_literals_are_gone_from_executable_code():
    """The literals themselves, excluding docstrings and comments.

    Comments are not in the AST at all; docstrings are excluded by node id, so
    this suite's own quotation of the old code in a docstring cannot satisfy or
    trip the assertion.
    """
    source = HL7_SOURCE.read_text()
    tree = ast.parse(source)

    docstring_ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                docstring_ids.add(id(body[0].value))

    found: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstring_ids
            and node.value in FORBIDDEN_PLACEHOLDERS
        ):
            found.append(f"line {node.lineno}: {node.value!r}")

    assert not found, (
        f"a placeholder identity literal is back in executable code: {found}"
    )


def test_the_route_returns_422_not_500_for_an_unconvertible_message():
    """The guards in to_fhir_bundle must not surface as a server fault.

    It was called outside the try block that catches HL7ConversionError.
    """
    routes = (
        pathlib.Path(__file__).resolve().parents[2]
        / "app" / "capabilities" / "fhir_interoperability" / "routes.py"
    )
    tree = ast.parse(routes.read_text())

    handler = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "convert_hl7_to_fhir"
    )

    guarded = {
        sub.func.id
        for try_node in ast.walk(handler) if isinstance(try_node, ast.Try)
        for sub in ast.walk(try_node)
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name)
    }
    assert {"parse_oru_r01", "to_fhir_bundle"} <= guarded, (
        f"both conversion calls must sit inside the try that maps "
        f"HL7ConversionError to 422; guarded calls are {sorted(guarded)}"
    )
