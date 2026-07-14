from __future__ import annotations

"""Contracts for Clinical_foundation capability - input/output schemas."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Clinical_foundationInput:
    action: str = "execute"
    data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Clinical_foundationOutput:
    success: bool = True
    data: dict = field(default_factory=dict)
    error: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
