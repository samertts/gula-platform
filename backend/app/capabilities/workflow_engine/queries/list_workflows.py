from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class List_workflowsQuery:
    """list_workflows query for workflow_engine capability."""
    filters: dict = field(default_factory=dict)
    skip: int = 0
    limit: int = 100
