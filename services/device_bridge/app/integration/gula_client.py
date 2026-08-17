from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from app.pipeline.normalizer import NormalizedResult

logger = logging.getLogger("lablink.gula")


class GulaClient:
    def __init__(
        self,
        base_url: str,
        lab_id: str,
        timeout: float = 5.0,
        access_token: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        # lab_id remains local diagnostic metadata; tenant authorization comes
        # from the server-validated token and is never trusted from the payload.
        self.lab_id = lab_id
        self.timeout = timeout
        self.access_token = access_token or os.getenv("GULA_ACCESS_TOKEN", "")
        self.transport = transport

    async def send_results(
        self,
        results: list[NormalizedResult],
        *,
        barcode: str | None = None,
    ) -> dict[str, Any]:
        if not barcode:
            return {"status": "failed", "error": "barcode_required"}
        if not results:
            return {"status": "failed", "error": "results_required"}

        payload = {
            "barcode": barcode,
            "device_id": results[0].device_id,
            "results": [
                {
                    "test_name": r.test_code,
                    "value": r.value,
                    "unit": r.unit,
                }
                for r in results
            ],
        }
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout, transport=self.transport) as client:
                response = await client.post(
                    f"{self.base_url}/device/results",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.warning("GULA send failed", extra={"error": str(exc), "lab_id": self.lab_id})
            return {"status": "failed", "error": str(exc)}
