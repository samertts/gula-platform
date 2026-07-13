from __future__ import annotations

import hashlib
import json
import logging
from datetime import timezone, datetime
from typing import Any

logger = logging.getLogger("gula.audit")


def compute_chain_hash(
    previous_hash: str,
    action: str,
    entity_type: str,
    entity_id: str | int,
    user_id: int | None,
    timestamp: str,
) -> str:
    raw = f"{previous_hash}|{action}|{entity_type}|{entity_id}|{user_id}|{timestamp}"
    return hashlib.sha256(raw.encode()).hexdigest()


def create_audit_entry(
    db_session: Any,
    action: str,
    entity_type: str,
    entity_id: str | int,
    user_id: int | None,
    lab_id: int | None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from sqlalchemy import text
    last = db_session.execute(
        text("SELECT chain_hash FROM audit_logs ORDER BY id DESC LIMIT 1 FOR UPDATE")
    ).scalar()
    previous_hash = last if last else "GENESIS"
    timestamp = datetime.now(timezone.utc).isoformat()
    chain_hash = compute_chain_hash(previous_hash, action, entity_type, str(entity_id), user_id, timestamp)
    result = db_session.execute(
        text("""
            INSERT INTO audit_logs (action, entity_type, entity_id, user_id, lab_id, details, previous_hash, chain_hash, timestamp)
            VALUES (:action, :entity_type, :entity_id, :user_id, :lab_id, :details, :previous_hash, :chain_hash, :timestamp)
            RETURNING id, chain_hash, previous_hash, timestamp
        """),
        {
            "action": action,
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "user_id": user_id,
            "lab_id": lab_id,
            "details": json.dumps(details) if details else "{}",
            "previous_hash": previous_hash,
            "chain_hash": chain_hash,
            "timestamp": timestamp,
        },
    )
    row = result.mappings().one()
    db_session.commit()
    return dict(row)


def query_audit_log(
    db_session: Any,
    entity_type: str | None = None,
    entity_id: str | int | None = None,
    user_id: int | None = None,
    lab_id: int | None = None,
    action: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    from sqlalchemy import text
    conditions = []
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if entity_type:
        conditions.append("entity_type = :entity_type")
        params["entity_type"] = entity_type
    if entity_id is not None:
        conditions.append("entity_id = :entity_id")
        params["entity_id"] = str(entity_id)
    if user_id is not None:
        conditions.append("user_id = :user_id")
        params["user_id"] = user_id
    if lab_id is not None:
        conditions.append("lab_id = :lab_id")
        params["lab_id"] = lab_id
    if action:
        conditions.append("action = :action")
        params["action"] = action
    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    rows = db_session.execute(
        text(f"""
            SELECT id, action, entity_type, entity_id, user_id, lab_id, details,
                   previous_hash, chain_hash, timestamp
            FROM audit_logs
            WHERE {where_clause}
            ORDER BY id DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    ).mappings().all()
    return [dict(r) for r in rows]


class AuditService:
    def __init__(self, db_session: Any) -> None:
        self._db = db_session

    def log(
        self,
        action: str,
        entity_type: str,
        entity_id: str | int,
        user_id: int | None = None,
        lab_id: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return create_audit_entry(self._db, action, entity_type, entity_id, user_id, lab_id, details)

    def query(
        self,
        entity_type: str | None = None,
        entity_id: str | int | None = None,
        user_id: int | None = None,
        lab_id: int | None = None,
        action: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        return query_audit_log(self._db, entity_type, entity_id, user_id, lab_id, action, limit, offset)
