from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime

from app.health_data.enums import DataClassification

logger = logging.getLogger("gula.health_data.governance.audit")


@dataclass
class DataAccessAudit:
    id: str
    user_id: str
    user_role: str
    action: str
    resource_type: str
    resource_id: str
    dataset: str
    purpose: str
    classification: DataClassification
    access_time: datetime
    ip_address: str = ""
    user_agent: str = ""
    granted: bool = True
    reason: str = ""
    rows_accessed: int = 0
    fields_accessed: list[str] = field(default_factory=list)
    tenant_id: str = ""


class DataAccessAuditTrail:
    def __init__(self):
        self._entries: list[DataAccessAudit] = []
        self._hash_chain: list[str] = []
        self._previous_hash: str = "0" * 64

    def record(self, entry: DataAccessAudit) -> None:
        self._entries.append(entry)
        chain_entry = self._build_chain_entry(entry)
        current_hash = hashlib.sha256(
            f"{self._previous_hash}{chain_entry}".encode(),
        ).hexdigest()
        self._hash_chain.append(current_hash)
        self._previous_hash = current_hash
        logger.debug(
            "Audit recorded: %s on %s/%s by %s — %s",
            entry.action, entry.resource_type, entry.resource_id, entry.user_id,
            "GRANTED" if entry.granted else "DENIED",
        )

    def query(
        self,
        user_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        dataset: str | None = None,
        action: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[DataAccessAudit]:
        results = list(self._entries)
        if user_id:
            results = [e for e in results if e.user_id == user_id]
        if resource_type:
            results = [e for e in results if e.resource_type == resource_type]
        if resource_id:
            results = [e for e in results if e.resource_id == resource_id]
        if dataset:
            results = [e for e in results if e.dataset == dataset]
        if action:
            results = [e for e in results if e.action == action]
        if start_time:
            results = [e for e in results if e.access_time >= start_time]
        if end_time:
            results = [e for e in results if e.access_time <= end_time]
        return results[:limit]

    def verify_chain(self) -> bool:
        previous = "0" * 64
        for i, entry in enumerate(self._entries):
            chain_entry = self._build_chain_entry(entry)
            expected = hashlib.sha256(f"{previous}{chain_entry}".encode()).hexdigest()
            if self._hash_chain[i] != expected:
                logger.error("Hash chain broken at entry %d", i)
                return False
            previous = self._hash_chain[i]
        return True

    def count(self) -> int:
        return len(self._entries)

    def _build_chain_entry(self, entry: DataAccessAudit) -> str:
        return json.dumps({
            "id": entry.id,
            "user_id": entry.user_id,
            "action": entry.action,
            "resource_type": entry.resource_type,
            "resource_id": entry.resource_id,
            "access_time": entry.access_time.isoformat(),
            "granted": entry.granted,
        }, sort_keys=True, default=str)
