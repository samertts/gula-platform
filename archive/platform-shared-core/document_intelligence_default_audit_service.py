"""Archived Shared Core `audit` reimplementation (ADR-028).

Commit 3.4 (PROGRAM-01, Wave 4 order 16): `DefaultAuditService` in
`backend/app/document_intelligence/application/wiring.py` was a no-op stub — it
only emitted `logger.info("AUDIT: ...")` and returned `[]` from
`get_document_history`, silently dropping every audit event. It reimplemented
(by shadowing) the canonical
`backend/app/identity/services/audit_service.py::AuditService` immutable
hash-chained audit provider. It was the ONLY `audit` concretion injected into
the six doc-intel services and the `DocumentIntelligenceOrchestrator`
composition root; the doc-intel domain `AuditService` ABC
(`application/interfaces.py`) is Retained as Domain-Owned (classification #4).
Preserved byte-for-byte (with the imports required for standalone execution) so
the migration is independently reversible.

Class + module singleton + accessor preserved from
`backend/app/document_intelligence/application/wiring.py` (lines 67-72 at time
of archive). Canonical provider: `backend/app/identity/services/audit_service.py`
(`AuditService`, immutable hash-chained audit log). The composition root now
injects `CanonicalAuditAdapter` (same module), a thin adapter that maps the
retained doc-intel ABC onto the canonical provider — fail-closed, never
silently dropping audit rows (ADR-031).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("gula.document_intelligence.wiring")


class DefaultAuditService:
    async def log_event(self, event_type: str, document_id: Any, details: dict) -> None:
        logger.info("AUDIT: %s [%s] %s", event_type, document_id, details)

    async def get_document_history(self, document_id: Any) -> list[dict]:
        return []
