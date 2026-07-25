from __future__ import annotations

import asyncio
import contextlib
import logging
import re
import time
from typing import Any

from .base import BaseConnector, ConnectorConfig, ConnectorResult, ConnectorStatus

logger = logging.getLogger("gula.ecosystem.hl7")


class HL7Connector(BaseConnector):
    MLLP_START = b"\x0b"
    MLLP_END = b"\x1c\x0d"
    DEFAULT_PORT = 2575

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._host: str = ""
        self._port: int = self.DEFAULT_PORT
        self._segment_separator = "\r"

    async def connect(self) -> bool:
        try:
            endpoint = self._config.endpoint or ""
            if ":" in endpoint:
                self._host, port_str = endpoint.split(":", 1)
                self._port = int(port_str)
            else:
                self._host = endpoint
                self._port = self.DEFAULT_PORT

            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=self._config.timeout_seconds,
            )
            self._connected = True
            self._status = ConnectorStatus.ACTIVE
            return True
        except TimeoutError:
            self._status = ConnectorStatus.ERROR
            self._metrics["last_error"] = "connection timeout"
            return False
        except Exception as exc:
            self._status = ConnectorStatus.ERROR
            self._metrics["last_error"] = str(exc)
            return False

    async def disconnect(self) -> bool:
        try:
            if self._writer:
                self._writer.close()
                with contextlib.suppress(Exception):
                    await self._writer.wait_closed()
                self._writer = None
                self._reader = None
            self._connected = False
            self._status = ConnectorStatus.INACTIVE
            return True
        except Exception as exc:
            self._metrics["last_error"] = str(exc)
            return False

    async def send(self, data: Any) -> ConnectorResult:
        if isinstance(data, str):
            message = data
        elif isinstance(data, dict):
            message = data.get("message", "")
            if not message:
                message = self._build_message(data)
        else:
            message = str(data)

        if not message:
            return self._build_result(False, error="empty message", status_code=400)

        if not message.startswith("MSH"):
            return self._build_result(
                False, error="message must start with MSH segment", status_code=400,
            )

        return await self._send_raw(message)

    async def receive(self) -> ConnectorResult:
        if not self._reader or not self._connected:
            return self._build_result(False, error="not connected", status_code=503)

        start = time.monotonic()
        try:
            raw = await asyncio.wait_for(
                self._read_mllp_message(),
                timeout=self._config.timeout_seconds,
            )
            duration_ms = int((time.monotonic() - start) * 1000)
            if not raw:
                return self._build_result(False, error="no data received", duration_ms=duration_ms)

            parsed = self._parse_message(raw)
            self._record_success(duration_ms)
            return self._build_result(True, data=parsed, duration_ms=duration_ms)

        except TimeoutError:
            duration_ms = int((time.monotonic() - start) * 1000)
            self._record_failure("receive timeout", duration_ms)
            return self._build_result(False, error="receive timeout", duration_ms=duration_ms)
        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            self._record_failure(str(exc), duration_ms)
            return self._build_result(False, error=str(exc), duration_ms=duration_ms)

    async def _send_raw(self, message: str) -> ConnectorResult:
        if not self._writer or not self._connected:
            connected = await self.connect()
            if not connected:
                return self._build_result(False, error="not connected", status_code=503)

        start = time.monotonic()
        for attempt in range(self._config.retry_count + 1):
            try:
                framed = self.MLLP_START + message.encode("utf-8") + self.MLLP_END
                self._writer.write(framed)
                await self._writer.drain()

                ack = await asyncio.wait_for(
                    self._read_mllp_message(),
                    timeout=self._config.timeout_seconds,
                )
                duration_ms = int((time.monotonic() - start) * 1000)

                if not ack:
                    self._record_failure("no ACK received", duration_ms)
                    return self._build_result(
                        False, error="no ACK received", duration_ms=duration_ms,
                    )

                ack_text = ack.decode("utf-8", errors="replace")
                ack_code = self._parse_ack_code(ack_text)

                if ack_code == "AA":
                    self._record_success(duration_ms)
                    return self._build_result(
                        True,
                        data={"ack": ack_text, "ack_code": ack_code},
                        duration_ms=duration_ms,
                        status_code=200,
                    )
                if ack_code == "AE":
                    self._record_failure(f"application error: {ack_text}", duration_ms)
                    return self._build_result(
                        False,
                        data={"ack": ack_text, "ack_code": ack_code},
                        error="application error",
                        duration_ms=duration_ms,
                    )
                if ack_code == "AR":
                    self._record_failure(f"rejected: {ack_text}", duration_ms)
                    return self._build_result(
                        False,
                        data={"ack": ack_text, "ack_code": ack_code},
                        error="rejected",
                        duration_ms=duration_ms,
                    )
                self._record_success(duration_ms)
                return self._build_result(
                    True, data={"ack": ack_text, "ack_code": ack_code}, duration_ms=duration_ms,
                )

            except TimeoutError:
                if attempt < self._config.retry_count:
                    await asyncio.sleep(self._config.retry_delay_seconds * (2**attempt))
                    await self.connect()
                    continue
                duration_ms = int((time.monotonic() - start) * 1000)
                self._record_failure("send timeout after retries", duration_ms)
                return self._build_result(
                    False, error="send timeout after retries", duration_ms=duration_ms,
                )
            except BrokenPipeError:
                if attempt < self._config.retry_count:
                    await self.connect()
                    continue
                duration_ms = int((time.monotonic() - start) * 1000)
                self._record_failure("connection broken", duration_ms)
                return self._build_result(False, error="connection broken", duration_ms=duration_ms)
            except Exception as exc:
                duration_ms = int((time.monotonic() - start) * 1000)
                self._record_failure(str(exc), duration_ms)
                return self._build_result(False, error=str(exc), duration_ms=duration_ms)

        duration_ms = int((time.monotonic() - start) * 1000)
        self._record_failure("max retries exceeded", duration_ms)
        return self._build_result(False, error="max retries exceeded", duration_ms=duration_ms)

    async def _read_mllp_message(self) -> bytes | None:
        if not self._reader:
            return None
        buffer = bytearray()
        while True:
            byte = await self._reader.readexactly(1)
            if byte == self.MLLP_START:
                buffer = bytearray()
                continue
            if byte == self.MLLP_END[0]:
                next_byte = await self._reader.readexactly(1)
                if next_byte == self.MLLP_END[1]:
                    break
                buffer.extend(self.MLLP_END[0:1])
                buffer.extend(next_byte)
                continue
            buffer.extend(byte)
        return bytes(buffer) if buffer else None

    def _parse_message(self, raw: bytes) -> dict:
        text = raw.decode("utf-8", errors="replace")
        segments = text.split(self._segment_separator)
        parsed: dict[str, Any] = {
            "raw": text,
            "segments": [],
            "fields": {},
        }
        for segment in segments:
            if not segment.strip():
                continue
            seg_data = segment.split("|")
            seg_name = seg_data[0]
            parsed["segments"].append({"name": seg_name, "fields": seg_data[1:], "raw": segment})
            parsed["fields"][seg_name] = seg_data[1:]
            if seg_name == "MSH" and len(seg_data) > 11:
                parsed["message_type"] = seg_data[8] if len(seg_data) > 8 else ""
                parsed["sending_app"] = seg_data[2] if len(seg_data) > 2 else ""
                parsed["sending_facility"] = seg_data[3] if len(seg_data) > 3 else ""
                parsed["receiving_app"] = seg_data[4] if len(seg_data) > 4 else ""
                parsed["receiving_facility"] = seg_data[5] if len(seg_data) > 5 else ""
                parsed["message_datetime"] = seg_data[6] if len(seg_data) > 6 else ""
                parsed["message_control_id"] = seg_data[9] if len(seg_data) > 9 else ""
                parsed["version"] = seg_data[11] if len(seg_data) > 11 else ""
        return parsed

    def _build_message(self, data: dict) -> str:
        msh = data.get("MSH", {})
        segments = data.get("segments", [])
        if not segments:
            msh_fields = [
                "MSH",
                msh.get("separator", "^~\\&"),
                msh.get("sending_app", ""),
                msh.get("sending_facility", ""),
                msh.get("receiving_app", ""),
                msh.get("receiving_facility", ""),
                msh.get("datetime", time.strftime("%Y%m%d%H%M%S")),
                msh.get("security", ""),
                msh.get("message_type", ""),
                msh.get("message_control_id", str(int(time.time()))),
                msh.get("processing_id", "P"),
                msh.get("version", "2.5"),
            ]
            segments.append("|".join(msh_fields))
        return "\r".join(segments) + "\r"

    def _parse_ack_code(self, ack_text: str) -> str:
        msa_match = re.search(r"MSA\|([^|]+)", ack_text)
        if msa_match:
            return msa_match.group(1)
        if "MSA" in ack_text:
            parts = ack_text.split("MSA|")
            if len(parts) > 1:
                return parts[1].split("|")[0].strip()
        return "UNKNOWN"
