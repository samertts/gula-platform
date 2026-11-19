from __future__ import annotations

"""Contracts for Fhir_interoperability capability - input/output schemas."""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Fhir_interoperabilityInput:
    action: str = "execute"
    data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Fhir_interoperabilityOutput:
    success: bool = True
    data: dict = field(default_factory=dict)
    error: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
