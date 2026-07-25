from __future__ import annotations

import logging
from typing import Any

from shared.audit.service import AuditService as SharedAuditService
from shared.audit.service import create_audit_entry, query_audit_log

logger = logging.getLogger("gula.control_plane.audit")


class ControlAuditAction:
    DEPLOYMENT = "control.deployment"
    CONFIG_CHANGE = "control.config_change"
    POLICY_CHANGE = "control.policy_change"
    API_CALL = "control.api_call"
    LOGIN = "control.login"
    RELEASE = "control.release"
    DECISION = "control.decision"
    INCIDENT = "control.incident"
    SECRET_ACCESS = "control.secret_access"
    SCALING = "control.scaling"
    REGISTRATION = "control.registration"


class EnterpriseAudit:
    def __init__(self, db_session: Any):
        self._service = SharedAuditService(db_session)
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
        return create_audit_entry(
            db_session=self._db,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            lab_id=lab_id,
            details=details,
        )

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
        return query_audit_log(
            db_session=self._db,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            lab_id=lab_id,
            action=action,
            limit=limit,
            offset=offset,
        )

    def log_deployment(
        self,
        component: str,
        version: str,
        user_id: int | None = None,
        details: dict | None = None,
    ) -> dict[str, Any]:
        return self.log(
            action=ControlAuditAction.DEPLOYMENT,
            entity_type="component",
            entity_id=component,
            user_id=user_id,
            details={"version": version, **(details or {})},
        )

    def log_config_change(
        self,
        key: str,
        user_id: int | None = None,
        details: dict | None = None,
    ) -> dict[str, Any]:
        return self.log(
            action=ControlAuditAction.CONFIG_CHANGE,
            entity_type="config",
            entity_id=key,
            user_id=user_id,
            details=details,
        )

    def log_policy_change(
        self,
        policy_name: str,
        user_id: int | None = None,
        details: dict | None = None,
    ) -> dict[str, Any]:
        return self.log(
            action=ControlAuditAction.POLICY_CHANGE,
            entity_type="policy",
            entity_id=policy_name,
            user_id=user_id,
            details=details,
        )

    def log_decision(
        self,
        decision: str,
        user_id: int | None = None,
        details: dict | None = None,
    ) -> dict[str, Any]:
        return self.log(
            action=ControlAuditAction.DECISION,
            entity_type="decision",
            entity_id=decision,
            user_id=user_id,
            details=details,
        )

    def log_incident(
        self,
        incident_id: str,
        user_id: int | None = None,
        details: dict | None = None,
    ) -> dict[str, Any]:
        return self.log(
            action=ControlAuditAction.INCIDENT,
            entity_type="incident",
            entity_id=incident_id,
            user_id=user_id,
            details=details,
        )
