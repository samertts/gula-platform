"""Workspace Platform — PROGRAM-STABLE-003 Phase 2 & Phase 6.

Every identity may own multiple workspaces. The user selects ONE workspace
after login and permissions never cross workspace boundaries.
"""

from __future__ import annotations

from app.identity.workspaces.services import (
    WorkspaceError,
    WorkspaceIsolationError,
    WorkspaceService,
)

__all__ = ["WorkspaceError", "WorkspaceIsolationError", "WorkspaceService"]
