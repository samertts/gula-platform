"""Shared audit facade.

P-01 / AUD-F01: the previous implementation wrote raw SQL into four legacy
columns (``entity_type``, ``entity_id``, ``previous_hash``, ``timestamp``) that
do not exist on the canonical ``audit_logs`` table, used a divergent chain hash
algorithm, and committed the caller's transaction. All writers now delegate to
the single canonical ``backend.app.services.audit_service.log_action`` writer.
The dormant enterprise modules are preserved and redirected, not removed.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import logging
import secrets
import sys
from typing import Any

logger = logging.getLogger("gula.audit")


def _canonical_audit_service():
    """Return the canonical audit module already in use in this process.

    The canonical module imports ``app._compat`` absolutely, so ``app`` is the
    required namespace; a freshly imported ``backend.app`` copy would create a
    second SQLAlchemy mapper registry. Reuse either namespace if it is already
    loaded (tests and legacy entry points may use ``backend.app``), otherwise
    import the canonical ``app`` namespace deterministically.
    """
    for name in ("app.services.audit_service", "backend.app.services.audit_service"):
        module = sys.modules.get(name)
        if module is not None:
            return module
    return importlib.import_module("app.services.audit_service")


def compute_chain_hash(
    previous_hash: str,
    action: str,
    entity_type: str,
    entity_id: str | int,
    user_id: int | None,
    timestamp: str,
) -> str:
    """Deprecated legacy hash shape.

    Retained only so the standalone verifier tooling can be aligned separately
    (P-04 / AUD-F04). No audit writer may call this function. Canonical chain
    hashes are produced exclusively by
    ``backend.app.services.audit_service._compute_chain_hash``.
    """
    raw = f"{previous_hash}|{action}|{entity_type}|{entity_id}|{user_id}|{timestamp}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _coerce_resource_id(entity_id: str | int | None) -> int | None:
    """Map a legacy identifier to the canonical integer ``resource_id``.

    Non-numeric identifiers (config keys, component names) are not discarded:
    they are preserved verbatim inside ``details.legacy_entity_id`` by
    :func:`create_audit_entry` and reconstructed by :func:`query_audit_log`.
    """
    if entity_id is None or isinstance(entity_id, bool):
        return None
    if isinstance(entity_id, int):
        return entity_id
    value = str(entity_id).strip()
    if not value:
        return None
    digits = value[1:] if value.startswith("-") else value
    return int(value) if digits.isdigit() else None


def _iso(value: Any) -> str | None:
    return value.isoformat() if hasattr(value, "isoformat") else (str(value) if value is not None else None)


def create_audit_entry(
    db_session: Any,
    action: str,
    entity_type: str,
    entity_id: str | int,
    user_id: int | None,
    lab_id: int | None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write through the canonical chain and return the legacy response shape.

    No ``commit()`` is performed — the caller owns the transaction boundary.
    The returned ``previous_hash`` is advisory only: it is the predecessor read
    before the canonical writer takes its serialization lock, and is not
    persisted as a row (the canonical schema has no such column).
    """
    from sqlalchemy import text

    canonical = _canonical_audit_service()

    previous_hash = canonical._get_last_chain_hash(db_session)

    # Unique correlation token: identifying the inserted row by "id > max(id)
    # seen before the write" is wrong under concurrency (another writer may
    # insert a lower id first). The token is hex-only, so it is safe inside the
    # JSON-text LIKE predicate used for retrieval.
    write_token = secrets.token_hex(16)
    canonical_details: dict[str, Any] = dict(details or {})
    canonical_details["legacy_entity_type"] = entity_type
    canonical_details["legacy_entity_id"] = str(entity_id)
    canonical_details["legacy_write_token"] = write_token

    canonical.log_action(
        db=db_session,
        action=action,
        resource_type=entity_type,
        resource_id=_coerce_resource_id(entity_id),
        user_id=user_id,
        lab_id=lab_id,
        details=canonical_details,
    )

    row = (
        db_session.execute(
            text(
                "SELECT id, action, resource_type, resource_id, user_id, lab_id, "
                "details, chain_hash, created_at FROM audit_logs "
                "WHERE details LIKE :write_token ORDER BY id DESC LIMIT 1"
            ),
            {"write_token": f'%"legacy_write_token":"{write_token}"%'},
        )
        .mappings()
        .first()
    )
    if row is None:  # defensive: canonical writer did not persist a row
        raise RuntimeError("canonical audit writer produced no row")
    return {
        "id": row["id"],
        "chain_hash": row["chain_hash"],
        # The canonical schema does not persist a per-row predecessor; expose
        # the value read immediately before the write for legacy callers.
        "previous_hash": previous_hash,
        "timestamp": _iso(row["created_at"]),
        "action": row["action"],
        "entity_type": row["resource_type"],
        "entity_id": (
            str(row["resource_id"])
            if row["resource_id"] is not None
            else canonical_details["legacy_entity_id"]
        ),
        "user_id": row["user_id"],
        "lab_id": row["lab_id"],
    }


def _legacy_entity_id(details: Any) -> str | None:
    if not details:
        return None
    try:
        parsed = json.loads(details) if isinstance(details, str) else details
    except (TypeError, ValueError):
        return None
    return str(parsed["legacy_entity_id"]) if isinstance(parsed, dict) and "legacy_entity_id" in parsed else None


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
    """Read canonical audit columns, mapping back to the legacy response shape."""
    from sqlalchemy import text

    clauses: list[str] = []
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if entity_type:
        clauses.append("resource_type = :entity_type")
        params["entity_type"] = entity_type
    if entity_id is not None:
        resource_id = _coerce_resource_id(entity_id)
        if resource_id is not None:
            clauses.append("resource_id = :resource_id")
            params["resource_id"] = resource_id
        else:
            # Bind parameters prevent injection, but `%` and `_` inside the
            # value would still act as LIKE wildcards. Escape them so a filter
            # such as "a%" matches only a literal identifier.
            escaped = (
                str(entity_id)
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            clauses.append("details LIKE :legacy_entity_id ESCAPE '\\'")
            params["legacy_entity_id"] = f'%"legacy_entity_id":"{escaped}"%'
    if user_id is not None:
        clauses.append("user_id = :user_id")
        params["user_id"] = user_id
    if lab_id is not None:
        clauses.append("lab_id = :lab_id")
        params["lab_id"] = lab_id
    if action:
        clauses.append("action = :action")
        params["action"] = action

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = (
        db_session.execute(
            text(
                "SELECT id, action, resource_type, resource_id, user_id, lab_id, "
                f"details, chain_hash, created_at FROM audit_logs {where} "
                "ORDER BY id DESC LIMIT :limit OFFSET :offset"
            ),
            params,
        )
        .mappings()
        .all()
    )
    return [
        {
            "id": row["id"],
            "action": row["action"],
            "entity_type": row["resource_type"],
            "entity_id": (
                str(row["resource_id"])
                if row["resource_id"] is not None
                else _legacy_entity_id(row["details"])
            ),
            "user_id": row["user_id"],
            "lab_id": row["lab_id"],
            "details": row["details"],
            "previous_hash": None,
            "chain_hash": row["chain_hash"],
            "timestamp": _iso(row["created_at"]),
        }
        for row in rows
    ]


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
