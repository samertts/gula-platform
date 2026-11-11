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


# ── IA-044: the image could not import the application at all ───────────────


def test_the_app_imports_with_only_its_own_tree_on_the_path():
    """The Dockerfile's build context is this directory and it copies only
    `app/`, so `backend` is not in the image. Four modules imported
    `backend.app._compat` for UTC, and `import app.main` raised

        ModuleNotFoundError: No module named 'backend'

    which means the published image could not start: the compose healthcheck
    polls /health, which never answered, so the documented
    `docker compose --profile device-bridge up device-bridge` could not come up.

    Every local test run put the repository root on PYTHONPATH, which satisfied
    the import and hid the failure for as long as nobody ran the image. This
    test reproduces the image's module path in a subprocess -- a clean
    environment with only this directory importable -- because that is the only
    way to observe it from inside a test run that has the root on the path.
    """
    import os
    import subprocess
    import sys

    env = {
        k: v
        for k, v in os.environ.items()
        if k not in {"PYTHONPATH", "PYTHONHOME"}
    }
    env["LABLINK_API_KEY"] = "import-probe-key"
    completed = subprocess.run(
        [sys.executable, "-c", "import sys; sys.path.insert(0, '.'); import app.main"],
        cwd=_SERVICE,
        env=env,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, (
        "the application cannot be imported with the module path the image has:\n"
        + completed.stderr[-2000:]
    )


def test_no_module_imports_from_a_sibling_tree():
    """The ratchet on the root cause. A service whose image contains only its own
    `app/` tree must not import from `backend/` or `shared/`."""
    offenders = []
    for path in (_SERVICE / "app").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith(("from backend", "import backend", "from shared", "import shared")):
                offenders.append(f"{path.relative_to(_SERVICE).as_posix()}:{lineno}: {stripped}")
    assert offenders == [], offenders


def test_the_local_compat_shim_gives_a_real_utc():
    """The copy it replaced had a dead branch that would have raised: for
    Python < 3.11 it read `UTC = UTC`, a self-reference. Unreachable on 3.11+,
    but a trap, so the local copy uses timezone.utc there."""
    import datetime

    from app._compat import UTC, StrEnum

    assert UTC is datetime.UTC
    assert datetime.datetime.now(UTC).tzinfo is not None
    assert issubclass(StrEnum, str)

    source = (_SERVICE / "app" / "_compat.py").read_text()
    assert "UTC = UTC" not in source, "the self-referential fallback is back"
    assert "UTC = timezone.utc" in source

    # `ruff check --fix` reintroduced exactly this defect once: rule UP017
    # rewrites `timezone.utc` to `datetime.UTC` without noticing it is inside a
    # `sys.version_info < (3, 11)` branch, where that name does not exist. The
    # suppression must stay, or the next automated fix run breaks the shim
    # again — and this test is the only thing that caught it.
    assert "noqa: UP017" in source, (
        "the UP017 suppression is gone; a `ruff --fix` run will rewrite the "
        "pre-3.11 fallback to `UTC = UTC` and the shim will raise NameError"
    )


def test_pyserial_is_declared_as_a_dependency():
    """`from serial import Serial` in app/connectors/base.py is lazy, so a
    missing pyserial breaks the first serial analyzer connection rather than
    startup. It was declared nowhere.

    UNVERIFIED by this test, and said so in the finding: the Dockerfile installs
    an explicit package list that still omits pyserial, and no image could be
    built here to confirm a fix, so only the declaration is asserted.
    """
    pyproject = (_SERVICE / "pyproject.toml").read_text()
    assert "pyserial" in pyproject


# ── IA-045: the retry queue was never drained, so the backlog multiplied ────


def _ingest_over_http(client, headers, chunk: bytes, device_id: str = "AMP-01"):
    return client.post(
        "/ingest",
        json={"patient_id": "FB", "device_id": device_id, "chunk": chunk.decode("latin-1")},
        headers=headers,
    )


def _fresh_app(monkeypatch, *, backend_url: str):
    """A reimported app.main with a chosen GULA_BACKEND_URL and empty stores."""
    import importlib
    import os

    monkeypatch.setenv("GULA_BACKEND_URL", backend_url)
    import app.main as main

    main = importlib.reload(main)
    main.repository.db.results.clear()
    main.repository.db.logs.clear()
    main.repository.db.audit_trail.clear()
    main.repository.db.offline_queue.clear()
    main.pipeline.sessions.clear()
    while main.pipeline.retry_queue.dequeue() is not None:
        pass
    return main


def test_the_offline_backlog_grows_once_per_failure_not_quadratically(monkeypatch):
    """Measured over HTTP against an unreachable GULA, before the fix:

        ingest   results  offline  audit
        1        1        1        2
        2        2        3        5
        3        3        6        9
        4        4        10       14
        5        5        15       20
        6        6        21       27

    `/ingest` drained the retry queue with `list_all()`, which returns a copy and
    removes nothing, so every request re-staged the entire backlog -- N(N+1)/2
    offline entries, every one of them a duplicate of the same haemoglobin
    result. `RetryQueue.dequeue()` existed and was called from nowhere. In a
    256 MB container (mem_limit in docker-compose.yml) that is an OOM path, and
    had the offline queue ever been drained to GULA it would have delivered one
    result twenty-one times.
    """
    import os

    from fastapi.testclient import TestClient

    main = _fresh_app(monkeypatch, backend_url="http://gula.invalid:9")
    client = TestClient(main.app)
    headers = {"x-api-key": os.environ["LABLINK_API_KEY"]}
    frame = _frame(_HEADER + "3R|1|^^^Hb|13.5|g/dL\r")

    observed = []
    for _ in range(6):
        response = _ingest_over_http(client, headers, frame)
        assert response.status_code == 200
        observed.append(
            (
                len(main.repository.db.results),
                len(main.repository.db.offline_queue),
            ),
        )

    assert observed == [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6)], (
        f"the backlog is multiplying again: {observed}"
    )
    # Six failed forwards, six records of failure, and nothing left pending.
    assert main.pipeline.retry_queue.size() == 0
    assert len(_rows(main.repository.db, "forward_failed")) == 6


def test_a_staging_failure_returns_the_item_to_the_queue(monkeypatch):
    """The second-order attack on the fix. Dequeuing before the hand-off opens a
    loss window the old code did not have: if staging raises, the only record
    that a result never reached GULA would be gone. It is put back."""
    import os

    from fastapi.testclient import TestClient

    main = _fresh_app(monkeypatch, backend_url="http://gula.invalid:9")

    def _explode(*args, **kwargs):
        raise RuntimeError("staging is down")

    monkeypatch.setattr(main.sync_engine, "stage", _explode)

    client = TestClient(main.app, raise_server_exceptions=False)
    headers = {"x-api-key": os.environ["LABLINK_API_KEY"]}
    response = _ingest_over_http(client, headers, _frame(_HEADER + "3R|1|^^^Hb|13.5|g/dL\r"))

    assert response.status_code == 500, "the failure must not be swallowed"
    assert main.pipeline.retry_queue.size() == 1, (
        "the retry item was dequeued and then lost when staging failed"
    )


def test_the_drain_uses_dequeue_and_not_list_all():
    source = _MAIN_SRC.read_text()
    assert "pipeline.retry_queue.dequeue()" in source
    assert "for item in pipeline.retry_queue.list_all():" not in source, (
        "the non-draining iteration is back"
    )


# ── measured delivery semantics, stated rather than claimed ─────────────────


def test_an_identical_frame_sent_twice_produces_two_results(monkeypatch):
    """Not a defect report -- a measurement, so the semantics are on the record.

    The bridge has no idempotency key. A device that retransmits a frame, or a
    client that retries POST /ingest, produces a second result. The delivery
    semantics of this ingestion path are therefore AT-LEAST-ONCE WITH
    DUPLICATION, not exactly-once, and nothing in the service claims otherwise.

    Deduplicating would mean choosing an identity for "the same result", and a
    content hash would collapse a genuinely repeated measurement -- the same
    analyte, the same value, the same device, measured twice -- into one. That is
    a clinical identity rule and is deliberately not invented here; it needs the
    ASTM message's own sequence/message-id carried through the pipeline, which
    the parser does not currently retain.
    """
    import os

    from fastapi.testclient import TestClient

    main = _fresh_app(monkeypatch, backend_url="http://gula.invalid:9")
    client = TestClient(main.app)
    headers = {"x-api-key": os.environ["LABLINK_API_KEY"]}
    frame = _frame(_HEADER + "3R|1|^^^Hb|13.5|g/dL\r")

    first = _ingest_over_http(client, headers, frame)
    second = _ingest_over_http(client, headers, frame)

    assert first.json()["processed"] == 1
    assert second.json()["processed"] == 1
    assert len(main.repository.db.results) == 2, (
        "if this is now 1, an idempotency rule was introduced -- check that it "
        "cannot collapse a genuinely repeated measurement"
    )


def test_the_parser_does_not_retain_a_message_identity_to_deduplicate_on():
    """The blocker behind the finding above, asserted so it is not guessed at.

    IA-050 added the fields the R record already carried, including its own
    `sequence`. That sharpens this assertion rather than weakening it: a record
    sequence is per-message and restarts at 1 in every message, so two
    retransmissions of the same message carry identical sequences and two
    different messages can too. It is not a message identity.

    What would be one -- an ASTM header message-control-id, or a session-level
    frame number -- is still not retained anywhere, so there remains nothing to
    deduplicate on. Exactly-once delivery stays unsupported, and claiming it
    would need both that identity and a durable store to remember it in
    (IA-040).
    """
    from app.pipeline.parser_engine import ASTMRecord

    fields = set(ASTMRecord.__dataclass_fields__)
    assert "message_id" not in fields
    assert "message_control_id" not in fields
    assert "frame_number" not in fields
    assert fields == {
        "type", "raw", "patient_id", "patient_name", "test_code", "value", "unit",
        "sequence", "reference_range", "abnormal_flags", "nature_of_abnormality",
        "result_status", "completed_at",
    }, "the retained field set changed; re-check whether a message identity now exists"

    # And the header record, which is where a message control id would live, is
    # parsed into nothing but its raw text.
    from app.pipeline.parser_engine import ASTMParser

    header = ASTMParser().parse_line("1H|\\^&|||Dev|||||P|1")
    assert header.type == "header"
    assert header.sequence is None
    assert header.test_code is None


# ── IA-046: no CI job runs any of this ──────────────────────────────────────


def test_no_workflow_covers_this_service_yet():
    """A ratchet on the gap, not on the fix.

    Nothing in .github/workflows/ runs this suite, lints it, or builds its image;
    the only gate it passes is the syntax-gate's `compile()` sweep over
    `services/`. The prepared job is in docs/CI_COVERAGE_GAP.md and is NOT
    applied, because CLAUDE.md puts `.github/workflows/` behind human approval.

    When someone applies it this test fails, which is the point: it says to come
    back, delete this test, and record in that document that the gap is closed.
    """
    workflows = _SERVICE.parents[1] / ".github" / "workflows"
    if not workflows.is_dir():
        pytest.skip("no workflow directory in this checkout")

    referencing = sorted(
        path.name
        for path in workflows.glob("*.yml")
        if "device_bridge" in path.read_text(errors="replace")
        or "device-bridge" in path.read_text(errors="replace")
    )
    assert referencing == [], (
        f"a workflow now references this service ({referencing}); if the prepared "
        "job was applied, update docs/CI_COVERAGE_GAP.md and remove this test"
    )


def test_the_prepared_patch_is_recorded():
    """The finding must not exist only in a commit message."""
    doc = _SERVICE / "docs" / "CI_COVERAGE_GAP.md"
    text = doc.read_text()
    assert "PREPARED, NOT APPLIED" in text
    assert "device-bridge:" in text, "the document must carry the actual job"
    assert "### Rollback" in text
    assert "pyserial" in text, "the one uncertain step must stay flagged"
