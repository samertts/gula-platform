from datetime import datetime, timezone
import json

import httpx
import pytest

from app.integration.gula_client import GulaClient
from app.pipeline.normalizer import NormalizedResult


def _result() -> NormalizedResult:
    return NormalizedResult(
        patient_id="PATIENT-001",
        device_id="CBC-01",
        test_code="HEMOGLOBIN",
        test_name="Hemoglobin",
        value=13.5,
        unit="g/dL",
        reference_range="12-17",
        timestamp=datetime.now(timezone.utc),
        status="final",
    )


@pytest.mark.asyncio
async def test_gula_client_matches_device_results_contract() -> None:
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["json"] = json.loads(request.content)
        return httpx.Response(200, json={"status": "accepted", "result_count": 1})

    client = GulaClient(
        base_url="https://gula.test",
        lab_id="LAB-001",
        access_token="synthetic-access-token",
        transport=httpx.MockTransport(handler),
    )

    response = await client.send_results([_result()], barcode="SAMPLE-001")

    assert response == {"status": "accepted", "result_count": 1}
    assert captured["method"] == "POST"
    assert captured["url"] == "https://gula.test/device/results"
    assert captured["headers"]["authorization"] == "Bearer synthetic-access-token"
    assert captured["json"] == {
        "barcode": "SAMPLE-001",
        "device_id": "CBC-01",
        "results": [{"test_name": "HEMOGLOBIN", "value": 13.5, "unit": "g/dL"}],
    }


@pytest.mark.asyncio
async def test_gula_client_rejects_missing_barcode_without_network_call() -> None:
    called = False

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(500)

    client = GulaClient(
        base_url="https://gula.test",
        lab_id="LAB-001",
        transport=httpx.MockTransport(handler),
    )

    response = await client.send_results([_result()])

    assert response == {"status": "failed", "error": "barcode_required"}
    assert called is False
