"""Archived Shared Core `audit` reimplementation (ADR-028).

Commit 3.5 (PROGRAM-01, Wave 4 order 17): `SQLAlchemyTaskAuditLogRepository` in
`backend/app/national/task_engine/infrastructure/repository.py` was a no-op
stub — `save` returned the log unchanged (persisting nothing) and
`find_by_task`/`find_by_user`/`list` always returned empty lists, silently
dropping every task_engine audit event. It reimplemented (by shadowing) the
canonical `backend/app/identity/services/audit_service.py::AuditService`
immutable hash-chained audit provider. It was the ONLY `audit` concretion
injected into the task_engine composition root
(`backend/app/national/task_engine/api/routes.py::_get_service`); the
task_engine domain `TaskAuditLogRepository` ABC (`domain/repository.py`) is
Retained as Domain-Owned (classification #8). Preserved byte-for-byte (with
the imports required for standalone execution) so the migration is
independently reversible.

Class preserved from
`backend/app/national/task_engine/infrastructure/repository.py` (lines 266-277
at time of archive). Canonical provider: `backend/app/identity/services/audit_service.py`
(`AuditService`, immutable hash-chained audit log). The composition root now
injects `CanonicalTaskAuditRepository` (same module), a thin adapter that maps
the retained task_engine ABC onto the canonical provider — fail-closed, never
silently dropping audit rows (ADR-031).
"""

from __future__ import annotations

from typing import Any

from app.national.task_engine.domain.repository import TaskAuditLogRepository


class SQLAlchemyTaskAuditLogRepository(TaskAuditLogRepository):
    async def save(self, log: Any) -> Any:
        return log

    async def find_by_task(self, task_id: str) -> list:
        return []

    async def find_by_user(self, user_id: str) -> list:
        return []

    async def list(self, skip: int = 0, limit: int = 100, filters: dict | None = None) -> list:
        return []
