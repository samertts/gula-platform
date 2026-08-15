from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.integration.gateway.base import (
    GatewayConfig,
    GatewayMessage,
    GatewayResult,
    MessageGateway,
)
from app.integration.gateway.registry import GatewayRegistry

logger = logging.getLogger("gula.integration.gateway.soap")


class SOAPGateway(MessageGateway):
    def __init__(self, name: str = "soap", config: GatewayConfig | None = None):
        super().__init__(name, config)
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> bool:
        try:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                headers={
                    "Content-Type": "text/xml; charset=utf-8",
                    "SOAPAction": self.config.options.get("soap_action", ""),
                    **self.config.headers,
                },
            )
            self._connected = True
            logger.info("SOAP gateway connected: %s", self.config.endpoint)
            return True
        except Exception as exc:
            logger.error("SOAP gateway connection failed: %s", exc)
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
            soap_body = message.payload if isinstance(message.payload, str) else self._build_envelope(message.payload)
            headers = {}
            if message.headers.get("SOAPAction"):
                headers["SOAPAction"] = message.headers["SOAPAction"]
            resp = await self._client.post(self.config.endpoint, content=soap_body, headers=headers)
            lat = (time.monotonic() - start) * 1000
            return GatewayResult(
                success=resp.is_success,
                status_code=resp.status_code,
                data=resp.text,
                latency_ms=lat,
            )
        except Exception as exc:
            lat = (time.monotonic() - start) * 1000
            logger.error("SOAP send failed: %s", exc)
            return GatewayResult(success=False, error=str(exc), latency_ms=lat)

    async def receive(self) -> GatewayMessage | None:
        return None

    async def transform(self, message: GatewayMessage) -> GatewayMessage:
        return message

    def _build_envelope(self, body: dict[str, Any]) -> str:
        ns = self.config.options.get("namespace", "http://tempuri.org/")
        method = body.get("method", "Request")
        params = body.get("params", {})
        param_xml = "".join(f"<{k}>{v}</{k}>" for k, v in params.items())
        return (
            f'<?xml version="1.0" encoding="utf-8"?>'
            f'<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" '
            f'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            f'xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
            f'<soap:Header/><soap:Body>'
            f'<{method} xmlns="{ns}">{param_xml}</{method}>'
            f'</soap:Body></soap:Envelope>'
        )


GatewayRegistry.register(SOAPGateway())
