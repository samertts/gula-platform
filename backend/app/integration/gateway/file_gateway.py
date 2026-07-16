from __future__ import annotations

import csv
import io
import json
import logging
import time
from pathlib import Path
from typing import Any

from backend.app.integration.gateway.base import (
    GatewayConfig,
    GatewayMessage,
    GatewayResult,
    MessageGateway,
)
from backend.app.integration.gateway.registry import GatewayRegistry

logger = logging.getLogger("gula.integration.gateway.file")


class FileGateway(MessageGateway):
    FORMATS = {"csv", "json", "xml"}

    def __init__(self, name: str = "file", config: GatewayConfig | None = None):
        super().__init__(name, config)
        self._watch_dir: Path | None = None

    async def connect(self) -> bool:
        watch_path = self.config.options.get("watch_dir", "")
        if watch_path:
            self._watch_dir = Path(watch_path)
            self._watch_dir.mkdir(parents=True, exist_ok=True)
        self._connected = True
        logger.info("File gateway connected — watch_dir: %s", watch_path or "none")
        return True

    async def disconnect(self) -> bool:
        self._connected = False
        return True

    async def send(self, message: GatewayMessage) -> GatewayResult:
        start = time.monotonic()
        try:
            output_dir = self._watch_dir or Path(self.config.options.get("output_dir", "/tmp/gula-file-gateway"))
            output_dir.mkdir(parents=True, exist_ok=True)
            file_format = message.headers.get("format", "json").lower()
            filename = message.headers.get("filename", f"export_{int(time.time())}.{file_format}")
            output_path = output_dir / filename
            content = self._serialize(message.payload, file_format)
            if message.headers.get("mode", "write") == "append" and output_path.exists():
                mode = "a"
            else:
                mode = "w"
            with open(output_path, mode, encoding="utf-8") as f:
                f.write(content)
            lat = (time.monotonic() - start) * 1000
            return GatewayResult(
                success=True,
                data={"path": str(output_path), "size": len(content)},
                latency_ms=lat,
            )
        except Exception as exc:
            lat = (time.monotonic() - start) * 1000
            logger.error("File send failed: %s", exc)
            return GatewayResult(success=False, error=str(exc), latency_ms=lat)

    async def receive(self) -> GatewayMessage | None:
        if not self._watch_dir:
            return None
        try:
            files = sorted(self._watch_dir.glob("*.json")) + sorted(self._watch_dir.glob("*.csv"))
            for fpath in files:
                if not fpath.is_file():
                    continue
                with open(fpath, encoding="utf-8") as f:
                    content = f.read()
                ext = fpath.suffix.lower()
                data = self._deserialize(content, ext.lstrip("."))
                fpath.unlink()
                return GatewayMessage(
                    payload=data,
                    headers={"filename": fpath.name, "format": ext.lstrip(".")},
                )
        except Exception as exc:
            logger.error("File receive failed: %s", exc)
        return None

    async def transform(self, message: GatewayMessage) -> GatewayMessage:
        target_format = message.headers.get("target_format", "json")
        if target_format not in self.FORMATS:
            return message
        payload_str = self._serialize(message.payload, target_format)
        message.payload = self._deserialize(payload_str, target_format)
        message.content_type = f"application/{target_format}"
        return message

    def _serialize(self, data: Any, fmt: str) -> str:
        if fmt == "json":
            return json.dumps(data, ensure_ascii=False, indent=2, default=str)
        if fmt == "csv":
            if isinstance(data, list) and data:
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
                return output.getvalue()
            return str(data)
        if fmt == "xml":
            return self._to_xml(data)
        return str(data)

    def _deserialize(self, content: str, fmt: str) -> Any:
        if fmt == "json":
            return json.loads(content)
        if fmt == "csv":
            reader = csv.DictReader(io.StringIO(content))
            return list(reader)
        return content

    def _to_xml(self, data: Any, root: str = "root") -> str:
        if isinstance(data, dict):
            items = "".join(f"<{k}>{self._to_xml(v, k)}</{k}>" for k, v in data.items())
            return f"<{root}>{items}</{root}>" if root != "root" else items
        if isinstance(data, list):
            return "".join(self._to_xml(item, "item") for item in data)
        return str(data)


GatewayRegistry.register(FileGateway())
