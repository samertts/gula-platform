from __future__ import annotations

from enum import Enum


class Workflow_enginePermission(Enum):
    WORKFLOW.CREATE = "workflow_engine:workflow.create"
    WORKFLOW.READ = "workflow_engine:workflow.read"
    WORKFLOW.TRANSITION = "workflow_engine:workflow.transition"
    WORKFLOW.ADMIN = "workflow_engine:workflow.admin"

    def describe(self) -> str:
        descriptions = {        "workflow_engine:workflow.create": "Workflow.Create",
                "workflow_engine:workflow.read": "Workflow.Read",
                "workflow_engine:workflow.transition": "Workflow.Transition",
                "workflow_engine:workflow.admin": "Workflow.Admin"}
        return descriptions.get(self, self.value)
