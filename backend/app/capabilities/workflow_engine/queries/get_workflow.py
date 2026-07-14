from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Get_workflowQuery:
    """get_workflow query for workflow_engine capability."""
    filters: dict = field(default_factory=dict)
    skip: int = 0
    limit: int = 100
