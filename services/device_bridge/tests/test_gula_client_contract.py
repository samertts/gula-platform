"""GulaClient must send the payload backend/app/routes/device_results.py
actually expects.

Before this fix, GulaClient posted {"lab_id", "results": [{"patient_id",
"test_code", "value", "unit", "timestamp"}]} with no auth header at all.
The real endpoint (DeviceSubmission) requires {"barcode", "device_id",
"results": [{"test_name", "value", "unit", ...}]} plus a bearer token
(Depends(get_current_user)) — every real submission would have 422'd on
the missing "barcode" field alone, before auth was even checked. This
test locks in the corrected shape without importing the full backend
app (which pulls in the DB/config stack) — see the docstring in
gula_client.py for the exact source reference.
"""
from __future__ import annotations

import asyncio
from datetime import datetime

from app.integration.gula_client import GulaClient
from app.pipeline.normalizer import NormalizedResult


class _FakeResponse:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return {"status": "ok"}


class _RecordingAsyncClient:
    """Stand-in for httpx.AsyncClient that records the outgoing request."""

    last_call: dict = {}

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None, headers=None):
        _RecordingAsyncClient.last_call = {"url": url, "json": json, "headers": headers}
        return _FakeResponse()


def _result(**overrides) -> NormalizedResult:
    defaults = dict(
        patient_id="12345",
        device_id="CBC-01",
        test_code="HGB",
        test_name="Hemoglobin",
        value=13.5,
        unit="g/dL",
        reference_range="",
        timestamp=datetime.now(),
        status="final",
        barcode="BC-9",
    )
    defaults.update(overrides)
    return NormalizedResult(**defaults)


def test_send_results_matches_device_results_contract(monkeypatch) -> None:
    monkeypatch.setattr("app.integration.gula_client.httpx.AsyncClient", _RecordingAsyncClient)

    client = GulaClient(base_url="http://gula.local", lab_id="LAB001", auth_token="tok-123")
    response = asyncio.run(client.send_results([_result()]))

    assert response == {"status": "ok"}
    call = _RecordingAsyncClient.last_call
    assert call["url"] == "http://gula.local/device/results"
    assert call["json"] == {
        "barcode": "BC-9",
        "device_id": "CBC-01",
        "results": [{"test_name": "Hemoglobin", "value": 13.5, "unit": "g/dL"}],
    }
    assert call["headers"] == {"Authorization": "Bearer tok-123"}


def test_send_results_without_barcode_fails_fast_without_a_network_call(monkeypatch) -> None:
    monkeypatch.setattr("app.integration.gula_client.httpx.AsyncClient", _RecordingAsyncClient)
    _RecordingAsyncClient.last_call = {}

    client = GulaClient(base_url="http://gula.local", lab_id="LAB001")
    response = asyncio.run(client.send_results([_result(barcode=None)]))

    assert response["status"] == "failed"
    assert response["error"] == "missing_barcode"
    assert _RecordingAsyncClient.last_call == {}  # no request was attempted


def test_send_results_without_token_omits_auth_header(monkeypatch) -> None:
    monkeypatch.delenv("GULA_DEVICE_BEARER_TOKEN", raising=False)
    monkeypatch.setattr("app.integration.gula_client.httpx.AsyncClient", _RecordingAsyncClient)

    client = GulaClient(base_url="http://gula.local", lab_id="LAB001")
    asyncio.run(client.send_results([_result()]))

    assert _RecordingAsyncClient.last_call["headers"] == {}
