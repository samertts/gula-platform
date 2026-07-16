"""Standardized audit module — wraps existing audit service and AuditLog model."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from ..services.audit_service import log_action
from . import PlatformRegistry

logger = logging.getLogger("gula.platform.audit")


@dataclass
class AuditEntry:
    id: int = 0
    user_id: int | None = None
    user_role: str | None = None
    action: str = ""
    resource_type: str = ""
    resource_id: int | None = None
    details: str | None = None
    ip_address: str | None = None
    created_at: str = ""
    chain_hash: str | None = None


class AuditService:
    def __init__(self, db) -> None:
        self._db = db

    def create_entry(
        self,
        action: str,
        resource_type: str,
        resource_id: int | None = None,
        user_id: int | None = None,
        user_role: str | None = None,
        details: str | None = None,
        ip_address: str | None = None,
    ) -> None:
        log_action(
            db=self._db,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            user_role=user_role,
            details=details,
            ip_address=ip_address,
        )

    def query_entries(
        self,
        resource_type: str | None = None,
        action: str | None = None,
        user_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[dict]:
        from ..models.audit_log import AuditLog
        q = self._db.query(AuditLog)
        if resource_type:
            q = q.filter(AuditLog.resource_type == resource_type)
        if action:
            q = q.filter(AuditLog.action == action)
        if user_id is not None:
            q = q.filter(AuditLog.user_id == user_id)
        entries = q.order_by(AuditLog.id.desc()).offset(skip).limit(limit).all()
        return [
            {
                "id": e.id, "user_id": e.user_id, "user_role": e.user_role,
                "action": e.action, "resource_type": e.resource_type,
                "resource_id": e.resource_id, "details": e.details,
                "ip_address": e.ip_address,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "chain_hash": e.chain_hash,
            }
            for e in entries
        ]

    def get_trail(self, resource_type: str, resource_id: int) -> list[dict]:
        from ..models.audit_log import AuditLog
        entries = (
            self._db.query(AuditLog)
            .filter(AuditLog.resource_type == resource_type, AuditLog.resource_id == resource_id)
            .order_by(AuditLog.id.asc())
            .all()
        )
        return [
            {
                "id": e.id, "user_id": e.user_id, "user_role": e.user_role,
                "action": e.action, "details": e.details,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "chain_hash": e.chain_hash,
            }
            for e in entries
        ]


PlatformRegistry.register("audit", AuditService, capabilities=[
    {"name": "create_entry", "description": "Create a tamper-evident audit log entry"},
    {"name": "query_entries", "description": "Query audit log entries with filters"},
    {"name": "get_trail", "description": "Get the full audit trail for a resource"},
])
