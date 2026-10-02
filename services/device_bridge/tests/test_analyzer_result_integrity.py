"""The analyzer flagged a result abnormal and the bridge threw the flag away.

IA-050 (P1) — DISCOVERED, REPRODUCED, FIXED, VERIFIED.

An ASTM E1394 result record carries more than a value. Given exactly what a real
analyzer sends:

    3R|1|^^^Hb|13.5|g/dL|12.0-16.0|L|N|F|||20260101120000|20260101120500

the parser read positions 2, 3 and 4 and discarded everything after them:

    [ 5] reference range        = '12.0-16.0'       DISCARDED
    [ 6] abnormal flags         = 'L'               DISCARDED
    [ 7] nature of abnormality  = 'N'               DISCARDED
    [ 8] result status          = 'F'               DISCARDED
    [12] completed at           = '20260101120500'  DISCARDED
    [ 1] sequence               = '1'               DISCARDED

and the stored row read:

    reference_range  = ''
    status           = 'final'
    timestamp        = <the moment the bridge processed it>

So the instrument's own LOW flag was dropped, its reference range was replaced
with an empty string, and the bridge stamped the result `final` — a verified,
complete result — having performed no validation of any kind. The one piece of
information in that record that says "look at this result" was the piece thrown
away.

FIX, which carries data without interpreting it:
  * ASTMRecord, the row dict, ParsedResult and NormalizedResult retain
    reference range, abnormal flags, nature of abnormality, result status,
    completion time and the record sequence, verbatim, as opaque strings.
  * `reference_range` now prefers what the instrument sent, falling back to the
    caller's argument (which was previously the only source, and always empty).
  * `status` is "preliminary", not "final". The bridge validates nothing, so
    that is what it can attest; the instrument's own status is carried
    separately in `device_result_status`.
  * `timestamp` deliberately still means ingestion time. Changing what an
    existing field means would be a silent reinterpretation; the instrument's
    completion time is carried separately and unparsed, because its format is
    vendor-specific and guessing one would be an invention.

WHAT IS DELIBERATELY NOT DONE: nothing here decides what `L` means, parses
`12.0-16.0` into bounds, maps the ASTM status code `F` onto a FHIR or GULA
status, or reads `20260101120500` as a datetime. Those are clinical and
terminology decisions. The forward payload to GULA is also unchanged: mapping a
reference range onto the endpoint's `normal_range_low`/`normal_range_high` would
mean parsing it, and that endpoint has no field for an abnormal flag at all —
both belong to the IA-041 contract decision, which now has these values
available as inputs.

One existing test asserted `status == "final"`, encoding the defect as the
contract. Corrected, with the reason recorded there.
"""
from __future__ import annotations

import asyncio
from dataclasses import asdict

import pytest
from app.integration.gula_client import GulaClient
from app.pipeline.data_pipeline import DataPipeline
from app.pipeline.normalizer import Normalizer
from app.pipeline.parser_engine import ASTMParser, ParsedResult, calculate_checksum
from app.storage.db import InMemoryDB
from app.storage.result_repository import LogRepository, ResultRepository

_HEADER = "1H|\\^&|||Dev|||||P|1\r2P|1||PATIENT-A||Alpha^A\r"
_TERMINATOR = "9L|1|N\r"

# A full E1394 result record, exactly as the finding measured it.
_FULL_R = "3R|1|^^^Hb|13.5|g/dL|12.0-16.0|L|N|F|||20260101120000|20260101120500\r"


class _FakeGula(GulaClient):
    def __init__(self) -> None:
        super().__init__(base_url="http://example.invalid", lab_id="LAB001")
        self.sent: list = []

    async def send_results(self, results):  # type: ignore[override]
        self.sent.append(results)
        return {"status": "ok"}


def _frame(payload_text: str) -> bytes:
    payload = payload_text.encode("ascii")
    return b"\x02" + payload + b"\x03" + calculate_checksum(payload).encode("ascii") + b"\r\n"


def _pipeline() -> tuple[DataPipeline, InMemoryDB]:
    db = InMemoryDB()
    return (
        DataPipeline(
            parser=ASTMParser(),
            normalizer=Normalizer(),
            gula_client=_FakeGula(),
            result_repo=ResultRepository(db),
            log_repo=LogRepository(db),
        ),
        db,
    )


def _ingest(chunk: bytes, pipeline=None, db=None, device_id="CBC-01", fallback="FALLBACK"):
    if pipeline is None or db is None:
        pipeline, db = _pipeline()
    results = asyncio.run(
        pipeline.process_chunk(device_id=device_id, fallback_patient_id=fallback, chunk=chunk),
    )
    return results, db, pipeline


# ── the parser retains what the instrument sent ─────────────────────────────


def test_the_result_record_keeps_every_field_the_analyzer_sent():
    records = ASTMParser().parse_frame((_HEADER + _FULL_R + _TERMINATOR).encode("ascii"))
    result = next(r for r in records if r.type == "result")

    assert result.test_code == "Hb"
    assert result.value == "13.5"
    assert result.unit == "g/dL"
    assert result.sequence == "1"
    assert result.reference_range == "12.0-16.0"
    assert result.abnormal_flags == "L"
    assert result.nature_of_abnormality == "N"
    assert result.result_status == "F"
    assert result.completed_at == "20260101120500"


def test_a_short_record_does_not_raise():
    """Vendors truncate. A record with only a value must still parse, with the
    absent fields empty rather than an IndexError that rejects a usable result."""
    result = ASTMParser().parse_line("3R|1|^^^Hb|13.5")
    assert result.value == "13.5"
    assert result.unit == ""
    assert result.reference_range == ""
    assert result.abnormal_flags == ""
    assert result.result_status == ""
    assert result.completed_at == ""


def test_the_fields_are_carried_verbatim_and_uninterpreted():
    """A vendor flag this code has never seen must survive untouched. The moment
    something maps it, that mapping is a clinical decision that needs deciding
    first."""
    result = ASTMParser().parse_line("3R|1|^^^K|7.9|mmol/L|3.5-5.1|HH*|VENDOR_SPECIFIC|R")
    assert result.abnormal_flags == "HH*"
    assert result.nature_of_abnormality == "VENDOR_SPECIFIC"
    assert result.result_status == "R"
    assert result.reference_range == "3.5-5.1"


# ── the stored result carries them, and claims only what is true ───────────


def test_the_stored_result_keeps_the_abnormal_flag():
    """The clinical point of the whole finding."""
    results, db, _ = _ingest(_frame(_HEADER + _FULL_R + _TERMINATOR))
    assert len(results) == 1
    stored = db.results[0]

    assert stored["device_abnormal_flags"] == "L", (
        "the analyzer's own LOW flag is being discarded again"
    )
    assert stored["reference_range"] == "12.0-16.0"
    assert stored["device_result_status"] == "F"
    assert stored["device_nature_of_abnormality"] == "N"
    assert stored["device_completed_at"] == "20260101120500"


def test_the_bridge_does_not_claim_a_result_is_final():
    """The bridge performs no validation of any kind, so it cannot attest that a
    result is final -- and "final" is the one direction in which being wrong is
    unsafe."""
    results, _, _ = _ingest(_frame(_HEADER + _FULL_R + _TERMINATOR))
    assert results[0].status == "preliminary"
    assert results[0].status != "final"


def test_the_instruments_own_status_is_kept_separately():
    """So that a future, decided mapping has the input it needs -- without this
    commit making that mapping up."""
    results, _, _ = _ingest(_frame(_HEADER + _FULL_R + _TERMINATOR))
    assert results[0].device_result_status == "F"
    assert results[0].status == "preliminary", (
        "the device status must not be copied into the platform's own field; "
        "mapping ASTM status codes is a terminology decision"
    )


def test_an_absent_device_status_is_not_invented():
    results, _, _ = _ingest(_frame(_HEADER + "3R|1|^^^Hb|13.5|g/dL\r" + _TERMINATOR))
    assert results[0].device_result_status == ""
    assert results[0].device_abnormal_flags == ""
    assert results[0].reference_range == ""
    assert results[0].status == "preliminary"


def test_the_timestamp_still_means_ingestion_time():
    """Asserted so it is not silently reinterpreted later: `timestamp` is when
    the bridge processed the result, and the instrument's own completion time
    lives in `device_completed_at`, unparsed."""
    import datetime

    before = datetime.datetime.now(datetime.UTC)
    results, _, _ = _ingest(_frame(_HEADER + _FULL_R + _TERMINATOR))
    after = datetime.datetime.now(datetime.UTC)

    assert before <= results[0].timestamp <= after
    assert results[0].device_completed_at == "20260101120500"
    assert not isinstance(results[0].device_completed_at, datetime.datetime), (
        "the vendor date string must not be parsed; its format is vendor-specific"
    )


def test_the_normalizer_still_accepts_a_bare_parsed_result():
    """Positive control for the signature change: every existing caller, and the
    legacy ParserEngine path, construct ParsedResult with three fields."""
    normalized = Normalizer().transform(
        ParsedResult(test_code="Hb", value=13.5, unit="g/dL"),
        patient_id="P1",
        device_id="CBC-01",
    )
    assert normalized.test_name == "Hemoglobin"
    assert normalized.status == "preliminary"
    assert normalized.device_abnormal_flags == ""


def test_the_forward_payload_is_unchanged():
    """Deliberate: mapping a reference range onto the endpoint's
    normal_range_low/high means parsing it, and that endpoint has no field for
    an abnormal flag at all. Both belong to the IA-041 contract decision."""
    import inspect

    source = inspect.getsource(GulaClient.send_results)
    for field in ("abnormal", "reference_range", "normal_range", "device_result_status"):
        assert field not in source, (
            f"the forward payload now carries {field!r}; that is part of the "
            "IA-041 contract and must be decided, not guessed"
        )


# ── patient/result association, measured across the awkward cases ──────────


def test_a_second_frame_without_a_patient_record_stays_in_the_same_message():
    """VERIFIED_NEGATIVE, pinned. ASTM records span frames: a frame is transport,
    not a message boundary. The first message was not terminated, so continuing
    to attribute to its patient is correct, not a leak."""
    pipeline, db = _pipeline()
    _ingest(_frame(_HEADER + "3R|1|^^^Hb|13.5|g/dL\r"), pipeline, db)
    results, _, _ = _ingest(_frame("4R|2|^^^Glu|180|mg/dL\r"), pipeline, db)
    assert [r.patient_id for r in results] == ["PATIENT-A"]


def test_an_orphan_result_after_a_terminator_falls_back_to_the_request_patient():
    """Measured and recorded rather than "fixed". Once the terminator clears the
    message, a result with no patient record is attributed to the patient the
    /ingest caller declared -- which is what `fallback_patient_id` is for, and
    correct for the single-patient chunk that endpoint's contract describes.

    The residual hazard is stated rather than patched: in a multi-patient
    stream, an orphan result would be stamped with the request's patient. Fixing
    that means deciding whether an orphan result should be rejected instead, and
    that is a clinical identity rule -- see IA-041.
    """
    pipeline, db = _pipeline()
    _ingest(_frame(_HEADER + "3R|1|^^^Hb|13.5|g/dL\r" + _TERMINATOR), pipeline, db)
    results, _, _ = _ingest(_frame("4R|2|^^^Glu|180|mg/dL\r"), pipeline, db, fallback="FALLBACK")
    assert [r.patient_id for r in results] == ["FALLBACK"]


def test_two_patients_in_one_frame_are_kept_apart():
    results, _, _ = _ingest(
        _frame(
            _HEADER
            + "3R|1|^^^Hb|13.5|g/dL\r"
            + "4P|2||PATIENT-B||Beta^B\r"
            + "5R|2|^^^Glu|180|mg/dL\r",
        ),
    )
    assert [(r.patient_id, r.test_code) for r in results] == [
        ("PATIENT-A", "HEMOGLOBIN"),
        ("PATIENT-B", "GLU"),
    ]


def test_one_devices_patient_never_leaks_into_another_device():
    """VERIFIED_NEGATIVE and the most important one here: builder state is held
    per device session, so a second analyzer sending an orphan result gets its
    own request's fallback, not the first device's patient."""
    pipeline, db = _pipeline()
    _ingest(_frame(_HEADER + "3R|1|^^^Hb|13.5|g/dL\r"), pipeline, db,
            device_id="DEV-1", fallback="FB1")
    results, _, _ = _ingest(_frame("4R|2|^^^Glu|180|mg/dL\r"), pipeline, db,
                            device_id="DEV-2", fallback="FB2")
    assert [r.patient_id for r in results] == ["FB2"], (
        "device DEV-2 received DEV-1's patient -- builder state is leaking "
        "across device sessions"
    )


# ── ordering and duplicate delivery ────────────────────────────────────────


def test_results_keep_the_order_the_analyzer_sent_them():
    results, db, _ = _ingest(
        _frame(
            _HEADER
            + "3R|1|^^^Hb|13.5|g/dL\r"
            + "4R|2|^^^Glu|180|mg/dL\r"
            + "5R|3|^^^K|4.1|mmol/L\r"
            + _TERMINATOR,
        ),
    )
    assert [r.test_code for r in results] == ["HEMOGLOBIN", "GLU", "K"]
    assert [row["test_code"] for row in db.results] == ["HEMOGLOBIN", "GLU", "K"]
    assert [r.sequence for r in
            [rec for rec in ASTMParser().parse_frame(
                (_HEADER + "3R|1|^^^Hb|13.5|g/dL\r4R|2|^^^Glu|180|mg/dL\r").encode("ascii"))
             if rec.type == "result"]] == ["1", "2"]


def test_multiple_frames_in_one_chunk_are_all_processed_in_order():
    chunk = (
        _frame(_HEADER + "3R|1|^^^Hb|13.5|g/dL\r" + _TERMINATOR)
        + _frame("1H|\\^&|||Dev|||||P|1\r2P|1||PATIENT-B||Beta^B\r3R|1|^^^Glu|180|mg/dL\r" + _TERMINATOR)
    )
    results, _, _ = _ingest(chunk)
    assert [(r.patient_id, r.test_code) for r in results] == [
        ("PATIENT-A", "HEMOGLOBIN"),
        ("PATIENT-B", "GLU"),
    ]


@pytest.mark.parametrize("repeats", [2, 3])
def test_a_retransmitted_frame_is_delivered_again_not_deduplicated(repeats):
    """At-least-once with duplication, asserted so the semantics stay recorded.
    See test_the_parser_does_not_retain_a_message_identity_to_deduplicate_on for
    why deduplicating is not available."""
    pipeline, db = _pipeline()
    frame = _frame(_HEADER + "3R|1|^^^Hb|13.5|g/dL\r" + _TERMINATOR)
    for _ in range(repeats):
        _ingest(frame, pipeline, db)
    assert len(db.results) == repeats


# ── the audit trail records each accepted result once ──────────────────────


def test_each_accepted_result_produces_exactly_one_audit_event():
    _, db, _ = _ingest(
        _frame(_HEADER + "3R|1|^^^Hb|13.5|g/dL\r4R|2|^^^Glu|180|mg/dL\r" + _TERMINATOR),
    )
    saved = [e for e in db.audit_trail if e["event_type"] == "result_saved"]
    assert len(saved) == 2
    assert {e["payload"]["test_code"] for e in saved} == {"HEMOGLOBIN", "GLU"}
    assert {e["payload"]["patient_id"] for e in saved} == {"PATIENT-A"}


def test_a_rejected_row_produces_no_audit_event():
    """An audit trail that records results nobody accepted would be as wrong as
    one that omits results that were."""
    _, db, _ = _ingest(_frame(_HEADER + "3R|1|^^^Hb|NOTANUMBER|g/dL\r" + _TERMINATOR))
    assert [e for e in db.audit_trail if e["event_type"] == "result_saved"] == []
    assert [row for row in db.logs if row["status"] == "rejected"]


def test_the_audit_payload_names_the_patient_and_the_device():
    """Attribution: an audit row that cannot say whose result it was, from which
    instrument, is not an audit row."""
    _, db, _ = _ingest(_frame(_HEADER + _FULL_R + _TERMINATOR), device_id="CBC-77")
    event = next(e for e in db.audit_trail if e["event_type"] == "result_saved")
    assert event["payload"]["patient_id"] == "PATIENT-A"
    assert event["payload"]["device_id"] == "CBC-77"
    assert event["timestamp"]
