from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Workflow_engineCreateRequest:
    workflow_id: str
    state: str
    assignee: str


@dataclass
class Workflow_engineUpdateRequest:
    workflow_id: str = None
    state: str = None
    assignee: str = None


@dataclass
class Workflow_engineResponse:
    workflow_id: str
    state: str
    assignee: str
