from __future__ import annotations

"""Contracts for Encounter_management capability - input/output schemas."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Encounter_managementInput:
    action: str = "execute"
    data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Encounter_managementOutput:
    success: bool = True
    data: dict = field(default_factory=dict)
    error: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
