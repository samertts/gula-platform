from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ConnectorProtocol(Enum):
    REST = "rest"
    SOAP = "soap"
    GRAPHQL = "graphql"
    FHIR_REST = "fhir_rest"
    FHIR_MESSAGING = "fhir_messaging"
    HL7_V2 = "hl7_v2"
    ASTM = "astm"
    DICOM = "dicom"
    MQTT = "mqtt"
    AMQP = "amqp"
    SFTP = "sftp"
    FILE_WATCHER = "file_watcher"
    WEBHOOK = "webhook"
    CSV_IMPORT = "csv_import"
    EXCEL_IMPORT = "excel_import"
    MANUAL_IMPORT = "manual_import"


class ConnectorStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEGRADED = "degraded"
    DISABLED = "disabled"


class ConnectorDirection(Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class ConnectorConfig:
    name: str
    protocol: ConnectorProtocol
    direction: ConnectorDirection
    endpoint: str | None = None
    auth_type: str | None = None
    credentials: dict | None = None
    timeout_seconds: int = 30
    retry_count: int = 3
    retry_delay_seconds: int = 5
    circuit_breaker_threshold: int = 5
    rate_limit_per_minute: int = 60
    batch_size: int = 100
    options: dict | None = None


@dataclass
class ConnectorResult:
    success: bool
    data: Any = None
    error: str | None = None
    duration_ms: int = 0
    status_code: int = 200


class BaseConnector(ABC):
    def __init__(self, config: ConnectorConfig) -> None:
        self._config = config
        self._status = ConnectorStatus.INACTIVE
        self._connected = False
        self._metrics: dict[str, Any] = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_duration_ms": 0,
            "last_call_at": None,
            "last_error": None,
            "circuit_breaker_open": False,
            "consecutive_failures": 0,
        }

    @abstractmethod
    async def connect(self) -> bool: ...

    @abstractmethod
    async def disconnect(self) -> bool: ...

    @abstractmethod
    async def send(self, data: Any) -> ConnectorResult: ...

    @abstractmethod
    async def receive(self) -> ConnectorResult: ...

    async def health_check(self) -> bool:
        start = time.monotonic()
        try:
            if not self._connected:
                result = await self.connect()
                if not result:
                    return False
            duration = int((time.monotonic() - start) * 1000)
            self._metrics["last_call_at"] = time.time()
            self._metrics["total_duration_ms"] += duration
            self._status = ConnectorStatus.ACTIVE
            return True
        except Exception as exc:
            self._metrics["last_error"] = str(exc)
            self._status = ConnectorStatus.ERROR
            return False

    def get_status(self) -> ConnectorStatus:
        return self._status

    def get_metrics(self) -> dict:
        return {
            **self._metrics,
            "name": self._config.name,
            "protocol": self._config.protocol.value,
            "status": self._status.value,
        }

    def _record_success(self, duration_ms: int) -> None:
        self._metrics["total_calls"] += 1
        self._metrics["successful_calls"] += 1
        self._metrics["total_duration_ms"] += duration_ms
        self._metrics["last_call_at"] = time.time()
        self._metrics["consecutive_failures"] = 0
        self._status = ConnectorStatus.ACTIVE

    def _record_failure(self, error: str, duration_ms: int) -> None:
        self._metrics["total_calls"] += 1
        self._metrics["failed_calls"] += 1
        self._metrics["total_duration_ms"] += duration_ms
        self._metrics["last_call_at"] = time.time()
        self._metrics["last_error"] = error
        self._metrics["consecutive_failures"] += 1
        if self._metrics["consecutive_failures"] >= self._config.circuit_breaker_threshold:
            self._metrics["circuit_breaker_open"] = True
            self._status = ConnectorStatus.DEGRADED
        else:
            self._status = ConnectorStatus.ERROR
