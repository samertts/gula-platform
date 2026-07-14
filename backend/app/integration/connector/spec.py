from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class ConnectorType(Enum):
    REST = auto()
    GRAPHQL = auto()
    GRPC = auto()
    WEBSOCKET = auto()
    FHIR = auto()
    HL7 = auto()
    DICOM = auto()
    ASTM = auto()
    CUSTOM = auto()


class ConnectorStatus(Enum):
    CREATED = auto()
    CONNECTED = auto()
    ACTIVE = auto()
    DEGRADED = auto()
    DISCONNECTED = auto()
    FAILED = auto()
    SUSPENDED = auto()


@dataclass
class ConnectorAuth:
    type: str = "none"
    credentials: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectorEndpoint:
    url: str = ""
    method: str = "GET"
    headers: dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0


@dataclass
class ConnectorHealth:
    status: str = "unknown"
    latency_ms: float = 0.0
    last_checked: float = 0.0
    error: str | None = None


@dataclass
class ConnectorMetric:
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    avg_latency_ms: float = 0.0


@dataclass
class ConnectorSpec:
    id: str = ""
    name: str = ""
    connector_type: ConnectorType = ConnectorType.REST
    version: str = "1.0.0"
    description: str = ""
    status: ConnectorStatus = ConnectorStatus.CREATED
    auth: ConnectorAuth = field(default_factory=ConnectorAuth)
    endpoints: list[ConnectorEndpoint] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    health: ConnectorHealth = field(default_factory=ConnectorHealth)
    metrics: ConnectorMetric = field(default_factory=ConnectorMetric)
    created_at: float = 0.0
    updated_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            now = time.time()
            self.created_at = now
            self.updated_at = now
