"""
GULA Platform - Medical Audit Logger
Executive Order 5: Mandatory audit for all medical operations
"""

import logging
import os
from datetime import datetime
from typing import Any, Optional
from .messaging import publish_event

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Records all mandatory medical events to:
    1. audit_log database table (via database trigger)
    2. audit.events RabbitMQ queue
    """

    MANDATORY_EVENTS = [
        "PatientCreated",
        "SampleCollected",
        "ResultUpdated",
        "ResultValidated",
        "OrderCompleted",
        "OrderCreated",
        "SampleRejected",
        "AlertTriggered",
        "UserLogin",
        "UserLogout",
        "ReportGenerated",
        "DeviceConnected",
        "DeviceDisconnected",
    ]

    def log(
        self,
        event_type: str,
        entity_type: str,
        entity_id: Any,
        actor_id: Optional[int] = None,
        actor_username: Optional[str] = None,
        lab_id: Optional[int] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        metadata: Optional[dict] = None,
        severity: str = "info",
        ip_address: Optional[str] = None,
    ):
        payload = {
            "event_type":     event_type,
            "entity_type":    entity_type,
            "entity_id":      str(entity_id) if entity_id else None,
            "actor_id":       actor_id,
            "actor_username": actor_username,
            "lab_id":         lab_id,
            "old_values":     old_values,
            "new_values":     new_values,
            "metadata":       metadata or {},
            "severity":       severity,
            "ip_address":     ip_address,
            "timestamp":      datetime.utcnow().isoformat(),
        }

        publish_event("audit.events", event_type, payload)
        logger.info(f"[AUDIT] {event_type} | {entity_type}:{entity_id} | actor:{actor_username}")

    # =========================================================================
    # Convenience methods for mandatory events (Executive Order 5)
    # =========================================================================

    def patient_created(self, patient_id: int, data: dict, actor: dict = None):
        self.log("PatientCreated", "patient", patient_id,
                 actor_id=actor.get("id") if actor else None,
                 actor_username=actor.get("username") if actor else None,
                 new_values=data)

    def sample_collected(self, sample_id: int, data: dict, actor: dict = None):
        self.log("SampleCollected", "sample", sample_id,
                 actor_id=actor.get("id") if actor else None,
                 actor_username=actor.get("username") if actor else None,
                 new_values=data, severity="info")

    def result_updated(self, result_id: int, old: dict, new: dict, actor: dict = None):
        self.log("ResultUpdated", "result", result_id,
                 actor_id=actor.get("id") if actor else None,
                 actor_username=actor.get("username") if actor else None,
                 old_values=old, new_values=new)

    def result_validated(self, result_id: int, data: dict, actor: dict = None):
        self.log("ResultValidated", "result", result_id,
                 actor_id=actor.get("id") if actor else None,
                 actor_username=actor.get("username") if actor else None,
                 new_values=data, severity="info")

    def order_completed(self, order_id: int, data: dict, actor: dict = None):
        self.log("OrderCompleted", "order", order_id,
                 actor_id=actor.get("id") if actor else None,
                 actor_username=actor.get("username") if actor else None,
                 new_values=data)


# Singleton
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
