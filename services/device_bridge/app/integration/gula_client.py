from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from app.pipeline.normalizer import NormalizedResult

logger = logging.getLogger("lablink.gula")

# The real backend endpoint (backend/app/routes/device_results.py) requires a
# JWT bearer token (Depends(get_current_user)) — device_bridge has no
# machine/device identity of its own yet to obtain one. Until that identity
# surface exists (backend/app/identity/repositories/device_repository.py is
# actively being built for this), an operator can provision a long-lived
# token out of band via this env var. Unset = requests will 401, which is
# reported as a normal failed-send (queued for retry) rather than papered
# over with a fake credential.
GULA_DEVICE_TOKEN_ENV = "GULA_DEVICE_BEARER_TOKEN"


class GulaClient:
    def __init__(
        self,
        base_url: str,
        lab_id: str,
        timeout: float = 5.0,
        auth_token: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.lab_id = lab_id
        self.timeout = timeout
        self.auth_token = auth_token if auth_token is not None else os.getenv(GULA_DEVICE_TOKEN_ENV)

    async def send_results(self, results: list[NormalizedResult]) -> dict[str, Any]:
        """POST to backend/app/routes/device_results.py's actual contract.

        That endpoint matches results to an order by sample barcode
        (``DeviceSubmission.barcode``) scoped to the caller's own lab_id —
        it does not read lab_id from the body at all, so results without a
        barcode can never be matched and are not sent.
        """
        if not results:
            return {"status": "failed", "error": "no results to send"}

        barcode = results[0].barcode
        if not barcode:
            logger.warning(
                "Cannot send results without a sample barcode",
                extra={"lab_id": self.lab_id, "device_id": results[0].device_id},
            )
            return {"status": "failed", "error": "missing_barcode"}

        payload = {
            "barcode": barcode,
            "device_id": results[0].device_id,
            "results": [
                {
                    "test_name": r.test_name,
                    "value": r.value,
                    "unit": r.unit,
                }
                for r in results
            ],
        }
        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/device/results", json=payload, headers=headers
                )
                response.raise_for_status()
                return response.json()
        except Exception as exc:
            logger.warning("GULA send failed", extra={"error": str(exc), "lab_id": self.lab_id})
            return {"status": "failed", "error": str(exc)}
