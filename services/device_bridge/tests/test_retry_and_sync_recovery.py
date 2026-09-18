"""Regression tests for the failed-delivery retry/recovery path.

Three bugs lived here before this pass:

1. retry_queue.enqueue() stored only ``[test_code, ...]`` strings, so even
   if something replayed the queue there was no patient_id/value/unit/
   timestamp left to actually resend.
2. main.py read `retry_queue.list_all()` (never removes anything) on every
   /ingest call, so a single persistent failure got re-staged into
   sync_engine again on every subsequent request — for every device_id,
   forever.
3. /edge/sync's sender just moved the item into `edge_buffer` and always
   reported success without ever calling GULA — a "retry" that silently
   dropped the data instead of resending it.
"""
from __future__ import annotations

from datetime import datetime

import app.main as main
from app.core.retry_queue import RetryQueue, content_key
from app.edge.sync_engine import SyncEngine
from app.pipeline.normalizer import NormalizedResult
from app.pipeline.parser_engine import calculate_checksum
from fastapi.testclient import TestClient


def _astm_chunk(hb_value: str) -> str:
    """Build a real (STX/ETX/checksum-framed) ASTM chunk, same shape as
    test_pipeline_astm.py's build_frame(), as a latin-1-safe str so it can
    travel through the JSON /ingest payload the same way the real HTTP
    route encodes it (payload.chunk.encode("latin-1"))."""
    payload = (
        f"1H|\\^&|||Device|||||P|1\r2P|1||12345||Doe^John\r3R|1|^^^Hb|{hb_value}|g/dL\r"
    ).encode("ascii")
    checksum = calculate_checksum(payload).encode("ascii")
    frame = b"\x02" + payload + b"\x03" + checksum + b"\r\n"
    return frame.decode("latin-1")


class AlwaysFailsGulaClient:
    def __init__(self) -> None:
        self.calls = 0

    async def send_results(self, results):
        self.calls += 1
        return {"status": "failed", "error": "simulated network failure"}


class RecoversOnSecondTryGulaClient:
    def __init__(self) -> None:
        self.attempts = []

    async def send_results(self, results):
        self.attempts.append(list(results))
        return {"status": "ok"}


def test_retry_queue_enqueue_keeps_full_result_data() -> None:
    normalized = NormalizedResult(
        patient_id="P-1",
        device_id="CBC-01",
        test_code="HGB",
        test_name="Hemoglobin",
        value=13.5,
        unit="g/dL",
        reference_range="",
        timestamp=datetime.now(),
        status="final",
        barcode="BC-1",
    )
    queue = RetryQueue()
    queue.enqueue(
        {
            "device_id": "CBC-01",
            "idempotency_key": content_key("CBC-01", [normalized]),
            "results": [
                {
                    "patient_id": normalized.patient_id,
                    "value": normalized.value,
                    "unit": normalized.unit,
                }
            ],
            "reason": "send_failed",
        }
    )
    item = queue.dequeue()
    assert item["results"][0]["patient_id"] == "P-1"
    assert item["results"][0]["value"] == 13.5
    assert item["idempotency_key"]


def test_retry_queue_drain_empties_and_returns_once() -> None:
    queue = RetryQueue()
    queue.enqueue({"device_id": "A"})
    queue.enqueue({"device_id": "B"})

    first = queue.drain()
    assert len(first) == 2
    assert queue.size() == 0

    # A second drain must not re-return already-drained items.
    second = queue.drain()
    assert second == []


def test_ingest_failure_is_staged_exactly_once_per_batch(api_key_headers, monkeypatch) -> None:
    """Two failing /ingest calls for the same device must not cause the
    first failure to be re-staged again on the second request."""
    fake = AlwaysFailsGulaClient()
    monkeypatch.setattr(main.pipeline, "gula_client", fake)
    monkeypatch.setattr(main, "sync_engine", SyncEngine())

    client = TestClient(main.app)
    body = {
        "patient_id": "P-9",
        "device_id": "RETRY-DEV",
        "chunk": _astm_chunk("13.5"),
        "barcode": "BC-9",
    }

    resp1 = client.post("/ingest", json=body, headers=api_key_headers)
    assert resp1.status_code == 200
    assert main.sync_engine.pending() == 1  # exactly one failure staged

    resp2 = client.post(
        "/ingest",
        json={**body, "chunk": _astm_chunk("14.0")},
        headers=api_key_headers,
    )
    assert resp2.status_code == 200
    # A second, distinct failure adds one more entry — not a re-staging of
    # the first one on top of itself.
    assert main.sync_engine.pending() == 2


def test_edge_sync_actually_resends_to_gula_and_clears_on_success(
    api_key_headers, monkeypatch
) -> None:
    failing = AlwaysFailsGulaClient()
    monkeypatch.setattr(main.pipeline, "gula_client", failing)
    monkeypatch.setattr(main, "sync_engine", SyncEngine())

    client = TestClient(main.app)
    client.post(
        "/ingest",
        json={
            "patient_id": "P-77",
            "device_id": "RECOVER-DEV",
            "chunk": _astm_chunk("11.1"),
            "barcode": "BC-77",
        },
        headers=api_key_headers,
    )
    assert main.sync_engine.pending() >= 1

    recovering = RecoversOnSecondTryGulaClient()
    monkeypatch.setattr(main.pipeline, "gula_client", recovering)

    resp = client.post("/edge/sync", headers=api_key_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["sent"] >= 1
    assert body["remaining"] == 0
    # The resend must have actually gone through send_results with real
    # NormalizedResult objects reconstructed from the queued payload, not
    # just been dropped into an unrelated buffer.
    assert len(recovering.attempts) >= 1
    resent_result = recovering.attempts[0][0]
    assert resent_result.patient_id == "12345"  # from the ASTM P record
    assert resent_result.value == 11.1
