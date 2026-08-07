"""Archived Shared Core `audit` reimplementation (ADR-028).

Commit 1.7 (PROGRAM-01, Wave 1 order 4): `AuditLogger` in
`backend/app/document_intelligence/security.py` was dead code (zero production
importers; sole consumer was `backend/tests/test_docintel_enterprise.py`) and
a reimplementation of the canonical `backend/app/identity/services/audit_service.py`
hash-chained audit provider. Preserved byte-for-byte (with the imports required
for standalone execution) so the migration is independently reversible.

Class + module singleton + accessor preserved from
`backend/app/document_intelligence/security.py` (lines 123-164 at time of
archive). Canonical provider: `backend/app/identity/services/audit_service.py`
(`AuditService`, immutable hash-chained audit log).
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class AuditLogger:
    def __init__(self):
        self._entries: list[dict[str, Any]] = []

    async def log(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        actor: str,
        changes: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "actor": actor,
            "changes": changes or {},
            "metadata": metadata or {},
        }
        self._entries.append(entry)
        logger.info("Audit: %s %s %s by %s", action, entity_type, entity_id, actor)
        return entry

    def get_entries(self, entity_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        if entity_id:
            return [e for e in self._entries if e["entity_id"] == entity_id][-limit:]
        return self._entries[-limit:]

    def search(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        return [e for e in self._entries if q in json.dumps(e, default=str).lower()]


_audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    return _audit_logger
