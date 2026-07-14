from __future__ import annotations

"""Contracts for Storage_service capability - input/output schemas."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Storage_serviceInput:
    action: str = "execute"
    data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Storage_serviceOutput:
    success: bool = True
    data: dict = field(default_factory=dict)
    error: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
