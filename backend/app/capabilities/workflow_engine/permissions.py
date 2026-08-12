from __future__ import annotations

from enum import Enum


class Workflow_enginePermission(Enum):
    CREATE = "workflow_engine:workflow.create"
    READ = "workflow_engine:workflow.read"
    TRANSITION = "workflow_engine:workflow.transition"
    ADMIN = "workflow_engine:workflow.admin"

    def describe(self) -> str:
        descriptions = {        "workflow_engine:workflow.create": "Workflow.Create",
                "workflow_engine:workflow.read": "Workflow.Read",
                "workflow_engine:workflow.transition": "Workflow.Transition",
                "workflow_engine:workflow.admin": "Workflow.Admin"}
        return descriptions.get(self, self.value)
