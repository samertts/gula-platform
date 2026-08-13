from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import Any

from backend.app._compat import UTC

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
    timestamp = datetime.now(UTC).isoformat()
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
    from sqlalchemy import bindparam, column, select, table

    audit_logs = table(
        "audit_logs",
        column("id"),
        column("action"),
        column("entity_type"),
        column("entity_id"),
        column("user_id"),
        column("lab_id"),
        column("details"),
        column("previous_hash"),
        column("chain_hash"),
        column("timestamp"),
    )
    conditions = []
    params: dict[str, Any] = {}
    if entity_type:
        conditions.append(audit_logs.c.entity_type == bindparam("entity_type"))
        params["entity_type"] = entity_type
    if entity_id is not None:
        conditions.append(audit_logs.c.entity_id == bindparam("entity_id"))
        params["entity_id"] = str(entity_id)
    if user_id is not None:
        conditions.append(audit_logs.c.user_id == bindparam("user_id"))
        params["user_id"] = user_id
    if lab_id is not None:
        conditions.append(audit_logs.c.lab_id == bindparam("lab_id"))
        params["lab_id"] = lab_id
    if action:
        conditions.append(audit_logs.c.action == bindparam("action"))
        params["action"] = action
    stmt = (
        select(
            audit_logs.c.id,
            audit_logs.c.action,
            audit_logs.c.entity_type,
            audit_logs.c.entity_id,
            audit_logs.c.user_id,
            audit_logs.c.lab_id,
            audit_logs.c.details,
            audit_logs.c.previous_hash,
            audit_logs.c.chain_hash,
            audit_logs.c.timestamp,
        )
        .select_from(audit_logs)
        .where(*conditions)
        .order_by(audit_logs.c.id.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = db_session.execute(stmt, params).mappings().all()
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
