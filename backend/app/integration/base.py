from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class IntegrationStatus(Enum):
    ACTIVE = auto()
    INACTIVE = auto()
    DEGRADED = auto()
    FAILED = auto()
    OFFLINE = auto()


@dataclass
class IntegrationRoute:
    source: str = ""
    target: str = ""
    protocol: str = ""
    status: IntegrationStatus = IntegrationStatus.INACTIVE
    transform_pipeline: list[str] = field(default_factory=list)
    error_count: int = 0
    last_error: str | None = None


@dataclass
class UplinkBase:
    id: str = ""
    name: str = ""
    version: str = "1.0.0"
    status: IntegrationStatus = IntegrationStatus.INACTIVE
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

    def touch(self) -> None:
        self.updated_at = time.time()

    def mark_active(self) -> None:
        self.status = IntegrationStatus.ACTIVE
        self.touch()

    def mark_failed(self, error: str | None = None) -> None:
        self.status = IntegrationStatus.FAILED
        self.touch()
        if error:
            self.metadata["last_error"] = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "status": self.status.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }
