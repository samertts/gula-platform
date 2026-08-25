"""Fail-closed transport client for the isolated local device bridge.

The bridge is not a live clinical-result path. Forwarding is disabled unless a
separate deployment supplies HTTPS plus mutual-TLS material. This module never
falls back to HTTP or one-way TLS.
"""

from __future__ import annotations

import logging
import ssl
from typing import Any, cast
from urllib.parse import urlparse

import httpx
from app.pipeline.normalizer import NormalizedResult

logger = logging.getLogger("lablink.gula")


class DeviceBridgeTransportConfigurationError(ValueError):
    """Raised when a requested live bridge transport is not mutually authenticated."""


class GulaClient:
    """Forward device envelopes only through explicitly enabled mTLS transport."""

    def __init__(
        self,
        base_url: str | None,
        lab_id: str,
        timeout: float = 5.0,
        *,
        enabled: bool = False,
        ca_bundle_path: str | None = None,
        client_cert_path: str | None = None,
        client_key_path: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/") if base_url else None
        self.lab_id = lab_id
        self.timeout = timeout
        self.enabled = enabled
        self.ca_bundle_path = ca_bundle_path
        self.client_cert_path = client_cert_path
        self.client_key_path = client_key_path

        if enabled:
            self._validate_enabled_transport()

    def _validate_enabled_transport(self) -> None:
        if self.base_url is None:
            raise DeviceBridgeTransportConfigurationError(
                "enabled device bridge forwarding requires an HTTPS backend URL"
            )
        parsed = urlparse(self.base_url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise DeviceBridgeTransportConfigurationError(
                "enabled device bridge forwarding requires a valid HTTPS backend URL"
            )
        if not all((self.ca_bundle_path, self.client_cert_path, self.client_key_path)):
            raise DeviceBridgeTransportConfigurationError(
                "enabled device bridge forwarding requires CA, client certificate, and client key paths"
            )

    def _build_mtls_context(self) -> ssl.SSLContext:
        """Build a mutual-TLS context only after all explicit configuration checks."""
        self._validate_enabled_transport()
        assert self.ca_bundle_path is not None
        assert self.client_cert_path is not None
        assert self.client_key_path is not None

        context = ssl.create_default_context(cafile=self.ca_bundle_path)
        context.load_cert_chain(certfile=self.client_cert_path, keyfile=self.client_key_path)
        return context

    async def send_results(self, results: list[NormalizedResult]) -> dict[str, Any]:
        """Send only through mTLS; disabled or invalid transport never sends a request."""
        if not self.enabled:
            logger.info("device bridge forwarding rejected because it is disabled")
            return {"status": "failed", "error": "device_bridge_forwarding_disabled"}

        try:
            tls_context = self._build_mtls_context()
        except DeviceBridgeTransportConfigurationError:
            logger.error("device bridge forwarding rejected because mTLS is unavailable")
            return {"status": "failed", "error": "device_bridge_mtls_unavailable"}
        except OSError:
            logger.error("device bridge forwarding rejected because mTLS is unavailable")
            return {"status": "failed", "error": "device_bridge_mtls_unavailable"}
        except ssl.SSLError:
            logger.error("device bridge forwarding rejected because mTLS is unavailable")
            return {"status": "failed", "error": "device_bridge_mtls_unavailable"}

        if self.base_url is None:
            logger.error("device bridge forwarding rejected because backend URL is absent")
            return {"status": "failed", "error": "device_bridge_mtls_unavailable"}

        payload = {
            "lab_id": self.lab_id,
            "results": [
                {
                    "patient_id": result.patient_id,
                    "test_code": result.test_code,
                    "value": result.value,
                    "unit": result.unit,
                    "timestamp": result.timestamp.isoformat(),
                }
                for result in results
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=tls_context) as client:
                response = await client.post(f"{self.base_url}/device/results", json=payload)
                response.raise_for_status()
                return cast(dict[str, Any], response.json())
        except httpx.HTTPError:
            logger.warning("device bridge mTLS forwarding failed", extra={"lab_id": self.lab_id})
            return {"status": "failed", "error": "device_bridge_forwarding_failed"}
