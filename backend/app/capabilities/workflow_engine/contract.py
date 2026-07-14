from __future__ import annotations

"""Contracts for Workflow_engine capability - input/output schemas."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Workflow_engineInput:
    action: str = "execute"
    data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Workflow_engineOutput:
    success: bool = True
    data: dict = field(default_factory=dict)
    error: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
