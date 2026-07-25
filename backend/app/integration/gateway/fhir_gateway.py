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
from backend.app.national.fhir import FHIRBundle, FHIRBundleEntry, FHIRValidationEngine

logger = logging.getLogger("gula.integration.gateway.fhir")


class FHIRGateway(MessageGateway):
    def __init__(
        self,
        name: str = "fhir",
        config: GatewayConfig | None = None,
        fhir_version: str = "R4",
    ):
        super().__init__(name, config)
        self.fhir_version = fhir_version
        self._client: httpx.AsyncClient | None = None
        self._validator = FHIRValidationEngine()

    async def connect(self) -> bool:
        try:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                headers={
                    "Content-Type": f"application/fhir+json; fhirVersion={self.fhir_version}",
                    "Accept": f"application/fhir+json; fhirVersion={self.fhir_version}",
                    **self.config.headers,
                },
            )
            self._connected = True
            logger.info("FHIR gateway connected: %s", self.config.endpoint)
            return True
        except Exception as exc:
            logger.error("FHIR gateway connection failed: %s", exc)
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
            resource = (
                message.payload
                if isinstance(message.payload, dict)
                else json.loads(message.payload)
            )
            validation = self._validator.validate(resource)
            if not validation.valid:
                return GatewayResult(
                    success=False,
                    error=f"FHIR validation failed: {'; '.join(validation.errors)}",
                    latency_ms=(time.monotonic() - start) * 1000,
                )
            resp = await self._client.post(
                urljoin(self.config.endpoint, resource.get("resourceType", "")),
                json=resource,
            )
            lat = (time.monotonic() - start) * 1000
            return GatewayResult(
                success=resp.is_success,
                status_code=resp.status_code,
                data=resp.json() if resp.is_success else None,
                latency_ms=lat,
            )
        except Exception as exc:
            lat = (time.monotonic() - start) * 1000
            logger.error("FHIR send failed: %s", exc)
            return GatewayResult(success=False, error=str(exc), latency_ms=lat)

    async def receive(self) -> GatewayMessage | None:
        return None

    async def transform(self, message: GatewayMessage) -> GatewayMessage:
        return message

    async def search(self, resource_type: str, params: dict[str, str]) -> GatewayResult:
        if not self._client:
            return GatewayResult(success=False, error="Not connected")
        start = time.monotonic()
        try:
            resp = await self._client.get(
                urljoin(self.config.endpoint, resource_type),
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

    async def read(self, resource_type: str, resource_id: str) -> GatewayResult:
        return await self.search(resource_type, {"_id": resource_id})

    async def create_bundle(self, entries: list[dict]) -> GatewayResult:
        bundle = FHIRBundle(
            type="collection",
            entry=[FHIRBundleEntry(resource=e) for e in entries],
        )
        return await self.send(GatewayMessage(payload=bundle.to_dict()))


GatewayRegistry.register(FHIRGateway())
