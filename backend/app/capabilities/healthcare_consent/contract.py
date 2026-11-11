from __future__ import annotations

"""Contracts for Healthcare_consent capability - input/output schemas."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Healthcare_consentInput:
    action: str = "execute"
    data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Healthcare_consentOutput:
    success: bool = True
    data: dict = field(default_factory=dict)
    error: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
