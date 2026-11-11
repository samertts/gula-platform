"""The forward contract, as executable requirements rather than prose.

IA-041 — DISCOVERED, REPRODUCED, NEEDS_DECISION. This file is the preparatory
work: every requirement the forward must satisfy, stated as a test, with the
three undecided pieces named individually so that deciding one flips one
assertion rather than requiring the whole thing to be rewritten.

`GulaClient.send_results` POSTs to `{base_url}/device/results`. The endpoint on
the other side is `backend/app/routes/device_results.py::receive_device_results`,
whose Pydantic models require:

    DeviceSubmission : barcode (required), device_id (optional), results (required)
    DeviceResult     : test_name (required), value, value_text, unit,
                       normal_range_low, normal_range_high

and whose handler depends on `get_current_user`, matches the sample through
`Sample.barcode == data.barcode`, and derives the tenant from
`current_user.lab_id`.

The bridge sends `{lab_id, results: [{patient_id, test_code, value, unit,
timestamp}]}` with no Authorization header. Measured on the backend side and
committed there (backend/tests/verification/test_device_bridge_forward_contract.py):

    validation : REJECTED
                   missing ('barcode',)                 Field required
                   missing ('results', 0, 'test_name')  Field required
    over HTTP  : 401 unauthenticated, 422 authenticated

The required field names below are transcribed from that module. They are not
imported: this suite must keep passing with only `services/device_bridge` on the
module path — the same constraint the image has, and the one whose absence hid
IA-044 — so it cannot import `backend`. The backend-side test is the half that
checks the transcription against the real models; if the two ever disagree, that
test fails there.

THE THREE PIECES THAT NEED A DECISION, each with its own assertion below:

  AUTH   — the bridge holds no credential for GULA and none exists. Inventing
           one means deciding how a service authenticates to this platform.

  SAMPLE — the endpoint matches a result to an order through a *sample* barcode.
           The bridge accepts a `barcode` on /ingest, so the obvious move is to
           pass it through. That move is wrong, and this is the finding's sharpest
           point: in the bridge, `barcode` is a *patient* lookup key —
           `PatientMatcher.barcode_map` maps barcode -> patient_id and
           `resolve_patient_id` returns it as the patient. Two fields, one name,
           different entities. Forwarding it would attach a result to whatever
           sample happened to share that string.

  TEST    — the endpoint wants `test_name`; the bridge has `test_code`.
            `TEST_NAME_MAP` holds three entries (HEMOGLOBIN/HB/HGB), so for every
            other analyte `test_name` is the raw code. Mapping a vendor code onto
            a catalog test name is clinical terminology.

IA-050 made the instrument's own reference range and abnormal flag available on
every result, which is new input for the SAMPLE and TEST decisions — the
endpoint has `normal_range_low`/`normal_range_high` fields and no abnormal-flag
field at all. Parsing "12.0-16.0" into those two numbers is part of the same
decision and is deliberately not done.
"""
from __future__ import annotations

import asyncio
import inspect

import pytest
from app.integration.gula_client import GulaClient
from app.pipeline.normalizer import Normalizer
from app.pipeline.parser_engine import ParsedResult

# Transcribed from backend/app/routes/device_results.py. The backend-side test
# checks this transcription against the real Pydantic models.
_SUBMISSION_REQUIRED = frozenset({"barcode", "results"})
_RESULT_REQUIRED = frozenset({"test_name"})
_RESULT_OPTIONAL = frozenset(
    {"value", "value_text", "unit", "normal_range_low", "normal_range_high"},
)
_ENDPOINT_PATH = "/device/results"

_CONTRACT_GAPS = ("AUTH", "SAMPLE", "TEST")

_RESOLVED_CONTRACT_GAPS: frozenset[str] = frozenset()
"""Gaps that have been decided and implemented. Empty: that is IA-041.

Adding a name here turns its assertion below from "the gap is still open" into
"the requirement is met", which is the whole point of writing the contract this
way -- deciding one piece costs one edit.
"""


class _CapturedPost(Exception):
    """Carries the payload out of the real send_results."""

    def __init__(self, payload: dict) -> None:
        super().__init__("captured")
        self.payload = payload


class _StubAsyncClient:
    """Stands in for httpx.AsyncClient so the REAL send_results runs.

    An earlier draft of this file subclassed GulaClient and rebuilt the payload
    in the override. NP-58 added `test_name` to the real method and every test
    here stayed green: the suite was testing the copy, which is the exact
    failure this file's docstring warns about. Intercepting the transport
    observes what the shipped method actually sends.
    """

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info) -> bool:
        return False

    async def post(self, url, json=None, **kwargs):
        raise _CapturedPost({"url": url, "json": json, "kwargs": kwargs})


def _one_result():
    return Normalizer().transform(
        ParsedResult(test_code="HEMOGLOBIN", value=13.5, unit="g/dL"),
        patient_id="12345",
        device_id="CBC-01",
    )


def _captured_post() -> dict:
    """Run the real send_results and return the url, json body and kwargs."""
    import httpx

    client = GulaClient(base_url="http://gula.invalid", lab_id="LAB001")
    real_client_class = httpx.AsyncClient
    httpx.AsyncClient = _StubAsyncClient  # type: ignore[misc]
    captured: dict | None = None
    try:
        async def drive():
            nonlocal captured
            # send_results catches every exception, so the capture travels back
            # through the sentinel rather than out of the call.
            try:
                await GulaClient.send_results.__wrapped__(client, [_one_result()])  # type: ignore[attr-defined]
            except AttributeError:
                await client.send_results([_one_result()])

        try:
            asyncio.run(drive())
        except _CapturedPost as exc:  # pragma: no cover - defensive
            captured = exc.payload
    finally:
        httpx.AsyncClient = real_client_class  # type: ignore[misc]

    if captured is None:
        # send_results swallowed the sentinel. Re-run and dig it out of the
        # recorded warning path by capturing inside the stub instead.
        holder: dict = {}

        class _Recording(_StubAsyncClient):
            async def post(self, url, json=None, **kwargs):
                holder.update({"url": url, "json": json, "kwargs": kwargs})
                raise RuntimeError("stop after capture")

        httpx.AsyncClient = _Recording  # type: ignore[misc]
        try:
            asyncio.run(client.send_results([_one_result()]))
        finally:
            httpx.AsyncClient = real_client_class  # type: ignore[misc]
        captured = holder

    assert captured, "the real send_results never reached the transport"
    return captured


def _real_payload() -> dict:
    return _captured_post()["json"]


# ── the payload the bridge actually builds ──────────────────────────────────


def test_the_capture_observes_the_real_send_results():
    """Guard on this file's own fidelity, and the one NP-58 had to break.

    The payload is captured at the transport, so it is what the shipped method
    builds -- not a transcription. The result key set is asserted exactly, so a
    field appearing or disappearing fails here first.
    """
    captured = _captured_post()
    assert captured["url"].endswith(_ENDPOINT_PATH)
    assert set(captured["json"]) == {"lab_id", "results"}
    assert set(captured["json"]["results"][0]) == {
        "patient_id", "test_code", "value", "unit", "timestamp",
    }, (
        "the forward payload's fields changed; if a contract gap was closed, "
        "record it in _RESOLVED_CONTRACT_GAPS"
    )


def test_the_payload_is_missing_the_fields_the_endpoint_requires():
    payload = _real_payload()
    missing_top = _SUBMISSION_REQUIRED - set(payload)
    missing_item = _RESULT_REQUIRED - set(payload["results"][0])

    if {"SAMPLE", "TEST"} <= _RESOLVED_CONTRACT_GAPS:
        assert missing_top == set() and missing_item == set()
        return

    assert missing_top == {"barcode"}, (
        f"the missing top-level requirement set changed: {missing_top}"
    )
    assert missing_item == {"test_name"}, (
        f"the missing result requirement set changed: {missing_item}"
    )


def test_the_payload_sends_a_field_the_endpoint_does_not_have():
    """`lab_id` is ignored by the endpoint, which derives the tenant from the
    caller. Harmless today, and recorded so that "just send lab_id" is never
    mistaken for the authentication answer."""
    payload = _real_payload()
    assert "lab_id" in payload
    assert payload["lab_id"] == "LAB001", "the hardcoded lab id is still hardcoded"


# ── AUTH ────────────────────────────────────────────────────────────────────


@pytest.mark.skipif("AUTH" in _RESOLVED_CONTRACT_GAPS, reason="AUTH decided")
def test_auth_gap_the_bridge_sends_no_credential():
    """The endpoint depends on get_current_user. Nothing in this service holds a
    GULA credential, and LABLINK_API_KEY is the key *inbound* callers present to
    the bridge -- it is not a credential the bridge can present to GULA."""
    source = inspect.getsource(GulaClient)
    for header in ("Authorization", "Bearer", "headers="):
        assert header not in source, (
            f"GulaClient now sets {header!r}; if a service credential was "
            "introduced, add 'AUTH' to _RESOLVED_CONTRACT_GAPS"
        )
    assert "LABLINK_API_KEY" not in source, (
        "the inbound API key must not be reused as an outbound credential: it "
        "authenticates devices TO the bridge, not the bridge to GULA"
    )


def test_auth_requirement_when_it_is_decided():
    """What "decided" has to mean, written now so it is not re-litigated later:
    a credential, sent as a header, that is not the inbound device key."""
    if "AUTH" not in _RESOLVED_CONTRACT_GAPS:
        pytest.skip("AUTH is still open -- IA-041")
    source = inspect.getsource(GulaClient)
    assert "headers=" in source
    assert "LABLINK_API_KEY" not in source


# ── SAMPLE ──────────────────────────────────────────────────────────────────


@pytest.mark.skipif("SAMPLE" in _RESOLVED_CONTRACT_GAPS, reason="SAMPLE decided")
def test_sample_gap_the_barcode_the_bridge_holds_is_not_the_one_the_endpoint_wants():
    """The sharpest point in this finding, asserted so the obvious wrong fix is
    blocked: both sides have a field called `barcode` and they mean different
    entities.

    In the bridge it is a patient lookup key -- barcode_map maps it to a
    patient_id and resolve_patient_id returns that as the patient. In the
    endpoint it is a *sample* barcode, matched as `Sample.barcode ==
    data.barcode` to find the order. Forwarding one as the other would attach a
    result to whatever sample happened to share the string.
    """
    from app.pipeline.patient_matching import PatientMatcher

    matcher = PatientMatcher(barcode_map={"BC-1": "PATIENT-7"})
    resolved = matcher.resolve_patient_id(
        row_patient_id="", fallback_patient_id="FB", barcode="BC-1",
    )
    assert resolved == "PATIENT-7", (
        "in this service a barcode resolves to a PATIENT; that is why it cannot "
        "be forwarded as the endpoint's sample barcode"
    )

    # And it is dropped before the forward, so no sample barcode is sent at all.
    assert "barcode" not in _real_payload()
    assert "barcode" not in inspect.getsource(GulaClient.send_results)


def test_sample_gap_the_barcode_map_is_never_populated():
    """Recorded because it bounds the gap: even the patient-by-barcode path is
    inert -- DataPipeline constructs PatientMatcher with no map, so the only
    patient sources in production are the ASTM P record and the request
    fallback."""
    source = inspect.getsource(
        __import__("app.pipeline.data_pipeline", fromlist=["DataPipeline"]).DataPipeline.__init__,
    )
    assert "PatientMatcher()" in source, (
        "a barcode map is now supplied; re-check the SAMPLE gap"
    )


# ── TEST ────────────────────────────────────────────────────────────────────


@pytest.mark.skipif("TEST" in _RESOLVED_CONTRACT_GAPS, reason="TEST decided")
def test_test_gap_there_is_no_code_to_name_mapping_to_speak_of():
    from app.pipeline.normalizer import TEST_NAME_MAP

    assert set(TEST_NAME_MAP) == {"HEMOGLOBIN", "HB", "HGB"}, (
        f"TEST_NAME_MAP changed: {sorted(TEST_NAME_MAP)}. If a real mapping was "
        "introduced, it is a clinical terminology decision -- record it and add "
        "'TEST' to _RESOLVED_CONTRACT_GAPS"
    )
    assert set(TEST_NAME_MAP.values()) == {"Hemoglobin"}

    # Any other analyte falls through to the raw code.
    normalized = Normalizer().transform(
        ParsedResult(test_code="GLU", value=180.0, unit="mg/dL"),
        patient_id="P1",
        device_id="CBC-01",
    )
    assert normalized.test_name == "GLU", (
        "test_name for an unmapped analyte is the vendor code, which is not a "
        "catalog test name"
    )


def test_the_mapping_engine_is_equally_thin():
    from app.pipeline.test_mapping import TestMappingEngine

    engine = TestMappingEngine()
    assert set(engine.mapping) == {"HB", "HGB"}
    assert engine.canonical_code("GLU") == "GLU", (
        "an unmapped code passes through uppercased; it is not canonicalised"
    )


# ── what IA-050 made available for these decisions ─────────────────────────


def test_the_inputs_the_decision_now_has_that_it_did_not_before():
    """IA-050 stopped the bridge discarding these. They are inputs to the
    SAMPLE and TEST decisions, not a licence to guess: the endpoint has
    normal_range_low/normal_range_high and no abnormal-flag field, so parsing
    "12.0-16.0" into two numbers is part of the decision."""
    from app.pipeline.parser_engine import ASTMParser

    record = ASTMParser().parse_line("3R|1|^^^Hb|13.5|g/dL|12.0-16.0|L|N|F")
    assert record.reference_range == "12.0-16.0"
    assert record.abnormal_flags == "L"
    assert record.result_status == "F"

    assert "normal_range_low" in _RESULT_OPTIONAL
    assert "normal_range_high" in _RESULT_OPTIONAL
    assert not any("abnormal" in field for field in _RESULT_OPTIONAL | _RESULT_REQUIRED), (
        "the endpoint has no abnormal-flag field, so the instrument's flag has "
        "nowhere to go in the current contract"
    )

    # Not parsed anywhere: that would be the invention.
    assert record.reference_range == "12.0-16.0"
    assert not isinstance(record.reference_range, tuple)


# ── the ledger ──────────────────────────────────────────────────────────────


def test_no_contract_gap_is_resolved_yet():
    """The honest ledger. This file is green *with all three gaps declared
    open*; that is a record of the gap, not its resolution. When one is decided
    and implemented, add it here and the matching assertion above becomes a
    requirement instead of a measurement."""
    assert frozenset() == _RESOLVED_CONTRACT_GAPS, (
        f"resolved: {sorted(_RESOLVED_CONTRACT_GAPS)} -- re-read this file's "
        "docstring and confirm each resolved gap now has a real requirement"
    )
    assert set(_CONTRACT_GAPS) == {"AUTH", "SAMPLE", "TEST"}


def test_the_forward_still_cannot_succeed_and_fails_softly():
    """The consequence, so it is never mistaken for a working integration:
    GulaClient catches every exception and returns {"status": "failed"}, which
    /ingest turns into a forward_failed log row and an offline-queue entry --
    while still answering HTTP 200 {"status": "ok"}."""
    source = inspect.getsource(GulaClient.send_results)
    assert "except Exception" in source
    assert '"status": "failed"' in source
