"""Three unbounded growth paths in a container capped at 256 MB.

IA-052 (P1) — DISCOVERED, REPRODUCED, FIXED, VERIFIED.

All three are reachable from the authenticated `POST /ingest`, and the service
registers no middleware at all (`app.user_middleware == []`), so the monolith's
`MaxBodySizeMiddleware` has no counterpart here.

MEASURED BEFORE THE FIX:

    A: an incomplete frame (STX, never an ETX), fed to one device
          1 chunks -> pending_bytes =      8,193   log rows = 0
         10 chunks -> pending_bytes =     81,930   log rows = 0
         50 chunks -> pending_bytes =    409,650   log rows = 0
        100 chunks -> pending_bytes =    819,300   log rows = 0
        200 chunks -> pending_bytes =  1,638,600   log rows = 0

    B: one session per distinct device id
        after ids 0..999: sessions held = 1,000

    C: /ingest chunk max_length: absent
       caps anywhere:            none

Linear, forever, and silent — zero log rows across 1.6 MB of retained bytes.
The IA-039 fix deliberately records nothing for a partial frame, which is right
for a frame still arriving and is exactly what made this invisible.

WHY THESE BOUNDS AND NOT OTHERS: an ASTM E1381 frame is at most 247 bytes
including its overhead, and a long message is sent as several frames rather than
one enormous one. A "partial frame" that has grown past tens of kilobytes is
therefore not a partial frame; it is a stream that will never produce one — a
truncated serial read, a malfunctioning instrument, or an authenticated client
that never sends an ETX. 64 KiB is two orders of magnitude above the protocol's
own frame size. 256 sessions sits far above the instrument count of one lab,
which is what one bridge serves. Both, and the chunk length, are overridable.

AFTER THE FIX, same probe:

    A:   1 chunks -> pending_bytes =  8,193   log rows = 0
        10 chunks -> pending_bytes = 16,386   log rows = 2
       100 chunks -> pending_bytes = 32,772   log rows = 24
       200 chunks -> pending_bytes =      0   log rows = 50
    B: after ids 0..999: sessions held = 256
    C: chunk max_length present

The discard is recorded, never silent: IA-039's invariant is that a loss leaves
a record, and this is the one place the service deliberately throws bytes away.
"""
from __future__ import annotations

import asyncio
import importlib
import os

import pytest
from app.integration.gula_client import GulaClient
from app.pipeline import data_pipeline as pipeline_module
from app.pipeline.data_pipeline import _MAX_PENDING_BYTES, _MAX_SESSIONS, DataPipeline
from app.pipeline.normalizer import Normalizer
from app.pipeline.parser_engine import ASTMParser, calculate_checksum
from app.storage.db import InMemoryDB
from app.storage.result_repository import LogRepository, ResultRepository

_HEADER = "1H|\\^&|||Dev|||||P|1\r2P|1||PATIENT-A||Alpha^A\r"


class _FakeGula(GulaClient):
    def __init__(self) -> None:
        super().__init__(base_url="http://example.invalid", lab_id="LAB001")

    async def send_results(self, results):  # type: ignore[override]
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


def _feed(pipeline, chunk: bytes, device_id: str = "DEV-1"):
    return asyncio.run(
        pipeline.process_chunk(device_id=device_id, fallback_patient_id="FB", chunk=chunk),
    )


def _rows(db: InMemoryDB, status: str) -> list[dict]:
    return [row for row in db.logs if row["status"] == status]


# ── A: the frame buffer ─────────────────────────────────────────────────────


def test_an_endless_partial_frame_does_not_grow_without_bound():
    pipeline, db = _pipeline()
    chunk = b"\x02" + b"X" * 8192
    high_water = 0

    for _ in range(200):
        _feed(pipeline, chunk)
        high_water = max(high_water, pipeline.sessions["DEV-1"].buffer.pending_bytes)

    # The check runs at the start of a call, so the buffer may hold up to the
    # limit plus one chunk before the next call clears it.
    assert high_water <= _MAX_PENDING_BYTES + len(chunk), (
        f"retained {high_water:,} bytes against a limit of {_MAX_PENDING_BYTES:,}"
    )
    assert high_water < 1_638_600, "the pre-fix growth curve is back"


def test_every_discard_leaves_a_record():
    pipeline, db = _pipeline()
    chunk = b"\x02" + b"X" * 8192
    for _ in range(40):
        _feed(pipeline, chunk)

    rejected = _rows(db, "rejected")
    assert rejected, "bytes were discarded with no record -- IA-039's invariant"
    assert all(
        row["error_message"].startswith("partial_frame_too_large") for row in rejected
    )
    assert "the buffer was cleared" in rejected[0]["error_message"]
    assert "limit" in rejected[0]["error_message"], (
        "the record must say what limit was hit, or an operator cannot act on it"
    )


def test_a_legitimate_partial_frame_is_still_buffered_and_completes():
    """The control that matters most: ASTM is streamed, so the cap must not
    break a frame that simply has not finished arriving."""
    pipeline, db = _pipeline()
    payload = (_HEADER + "3R|1|^^^Hb|13.5|g/dL\r").encode("ascii")

    results = _feed(pipeline, b"\x02" + payload)
    assert results == []
    assert _rows(db, "rejected") == [], "a normal partial frame was called a loss"
    assert pipeline.sessions["DEV-1"].buffer.pending_bytes > 0

    rest = b"\x03" + calculate_checksum(payload).encode("ascii") + b"\r\n"
    results = _feed(pipeline, rest)
    assert [r.test_code for r in results] == ["HEMOGLOBIN"]
    assert _rows(db, "rejected") == []


def test_the_discard_does_not_destroy_results_already_parsed():
    """A chunk that both completes a frame and leaves an over-long remainder
    must keep the result."""
    pipeline, db = _pipeline()
    # First: push the buffer over the limit with junk that has no STX... which
    # extract_frames clears. So use an STX-led remainder instead.
    _feed(pipeline, b"\x02" + b"X" * (_MAX_PENDING_BYTES + 1))
    good = _frame(_HEADER + "3R|1|^^^Hb|13.5|g/dL\r")
    results = _feed(pipeline, good)

    assert [r.test_code for r in results] == ["HEMOGLOBIN"], (
        "the over-long discard took a usable result with it"
    )
    assert len(db.results) == 1
    assert _rows(db, "rejected"), "the discard itself must still be recorded"


# ── B: the session table ───────────────────────────────────────────────────


def test_the_session_table_is_bounded():
    pipeline, _ = _pipeline()
    for index in range(_MAX_SESSIONS * 4):
        _feed(pipeline, b"\x02ABC", device_id=f"DEV-{index}")
    assert len(pipeline.sessions) == _MAX_SESSIONS


def test_eviction_is_least_recently_used():
    pipeline, _ = _pipeline()
    _feed(pipeline, b"\x02ABC", device_id="OLDEST")
    for index in range(_MAX_SESSIONS - 1):
        _feed(pipeline, b"\x02ABC", device_id=f"DEV-{index}")

    # Touch OLDEST so it is no longer the least recently used.
    _feed(pipeline, b"\x02ABC", device_id="OLDEST")
    _feed(pipeline, b"\x02ABC", device_id="NEWCOMER")

    assert "OLDEST" in pipeline.sessions, "a recently used session was evicted"
    assert "NEWCOMER" in pipeline.sessions
    assert "DEV-0" not in pipeline.sessions, "the oldest untouched session survived"
    assert len(pipeline.sessions) == _MAX_SESSIONS


def test_a_devices_own_stream_is_unaffected_by_other_devices_arriving():
    """Eviction must not corrupt an active device's partial frame."""
    pipeline, db = _pipeline()
    payload = (_HEADER + "3R|1|^^^Hb|13.5|g/dL\r").encode("ascii")
    _feed(pipeline, b"\x02" + payload, device_id="ACTIVE")

    for index in range(_MAX_SESSIONS - 1):
        _feed(pipeline, b"\x02ABC", device_id=f"NOISE-{index}")

    rest = b"\x03" + calculate_checksum(payload).encode("ascii") + b"\r\n"
    results = _feed(pipeline, rest, device_id="ACTIVE")
    assert [r.test_code for r in results] == ["HEMOGLOBIN"], (
        "the active device's buffered frame was lost to session churn"
    )


# ── C: the request body ────────────────────────────────────────────────────


def test_an_over_long_chunk_is_refused_at_the_api_boundary(monkeypatch):
    import app.main as main
    from fastapi.testclient import TestClient

    client = TestClient(main.app)
    headers = {"x-api-key": os.environ["LABLINK_API_KEY"]}
    oversized = "X" * (main._MAX_CHUNK_CHARS + 1)

    response = client.post(
        "/ingest",
        json={"patient_id": "FB", "device_id": "DEV-1", "chunk": oversized},
        headers=headers,
    )
    assert response.status_code == 422, (
        "an unbounded chunk is accepted again; there is no body-size middleware "
        "on this service to catch it"
    )


def test_a_normal_chunk_is_still_accepted():
    """Positive control: the cap must be far above any real payload."""
    import app.main as main
    from fastapi.testclient import TestClient

    assert main._MAX_CHUNK_CHARS >= 1024 * 1024, (
        "the chunk cap is now below a megabyte; an ASTM frame is 247 bytes, so "
        "this should admit thousands of them"
    )
    client = TestClient(main.app)
    response = client.post(
        "/ingest",
        json={
            "patient_id": "FB",
            "device_id": "DEV-OK",
            "chunk": _frame(_HEADER + "3R|1|^^^Hb|13.5|g/dL\r").decode("latin-1"),
        },
        headers={"x-api-key": os.environ["LABLINK_API_KEY"]},
    )
    assert response.status_code == 200
    assert response.json()["processed"] == 1


# ── the bounds are operator-overridable, and sane when set absurdly ────────


@pytest.mark.parametrize(
    ("variable", "attribute"),
    [
        ("LABLINK_MAX_PENDING_BYTES", "_MAX_PENDING_BYTES"),
        ("LABLINK_MAX_SESSIONS", "_MAX_SESSIONS"),
    ],
)
def test_each_bound_reads_its_environment_variable(variable, attribute, monkeypatch):
    monkeypatch.setenv(variable, "7")
    reloaded = importlib.reload(pipeline_module)
    try:
        assert getattr(reloaded, attribute) == 7
    finally:
        monkeypatch.delenv(variable, raising=False)
        importlib.reload(pipeline_module)


@pytest.mark.parametrize("value", ["0", "-1"])
def test_a_nonsensical_bound_cannot_disable_the_limit(value, monkeypatch):
    """`max(1, ...)`: a zero or negative limit would mean "discard everything"
    or an infinite eviction loop, so it floors at one rather than trusting the
    environment."""
    monkeypatch.setenv("LABLINK_MAX_SESSIONS", value)
    monkeypatch.setenv("LABLINK_MAX_PENDING_BYTES", value)
    reloaded = importlib.reload(pipeline_module)
    try:
        assert reloaded._MAX_SESSIONS == 1
        assert reloaded._MAX_PENDING_BYTES == 1
    finally:
        monkeypatch.delenv("LABLINK_MAX_SESSIONS", raising=False)
        monkeypatch.delenv("LABLINK_MAX_PENDING_BYTES", raising=False)
        importlib.reload(pipeline_module)


def test_the_defaults_are_the_documented_ones():
    assert _MAX_PENDING_BYTES == 65536
    assert _MAX_SESSIONS == 256


def test_this_service_registers_no_body_size_middleware():
    """Recorded because it is why the chunk bound has to live on the field: the
    monolith's MaxBodySizeMiddleware has no counterpart here."""
    import app.main as main

    assert [m.cls.__name__ for m in main.app.user_middleware] == [], (
        "middleware was added; if it bounds the body, the field cap may be "
        "redundant -- check before removing either"
    )


def test_one_loss_produces_exactly_one_record():
    """Found while writing this suite: the discard empties the buffer, so the
    IA-039 `unframed_chunk` branch fired on the same chunk and the one loss was
    reported twice -- once truthfully and once with the wrong reason. An
    operator counting rejections would have counted double."""
    pipeline, db = _pipeline()
    for _ in range(30):
        _feed(pipeline, b"\x02" + b"X" * 8192)

    reasons = [row["error_message"].split(":")[0] for row in _rows(db, "rejected")]
    assert set(reasons) == {"partial_frame_too_large"}, (
        f"a single loss is being reported under more than one reason: {set(reasons)}"
    )


def test_an_unframed_chunk_is_still_reported_as_unframed():
    """The control for the fix above: suppressing the duplicate must not
    suppress the genuine case. A chunk with no STX at all is still a loss, and
    still says so."""
    pipeline, db = _pipeline()
    _feed(pipeline, b"MSH|^~\\&|LIS|LAB|||20260101||ORU^R01|1|P|2.5\r")
    rejected = _rows(db, "rejected")
    assert len(rejected) == 1
    assert rejected[0]["error_message"].startswith("unframed_chunk")


# ── IA-053: a missing key made every endpoint 500 instead of refusing to start ─


def test_a_missing_api_key_prevents_startup_rather_than_500ing_each_request():
    """IA-053 (P2) — DISCOVERED, REPRODUCED, FIXED, VERIFIED.

    Measured before the fix, with LABLINK_API_KEY unset against a real uvicorn
    process:

        GET /health   -> 200
        GET /devices  -> 500, with `SystemExit: 1` from verify_api_key in the log

    `verify_api_key` called sys.exit(1) per request. The SystemExit is raised
    inside the request, where the ASGI stack turns it into a 500: the process
    survives, every authenticated endpoint 500s, and the healthcheck keeps
    passing — so the container looks healthy and does nothing. It fails closed,
    so it was never an authorization hole; it was undiagnosable.

    And that is the *default* for a documented deployment: docker-compose.yml
    passes `LABLINK_API_KEY: "${LABLINK_API_KEY:-}"`, so
    `docker compose --profile device-bridge up device-bridge` with nothing set
    produces exactly this. The key is also absent from .env.example.

    A missing credential is a configuration error, not a request error, and is
    now detected at import — where the monolith detects its own (config.py
    hard-fails on missing secrets).
    """
    import os
    import subprocess
    import sys

    service_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = {k: v for k, v in os.environ.items() if k not in {"LABLINK_API_KEY", "PYTHONPATH"}}
    completed = subprocess.run(
        [sys.executable, "-c", "import sys; sys.path.insert(0,'.'); import app.main"],
        cwd=service_dir,
        env=env,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0, (
        "the app imported with no API key configured; it will start, pass its "
        "healthcheck, and answer 500 on every authenticated request"
    )
    assert "LABLINK_API_KEY is not set" in completed.stderr
    assert "MissingApiKeyError" in completed.stderr


def test_the_startup_check_names_what_to_do():
    from app.security.auth import MissingApiKeyError, require_configured_api_key

    import os

    previous = os.environ.pop("LABLINK_API_KEY", None)
    try:
        with pytest.raises(MissingApiKeyError) as excinfo:
            require_configured_api_key()
        message = str(excinfo.value)
        assert "LABLINK_API_KEY" in message
        assert "docker-compose" in message, "the operator is not told where it comes from"
    finally:
        if previous is not None:
            os.environ["LABLINK_API_KEY"] = previous


def test_a_whitespace_only_key_is_treated_as_absent():
    import os

    from app.security.auth import MissingApiKeyError, require_configured_api_key

    previous = os.environ.get("LABLINK_API_KEY")
    try:
        os.environ["LABLINK_API_KEY"] = "   "
        with pytest.raises(MissingApiKeyError):
            require_configured_api_key()
    finally:
        if previous is None:
            os.environ.pop("LABLINK_API_KEY", None)
        else:
            os.environ["LABLINK_API_KEY"] = previous


def test_no_request_path_can_terminate_the_interpreter():
    """The root-cause ratchet: sys.exit in a request handler is the pattern, not
    just this one call."""
    import ast
    import pathlib

    # By AST, not by text: this file's own first draft matched the sentence in
    # auth.py's docstring that *describes* the removed sys.exit, which is the
    # same shape as a ratchet passing on a commented-out line.
    service = pathlib.Path(__file__).resolve().parents[1]
    offenders = []
    for path in (service / "app").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            is_sys_exit = (
                isinstance(func, ast.Attribute)
                and func.attr == "exit"
                and isinstance(func.value, ast.Name)
                and func.value.id == "sys"
            )
            if is_sys_exit:
                offenders.append(f"{path.relative_to(service).as_posix()}:{node.lineno}")
    assert offenders == [], (
        f"sys.exit in served code: {offenders}. Inside a request the ASGI stack "
        "turns SystemExit into a 500, which is a configuration error disguised "
        "as a server fault."
    )


def test_a_valid_key_still_authenticates():
    """Positive control."""
    import os

    from app.security.auth import verify_api_key

    assert verify_api_key(os.environ["LABLINK_API_KEY"]) == os.environ["LABLINK_API_KEY"]
    with pytest.raises(Exception):
        verify_api_key("wrong")
    with pytest.raises(Exception):
        verify_api_key(None)
