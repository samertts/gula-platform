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

logger = logging.getLogger("gula.integration.gateway.hl7")


class HL7Gateway(MessageGateway):
    SEGMENT_SEPARATOR = "\r"
    FIELD_SEPARATOR = "|"
    COMPONENT_SEPARATOR = "^"
    REPETITION_SEPARATOR = "~"
    ESCAPE_CHARACTER = "\\"
    SUBCOMPONENT_SEPARATOR = "&"

    def __init__(self, name: str = "hl7", config: GatewayConfig | None = None):
        super().__init__(name, config)
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> bool:
        try:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                headers={"Content-Type": "x-application/hl7-v2+er", **self.config.headers},
            )
            self._connected = True
            logger.info("HL7 gateway connected: %s", self.config.endpoint)
            return True
        except Exception as exc:
            logger.error("HL7 gateway connection failed: %s", exc)
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
            hl7_message = message.payload if isinstance(message.payload, str) else self._serialize(message.payload)
            resp = await self._client.post(
                self.config.endpoint,
                content=hl7_message,
            )
            lat = (time.monotonic() - start) * 1000
            ack = self._parse_ack(resp.text) if resp.text else None
            return GatewayResult(
                success=resp.is_success and (ack is None or ack.get("ack_code") in ("AA", "CA")),
                status_code=resp.status_code,
                data=ack,
                latency_ms=lat,
            )
        except Exception as exc:
            lat = (time.monotonic() - start) * 1000
            logger.error("HL7 send failed: %s", exc)
            return GatewayResult(success=False, error=str(exc), latency_ms=lat)

    async def receive(self) -> GatewayMessage | None:
        return None

    async def transform(self, message: GatewayMessage) -> GatewayMessage:
        return message

    def parse_message(self, raw: str) -> dict[str, Any]:
        segments = raw.strip().split(self.SEGMENT_SEPARATOR)
        parsed: dict[str, Any] = {"segments": {}}
        for seg in segments:
            if not seg.strip():
                continue
            seg_name = seg[:3]
            fields = seg[3:].split(self.FIELD_SEPARATOR)
            parsed["segments"][seg_name] = fields
            if seg_name == "MSH":
                parsed["message_type"] = fields[8] if len(fields) > 8 else ""
                parsed["sending_app"] = fields[2] if len(fields) > 2 else ""
                parsed["receiving_app"] = fields[3] if len(fields) > 3 else ""
        return parsed

    def _serialize(self, msg: dict[str, Any]) -> str:
        segments = []
        for seg_name, fields in msg.get("segments", {}).items():
            segments.append(seg_name + self.FIELD_SEPARATOR.join(fields))
        return self.SEGMENT_SEPARATOR.join(segments)

    def _parse_ack(self, raw: str) -> dict[str, str]:
        parsed = self.parse_message(raw)
        ack_seg = parsed.get("segments", {}).get("MSA", [])
        return {
            "ack_code": ack_seg[0] if len(ack_seg) > 0 else "",
            "ack_message": ack_seg[1] if len(ack_seg) > 1 else "",
        }

    def build_ack(self, original_msh: list, ack_code: str = "AA") -> str:
        msh = [
            "MSH",
            "^~\\&",
            original_msh[2] if len(original_msh) > 2 else "",
            original_msh[3] if len(original_msh) > 3 else "",
            original_msh[4] if len(original_msh) > 4 else "",
            original_msh[5] if len(original_msh) > 5 else "",
            time.strftime("%Y%m%d%H%M%S"),
            "",
            "ACK",
            original_msh[9] if len(original_msh) > 9 else "",
        ]
        msa = ["MSA", ack_code, original_msh[9] if len(original_msh) > 9 else ""]
        return (
            self.FIELD_SEPARATOR.join(msh)
            + self.SEGMENT_SEPARATOR
            + self.FIELD_SEPARATOR.join(msa)
        )


GatewayRegistry.register(HL7Gateway())
