from __future__ import annotations

import json
import logging
import time
from urllib.parse import urljoin

import httpx

from backend.app.integration.gateway.base import (
    GatewayConfig,
    GatewayMessage,
    GatewayResult,
    MessageGateway,
)
from backend.app.integration.gateway.registry import GatewayRegistry

logger = logging.getLogger("gula.integration.gateway.dicom")


class DICOMGateway(MessageGateway):
    SUPPORTED_STUDY_LEVELS = {"patient", "study", "series", "instance"}

    def __init__(self, name: str = "dicom", config: GatewayConfig | None = None):
        super().__init__(name, config)
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> bool:
        try:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                headers={"Content-Type": "application/dicom+json", **self.config.headers},
            )
            self._connected = True
            logger.info("DICOM gateway connected: %s", self.config.endpoint)
            return True
        except Exception as exc:
            logger.error("DICOM gateway connection failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        return True

    async def send(self, message: GatewayMessage) -> GatewayResult:
        if not self._client:
            return GatewayResult(success=False, error="Not connected")
        start = time.monotonic()
        try:
            resp = await self._client.post(
                urljoin(self.config.endpoint, "studies"),
                content=message.payload
                if isinstance(message.payload, bytes)
                else json.dumps(message.payload),
            )
            lat = (time.monotonic() - start) * 1000
            return GatewayResult(
                success=resp.is_success,
                status_code=resp.status_code,
                data={"study_uid": resp.headers.get("Location", "")} if resp.is_success else None,
                latency_ms=lat,
            )
        except Exception as exc:
            lat = (time.monotonic() - start) * 1000
            return GatewayResult(success=False, error=str(exc), latency_ms=lat)

    async def receive(self) -> GatewayMessage | None:
        return None

    async def transform(self, message: GatewayMessage) -> GatewayMessage:
        return message

    async def store_instance(self, dicom_data: bytes) -> GatewayResult:
        return await self.send(GatewayMessage(payload=dicom_data, content_type="application/dicom"))

    async def query_studies(self, params: dict[str, str]) -> GatewayResult:
        if not self._client:
            return GatewayResult(success=False, error="Not connected")
        start = time.monotonic()
        try:
            resp = await self._client.get(
                urljoin(self.config.endpoint, "studies"),
                params=params,
            )
            lat = (time.monotonic() - start) * 1000
            return GatewayResult(
                success=resp.is_success,
                status_code=resp.status_code,
                data=resp.json() if resp.is_success else None,
                latency_ms=lat,
            )
        except Exception as exc:
            return GatewayResult(success=False, error=str(exc))

    async def retrieve_study(self, study_uid: str) -> GatewayResult:
        if not self._client:
            return GatewayResult(success=False, error="Not connected")
        start = time.monotonic()
        try:
            resp = await self._client.get(
                urljoin(self.config.endpoint, f"studies/{study_uid}"),
            )
            lat = (time.monotonic() - start) * 1000
            return GatewayResult(
                success=resp.is_success,
                status_code=resp.status_code,
                data=resp.content if resp.is_success else None,
                latency_ms=lat,
            )
        except Exception as exc:
            return GatewayResult(success=False, error=str(exc))

    async def delete_study(self, study_uid: str) -> GatewayResult:
        if not self._client:
            return GatewayResult(success=False, error="Not connected")
        start = time.monotonic()
        try:
            resp = await self._client.delete(
                urljoin(self.config.endpoint, f"studies/{study_uid}"),
            )
            return GatewayResult(
                success=resp.is_success,
                status_code=resp.status_code,
                latency_ms=(time.monotonic() - start) * 1000,
            )
        except Exception as exc:
            return GatewayResult(success=False, error=str(exc))


GatewayRegistry.register(DICOMGateway())
