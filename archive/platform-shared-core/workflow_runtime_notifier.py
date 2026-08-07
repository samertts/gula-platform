"""Archived orphan interface — WorkflowNotifier (Shared Core: notifications).

PROGRAM-01 Wave 1 order 10 — finding #25
(`rule_id: notifications`, signal matching NotificationService/Notifier class
name patterns).

Source: `backend/app/national/workflow_runtime/application/interfaces.py`
(removed in Commit 1.13).

Extraction is byte-for-byte (class body unchanged). The class had zero
consumers repo-wide; the module itself had zero importers. It is preserved
for provenance and reversibility per ADR-028 (archive-first, every migration
independently reversible via a single `git revert`).

The remaining orphan ABCs of that module (`WorkflowStepExecutor`,
`WorkflowApprovalHandler`, `WorkflowTimerHandler`) are not Shared Core
findings and remain in the active tree (dormant national module preservation).
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class WorkflowNotifier(ABC):
    @abstractmethod
    async def notify_approval_required(
        self,
        execution_id: str,
        step_name: str,
        roles: list[str],
    ) -> None: ...

    @abstractmethod
    async def notify_workflow_failed(
        self,
        execution_id: str,
        workflow_name: str,
        error: str,
    ) -> None: ...

    @abstractmethod
    async def notify_workflow_completed(
        self,
        execution_id: str,
        workflow_name: str,
    ) -> None: ...
