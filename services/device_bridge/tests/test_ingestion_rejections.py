"""Analyzer input that cannot be used must leave a record, not vanish.

IA-039 (P1). `DataPipeline.process_chunk` had three silent drop sites, and the
asymmetry they created was the defect: a *forward* failure (GULA unreachable) was
recoverable -- `retry_queue.enqueue` -> `/ingest` drains it into the offline queue
and the sync engine -- while a *parse or validation* failure was recorded nowhere
at all.

Measured on the real pipeline before the fix (reproduction in the commit message):

    every frame has a bad checksum   -> 0 results, 0 result rows, 0 log rows
    result value is not a number     -> 0 results, 0 result rows, 0 log rows
    row carries no test code         -> 0 results, 0 result rows, 0 log rows
    good row + unparseable row       -> 1 result, and one log row: "processed"

The last line is the worst of them. A frame carrying haemoglobin *and* glucose was
recorded as processed with the glucose silently gone -- a failure turned into a
success claim. `/ingest` answers HTTP 200 `{"status": "ok", "processed": 0}` in
every case above, and nothing in the service contradicted it.

Three causes, all fixed here:

  * `if not row["test_code"] or not row["value"]: continue` -- a bare continue.
  * `except Exception: logger.exception("Invalid ASTM frame")` wrapped the whole
    per-frame block including the row loop, so one unparseable value abandoned
    every row after it in that frame, and every cause was mislabeled as invalid
    framing whether it was a checksum, a mapping or an adapter fault.
  * `if not normalized_results: return` sat in front of the only `log_repo.save`,
    so a chunk whose every frame failed never reached a log row at all.

A related wiring defect found while fixing it: `DataPipeline` was constructed
without `result_repo`/`log_repo`, so it built its own `InMemoryDB` and every row
it wrote went to a store no endpoint reads. `/ingest` papered over that for
results by saving them a second time into the served store; the per-chunk log row
was simply invisible. Rejection records would have been invisible too, which is
why the wiring is part of this fix rather than a separate one.

What is deliberately NOT claimed here: these records live in `InMemoryDB` and do
not survive a restart (IA-040, raised separately as NEEDS_DECISION -- a durable
store for this service is a new persistence layer with deployment implications).
A rejection is recorded and queryable; it is not yet durable.
"""
from __future__ import annotations

import asyncio
import pathlib

import pytest
from app.integration.gula_client import GulaClient
from app.pipeline.data_pipeline import DataPipeline
from app.pipeline.normalizer import Normalizer
from app.pipeline.parser_engine import ASTMParser, calculate_checksum
from app.storage.db import InMemoryDB
from app.storage.result_repository import LogRepository, ResultRepository

_SERVICE = pathlib.Path(__file__).resolve().parents[1]
_PIPELINE_SRC = _SERVICE / "app" / "pipeline" / "data_pipeline.py"
_AUTH_SRC = _SERVICE / "app" / "security" / "auth.py"
_MAIN_SRC = _SERVICE / "app" / "main.py"

_HEADER = "1H|\\^&|||Device|||||P|1\r2P|1||12345||Doe^John\r"


class _FakeGula(GulaClient):
    def __init__(self) -> None:
        super().__init__(base_url="http://example.invalid", lab_id="LAB001")
        self.sent: list = []

    async def send_results(self, results):  # type: ignore[override]
        self.sent.append(results)
        return {"status": "ok"}


def _frame(payload_text: str, *, checksum: str | None = None) -> bytes:
    payload = payload_text.encode("ascii")
    cs = (checksum or calculate_checksum(payload)).encode("ascii")
    return b"\x02" + payload + b"\x03" + cs + b"\r\n"


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


def _ingest(chunk: bytes, pipeline: DataPipeline | None = None, db: InMemoryDB | None = None):
    if pipeline is None or db is None:
        pipeline, db = _pipeline()
    results = asyncio.run(
        pipeline.process_chunk(device_id="CBC-01", fallback_patient_id="FB", chunk=chunk),
    )
    return results, db, pipeline


def _rows(db: InMemoryDB, status: str) -> list[dict]:
    return [row for row in db.logs if row["status"] == status]


# ── the positive control, first ───────────────────────────────────────────────


def test_a_valid_frame_is_still_processed_and_still_says_processed():
    """A suite that only forbids things passes on a pipeline that accepts nothing.

    This also pins the unchanged shape of the success record: status "processed"
    with an empty error_message, exactly as before the fix.
    """
    results, db, pipeline = _ingest(_frame(_HEADER + "3R|1|^^^Hb|13.5|g/dL\r"))
    assert [r.test_code for r in results] == ["HEMOGLOBIN"]
    assert len(db.results) == 1
    assert [(r["status"], r["error_message"]) for r in db.logs] == [("processed", "")]
    assert len(pipeline.gula_client.sent) == 1  # type: ignore[attr-defined]


# ── every drop site now leaves a record ──────────────────────────────────────


def test_a_frame_with_a_bad_checksum_is_recorded_as_rejected():
    results, db, _ = _ingest(_frame(_HEADER + "3R|1|^^^Hb|13.5|g/dL\r", checksum="ZZ"))
    assert results == []
    rejected = _rows(db, "rejected")
    assert len(rejected) == 1
    assert "frame_ParserError" in rejected[0]["error_message"]
    assert "Checksum mismatch" in rejected[0]["error_message"]


def test_a_non_numeric_result_value_is_recorded_as_rejected():
    results, db, _ = _ingest(_frame(_HEADER + "3R|1|^^^Hb|NOTANUMBER|g/dL\r"))
    assert results == []
    rejected = _rows(db, "rejected")
    assert len(rejected) == 1
    assert "row_ValueError" in rejected[0]["error_message"]
    assert "row 0" in rejected[0]["error_message"]


@pytest.mark.parametrize(
    ("line", "expected_reason"),
    [
        ("3R|1|^^^|13.5|g/dL\r", "row_missing_test_code"),
        ("3R|1|^^^Hb||g/dL\r", "row_missing_value"),
        ("3R|1|^^^||g/dL\r", "row_missing_test_code_and_value"),
    ],
)
def test_an_incomplete_row_is_recorded_rather_than_skipped(line, expected_reason):
    """This was the bare `continue`. The row named which analyte it carried, or
    what the value was, and the service kept neither."""
    results, db, _ = _ingest(_frame(_HEADER + line))
    assert results == []
    rejected = _rows(db, "rejected")
    assert len(rejected) == 1
    assert rejected[0]["error_message"].startswith(expected_reason)


def test_a_chunk_that_is_not_astm_at_all_is_recorded_rather_than_discarded():
    """An analyzer configured for the wrong protocol, or pointed at the wrong
    port. There is no STX, so the assembler clears the buffer: the bytes are
    gone, and that is now distinguishable from waiting for more of them."""
    results, db, _ = _ingest(b"MSH|^~\\&|LIS|LAB|||20260101||ORU^R01|1|P|2.5\r")
    assert results == []
    rejected = _rows(db, "rejected")
    assert len(rejected) == 1
    assert rejected[0]["error_message"].startswith("unframed_chunk")


# ── the fail-safe direction: incomplete is not lost ──────────────────────────


def test_a_frame_still_arriving_is_not_called_a_rejection():
    """The counterpart that keeps the fix honest. ASTM is streamed, so a chunk
    ending mid-frame is normal. Recording that as a rejection would bury the
    real ones in false alarms, so this asserts silence -- and then asserts the
    continuation produces the result, proving the silence was not a loss."""
    pipeline, db = _pipeline()
    partial = b"\x02" + (_HEADER + "3R|1|^^^Hb|13.5|g/dL\r").encode("ascii")
    results, _, _ = _ingest(partial, pipeline, db)
    assert results == []
    assert db.logs == [], f"a buffered frame was reported as an outcome: {db.logs}"

    payload = (_HEADER + "3R|1|^^^Hb|13.5|g/dL\r").encode("ascii")
    rest = b"\x03" + calculate_checksum(payload).encode("ascii") + b"\r\n"
    results, _, _ = _ingest(rest, pipeline, db)
    assert [r.test_code for r in results] == ["HEMOGLOBIN"]
    assert _rows(db, "rejected") == []
    assert len(_rows(db, "processed")) == 1


# ── partial acceptance is never reported as success ──────────────────────────


def test_one_bad_row_no_longer_abandons_the_rows_after_it():
    """The frame-wide `except` meant row 3 was lost because row 2 was unparseable.
    Three results in, one unusable, and the other two must both survive."""
    results, db, _ = _ingest(
        _frame(
            _HEADER
            + "3R|1|^^^Hb|13.5|g/dL\r"
            + "4R|2|^^^Glu|BROKEN|mg/dL\r"
            + "5R|3|^^^K|4.1|mmol/L\r",
        ),
    )
    # "K" has no entry in TestMappingEngine's two-code table and passes through
    # uppercased; what matters here is that the third row survived the second.
    assert [r.test_code for r in results] == ["HEMOGLOBIN", "K"]
    rejected = _rows(db, "rejected")
    assert len(rejected) == 1
    assert "row 1" in rejected[0]["error_message"]


def test_a_chunk_that_lost_a_result_is_not_recorded_as_processed():
    """The clinical point of the whole finding: a record saying "processed" for a
    chunk that dropped a result is a failure reported as a success."""
    results, db, _ = _ingest(
        _frame(_HEADER + "3R|1|^^^Hb|13.5|g/dL\r4R|2|^^^Glu|BROKEN|mg/dL\r"),
    )
    assert len(results) == 1
    assert _rows(db, "processed") == [], "a lossy chunk was recorded as fully processed"
    partial = _rows(db, "partially_processed")
    assert len(partial) == 1
    assert partial[0]["error_message"] == "1 rejected"


@pytest.mark.parametrize(
    "chunk_text",
    [
        _HEADER + "3R|1|^^^Hb|NOTANUMBER|g/dL\r",
        _HEADER + "3R|1|^^^|13.5|g/dL\r",
        _HEADER + "3R|1|^^^Hb|13.5|g/dL\r4R|2|^^^Glu|BROKEN|mg/dL\r",
    ],
)
def test_no_lossy_chunk_anywhere_is_recorded_as_plainly_processed(chunk_text):
    """The invariant, over every loss shape: if anything was rejected, no log row
    for that chunk may claim unqualified success."""
    _, db, _ = _ingest(_frame(chunk_text))
    assert _rows(db, "rejected"), "the loss itself was not recorded"
    assert _rows(db, "processed") == []


# ── the wiring: a record nobody can read is not a record ─────────────────────


def test_the_served_store_is_the_store_the_pipeline_writes_to():
    """`/ingest` and the pipeline must share one InMemoryDB. Left to its default
    the pipeline built its own, so its rows were unreachable through the API."""
    import app.main as main

    assert main.pipeline.result_repo is main.repository
    assert main.pipeline.log_repo.db is main.repository.db


def test_a_rejected_chunk_is_visible_through_the_api():
    """End to end over HTTP, which is the only view an operator has."""
    import app.main as main
    from fastapi.testclient import TestClient

    main.repository.db.logs.clear()
    main.repository.db.results.clear()
    main.pipeline.sessions.clear()

    client = TestClient(main.app)
    import os

    headers = {"x-api-key": os.environ["LABLINK_API_KEY"]}
    body = {
        "patient_id": "FB",
        "device_id": "CBC-99",
        "chunk": _frame(_HEADER + "3R|1|^^^Hb|NOTANUMBER|g/dL\r").decode("latin-1"),
    }
    response = client.post("/ingest", json=body, headers=headers)
    assert response.status_code == 200
    assert response.json()["processed"] == 0

    logs = client.get("/logs", headers=headers).json()
    statuses = [row["status"] for row in logs]
    assert "rejected" in statuses, f"HTTP 200, nothing processed, and no record: {statuses}"
    assert any("row_ValueError" in row["error_message"] for row in logs)


def test_a_result_reaches_the_served_store_exactly_once():
    """The wiring's own regression: `/ingest` used to save results a second time.
    Now that both write to one store, saving twice would duplicate every row."""
    import os

    import app.main as main
    from fastapi.testclient import TestClient

    main.repository.db.logs.clear()
    main.repository.db.results.clear()
    main.pipeline.sessions.clear()

    client = TestClient(main.app)
    headers = {"x-api-key": os.environ["LABLINK_API_KEY"]}
    body = {
        "patient_id": "FB",
        "device_id": "CBC-98",
        "chunk": _frame(_HEADER + "3R|1|^^^Hb|13.5|g/dL\r").decode("latin-1"),
    }
    response = client.post("/ingest", json=body, headers=headers)
    assert response.status_code == 200
    assert response.json()["processed"] == 1

    results = client.get("/results", headers=headers).json()
    assert len(results) == 1, f"the result was stored {len(results)} times"


# ── source ratchets, so the drop sites cannot come back ──────────────────────


def test_no_drop_site_is_a_bare_continue_again():
    source = _PIPELINE_SRC.read_text()
    assert 'if not row["test_code"] or not row["value"]:\n                        continue' not in source
    assert "rejections.append" in source
    assert 'logger.exception("Invalid ASTM frame"' not in source, (
        "every cause was being labelled as invalid framing"
    )


def test_the_rejection_records_are_written_before_the_empty_result_shortcut():
    """`if not normalized_results: return` in front of the recording is exactly
    how a chunk whose every frame failed left no trace."""
    source = _PIPELINE_SRC.read_text()
    record_at = source.index("for reason, detail, source_text in rejections:")
    shortcut_at = source.index("if not normalized_results:\n            return normalized_results")
    assert record_at < shortcut_at, (
        "the shortcut runs before the rejections are recorded, so a total failure "
        "is silent again"
    )


def test_the_pipeline_is_wired_to_the_served_store_in_source():
    source = _MAIN_SRC.read_text()
    assert "result_repo=repository" in source
    assert "log_repo=LogRepository(repository.db)" in source
    assert "    repository.save_results(results)\n" not in source, (
        "the duplicate save is back; every result would be stored twice"
    )


def test_no_default_api_key_constant_is_reintroduced():
    """Two test modules were uncollectable because they imported a
    `DEFAULT_API_KEY` that had been removed from `app.security.auth` -- removed
    correctly, since a hardcoded default key is a credential in the source tree.
    The tests were repaired to read the environment; this keeps the constant from
    coming back as the easier way to fix them."""
    source = _AUTH_SRC.read_text()
    assert "DEFAULT_API_KEY" not in source
    assert 'API_KEY_ENV = "LABLINK_API_KEY"' in source


# ── the forward half of the same symmetry ────────────────────────────────────


class _UnreachableGula(GulaClient):
    """What GulaClient returns when the POST cannot be made: it catches every
    exception and reports {"status": "failed"}."""

    async def send_results(self, results):  # type: ignore[override]
        return {"status": "failed", "error": "[Errno -2] Name or service not known"}


def test_a_result_that_never_reached_gula_is_recorded_too():
    """The retry queue and the edge buffer already carried this, but neither is
    readable through the API, so a bridge that has never once delivered a result
    looked exactly like one that always does."""
    db = InMemoryDB()
    pipeline = DataPipeline(
        parser=ASTMParser(),
        normalizer=Normalizer(),
        gula_client=_UnreachableGula(base_url="http://gula.invalid", lab_id="LAB001"),
        result_repo=ResultRepository(db),
        log_repo=LogRepository(db),
    )
    results, _, _ = _ingest(_frame(_HEADER + "3R|1|^^^Hb|13.5|g/dL\r"), pipeline, db)

    assert len(results) == 1  # parsed and stored locally
    assert pipeline.retry_queue.size() == 1
    failed = _rows(db, "forward_failed")
    assert len(failed) == 1
    assert "Name or service not known" in failed[0]["error_message"]


def test_the_backend_url_comes_from_the_documented_environment_variable():
    """GULA_BACKEND_URL is set by docker-compose and documented in
    docs/configuration/CONFIGURATION_REFERENCE.md as the URL the device bridge
    forwards results to. It was read by nothing: the only os.getenv in the whole
    service was the API key, and the URL was hardcoded to a host that does not
    exist on the compose network."""
    source = _MAIN_SRC.read_text()
    assert 'os.getenv(GULA_BACKEND_URL_ENV, "")' in source
    assert 'GULA_BACKEND_URL_ENV = "GULA_BACKEND_URL"' in source
    assert 'GulaClient(base_url="http://gula.local"' not in source, (
        "the backend URL is hardcoded again"
    )


def test_an_unset_backend_url_does_not_become_an_empty_base_url():
    """An empty GULA_BACKEND_URL must not produce POSTs to "/device/results"
    with no host. The previous literal is kept as the fallback so behaviour
    without the variable is unchanged."""
    import importlib
    import os

    import app.main as main

    previous = os.environ.get("GULA_BACKEND_URL")
    try:
        os.environ["GULA_BACKEND_URL"] = "   "
        reloaded = importlib.reload(main)
        assert reloaded.pipeline.gula_client.base_url == "http://gula.local"

        os.environ["GULA_BACKEND_URL"] = "http://gula-backend:8000/"
        reloaded = importlib.reload(main)
        assert reloaded.pipeline.gula_client.base_url == "http://gula-backend:8000"
    finally:
        if previous is None:
            os.environ.pop("GULA_BACKEND_URL", None)
        else:
            os.environ["GULA_BACKEND_URL"] = previous
        importlib.reload(main)
