"""Archived Shared Core `workflow_engine` reimplementation (ADR-028 / ADR-036).

PROGRAM-01 Wave 4 order 19 — finding #44
(`rule_id: workflow_engine`, signal `def\\s+execute_workflow\\s*\\(`).

Source: `backend/app/national/workflow_runtime/application/interfaces.py` (moved by `git mv` in Commit 3.6).

The national workflow_runtime package was wired-but-broken: its
`application/service.py` was 0 bytes, so every `/national/workflows/*` handler
raised ImportError (HTTP 500). It reimplemented (by shadowing) the canonical
live `backend/app/workflows/engine.py::WorkflowEngine`, exposed at
`/niam/workflows`. The package was archived per ADR-028 (archive-first, every
migration independently reversible via a single `git revert`). Content is
preserved byte-for-byte (with the imports required for standalone execution).
Canonical provider: `backend/app/workflows` + `backend/app/identity/workflows/routes.py`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class WorkflowStepExecutor(ABC):
    @abstractmethod
    async def execute(
        self,
        step_type: str,
        step_name: str,
        input_data: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def compensate(
        self,
        step_type: str,
        step_name: str,
        execution_data: dict[str, Any],
    ) -> None: ...


class WorkflowApprovalHandler(ABC):
    @abstractmethod
    async def request_approval(
        self,
        execution_id: str,
        step_id: str,
        roles: list[str],
        context: dict[str, Any],
    ) -> None: ...

    @abstractmethod
    async def approve(
        self,
        execution_id: str,
        step_id: str,
        approver_id: str,
        comments: str | None = None,
    ) -> bool: ...

    @abstractmethod
    async def reject(
        self,
        execution_id: str,
        step_id: str,
        approver_id: str,
        comments: str | None = None,
    ) -> bool: ...


class WorkflowTimerHandler(ABC):
    @abstractmethod
    async def schedule_timeout(
        self,
        execution_id: str,
        step_id: str,
        timeout_s: float,
    ) -> str: ...

    @abstractmethod
    async def cancel_timer(self, timer_id: str) -> None: ...
