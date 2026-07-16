from __future__ import annotations

import contextlib
import io
import logging
import time
from pathlib import PurePosixPath
from typing import Any

from backend.app.integration.gateway.base import (
    GatewayConfig,
    GatewayMessage,
    GatewayResult,
    MessageGateway,
)
from backend.app.integration.gateway.registry import GatewayRegistry

logger = logging.getLogger("gula.integration.gateway.sftp")


class SFTPGateway(MessageGateway):
    def __init__(self, name: str = "sftp", config: GatewayConfig | None = None):
        super().__init__(name, config)
        self._transport: Any = None
        self._sftp: Any = None

    async def connect(self) -> bool:
        try:
            import paramiko
            self._transport = paramiko.Transport(self.config.endpoint)
            self._transport.connect(
                username=self.config.options.get("username", ""),
                password=self.config.options.get("password", ""),
                pkey=self.config.options.get("private_key"),
            )
            self._sftp = paramiko.SFTPClient.from_transport(self._transport)
            self._connected = True
            logger.info("SFTP gateway connected: %s", self.config.endpoint)
            return True
        except ImportError:
            logger.warning("paramiko not installed — SFTP will use simulated mode")
            self._connected = True
            return True
        except Exception as exc:
            logger.error("SFTP gateway connection failed: %s", exc)
            return False

    async def disconnect(self) -> bool:
        if self._sftp:
            with contextlib.suppress(Exception):
                self._sftp.close()
            self._sftp = None
        if self._transport:
            with contextlib.suppress(Exception):
                self._transport.close()
            self._transport = None
        self._connected = False
        return True

    async def send(self, message: GatewayMessage) -> GatewayResult:
        start = time.monotonic()
        try:
            remote_path = message.destination or self.config.options.get("remote_path", "/inbound")
            filename = message.headers.get("filename", f"{int(time.time())}.json")
            full_path = str(PurePosixPath(remote_path) / filename)
            content = message.payload if isinstance(message.payload, bytes) else str(message.payload).encode()
            if self._sftp:
                with io.BytesIO(content) as f:
                    self._sftp.putfo(f, full_path)
            lat = (time.monotonic() - start) * 1000
            return GatewayResult(
                success=True,
                data={"path": full_path, "size": len(content)},
                latency_ms=lat,
            )
        except ImportError:
            lat = (time.monotonic() - start) * 1000
            return GatewayResult(success=True, latency_ms=lat)
        except Exception as exc:
            lat = (time.monotonic() - start) * 1000
            logger.error("SFTP send failed: %s", exc)
            return GatewayResult(success=False, error=str(exc), latency_ms=lat)

    async def receive(self) -> GatewayMessage | None:
        return None

    async def transform(self, message: GatewayMessage) -> GatewayMessage:
        return message

    async def list_files(self, remote_path: str = "/") -> list[str]:
        if self._sftp:
            try:
                return self._sftp.listdir(remote_path)
            except Exception as exc:
                logger.error("SFTP listdir failed: %s", exc)
        return []

    async def download(self, remote_path: str) -> bytes | None:
        if self._sftp:
            try:
                with io.BytesIO() as f:
                    self._sftp.getfo(remote_path, f)
                    return f.getvalue()
            except Exception as exc:
                logger.error("SFTP download failed: %s", exc)
        return None


GatewayRegistry.register(SFTPGateway())
