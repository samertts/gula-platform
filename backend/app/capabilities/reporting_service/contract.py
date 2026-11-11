from __future__ import annotations

"""Contracts for Reporting_service capability - input/output schemas."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Reporting_serviceInput:
    action: str = "execute"
    data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Reporting_serviceOutput:
    success: bool = True
    data: dict = field(default_factory=dict)
    error: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
