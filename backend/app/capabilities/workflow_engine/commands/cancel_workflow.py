from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Cancel_workflowCommand:
    """cancel_workflow command for workflow_engine capability."""
    command_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: dict = field(default_factory=dict)
